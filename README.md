# LMS Course Management API (Django + DRF)

A multi-tenant Learning Management System (LMS) API that separates **tenants by workspace** (API Key) and authenticates **actors** (teacher / student / admin / guest) with JWT. It exposes endpoints to manage teachers, students, courses, lessons, materials, assignments, submissions, and progress—with clean per-workspace isolation.

> **Tenant model in one line**
> **API Key** ⇒ identifies the **workspace (tenant)**.
> **JWT** ⇒ authenticates the **user** (teacher / student / admin / guest) and enforces permissions.

---

## 1) Project Overview

This API lets multiple developers (or customers) share a single deployment while keeping data isolated per **workspace**. Each workspace has **one API key**, and actions inside the workspace are performed by **users** with roles. A typical flow:

1. Create (or fetch) a **workspace API key**.
2. Register/login users **inside that workspace**.
3. Call LMS endpoints using **both** headers:

   * `X-API-Key: <workspace-api-key>` (tenant)
   * `Authorization: Bearer <jwt>` (actor)

---

## 2) Features

* **Multi-tenancy via Workspace + API Key**

  * One key per workspace (rotation supported).
  * Middleware attaches `request.workspace` from the API key.
* **Role-based actors with JWT**

  * Users belong to a workspace via Teacher/Student/Guest profile.
  * Tenant-aware login: users can only login within their own workspace.
* **Teacher & Student management**

  * Per-workspace Teacher/Student/Guest profiles.
  * Group/role assignment for permissions.
* **Courses & Enrollment**

  * Per-workspace courses.
  * Enrollment (students on courses) scoped to same workspace.
* **Lessons & Materials**

  * Lessons and course materials per course / workspace.
* **Assignments & Submissions**

  * Teachers create assignments; students submit files; teachers grade.
* **Progress Tracking**

  * Track lesson completion per student.
* **Seeding**

  * DRF scoped throttles (per IP / per user).

---

## 3) Tech Stack

* **Python** 3.10+
* **Django** 4.x
* **Django REST Framework** (DRF)
* **SimpleJWT** for JWT auth
* **SQLite** (local) / **PostgreSQL** (recommended for production)
---

## 4) Models Description

> Only key fields are shown for brevity; your code contains additional timestamps and options.

### accounts.Workspace

* `name` (unique) — workspace/tenant name.
* *(optional)* `owner` — if you cap workspaces per user.

### accounts.ApiKey

* `workspace` (OneToOne) — one key per workspace.
* `key` (unique) — URL-safe string.
* `expires_at` — key expiry.

### accounts.User (custom)

* Extends `AbstractUser`.
* `role` — one of `teacher|student|guest|admin`.
* *(optional)* `workspace` FK if you choose to store a direct link.

### mainapp.Teacher

* `workspace` (FK → Workspace)
* `user` (OneToOne → User)
* `specialization`, `experience`, `bio`…

### mainapp.Student

* `workspace` (FK → Workspace)
* `user` (OneToOne → User)
* `age`, `enrolled_date`…

### mainapp.Guest

* `workspace` (FK → Workspace)
* `user` (OneToOne → User)

### mainapp.Course

* `workspace` (FK → Workspace)
* `title` (unique **per workspace** via `UniqueConstraint(workspace, title)`)
* `description`, `instructor` (FK → Teacher), `students` (M2M → Student)
* `start_date`, `end_date`, `duration`, `level`, `category`, `summary`

### mainapp.CourseMaterial

* `workspace` (FK), `course` (FK), `title`, `file`

### mainapp.Lesson

* `workspace` (FK), `course` (FK), `title`, `content`, `order`

### mainapp.Assignment

* `workspace` (FK), `course` (FK), `title`, `description`, `due_date`

### mainapp.Submission

* `workspace` (FK), `assignment` (FK), `student` (FK), `file`, `grade`

### mainapp.Progress

* `workspace` (FK), `student` (FK), `lesson` (FK), `completed` (bool)
* `unique_together(student, lesson)`; ordered by `created_at`

---

## 5) Project Structure

Below is a focused view of the most relevant files and folders in this project. Boilerplate like `__pycache__` and compiled files are omitted.

```
CMApi/
├─ build.sh                 # (optional) deploy/build helper
├─ db.sqlite3               # local dev DB (swap for Postgres in prod)
├─ manage.py                # Django admin/management entrypoint
├─ requirements.txt         # Python dependencies
│
├─ CMApi/                   # Project config package
│  ├─ settings.py           # Django settings (env, DB, apps, DRF, JWT, cache)
│  ├─ urls.py               # Root URL router; includes app URLs
│  ├─ asgi.py / wsgi.py     # ASGI/WSGI entrypoints
│  └─ __init__.py
│
├─ accounts/                # Authentication, tenancy, API keys
│  ├─ models.py             # Workspace, ApiKey, custom User
│  ├─ serializers.py        # RegisterSerializer, etc.
│  ├─ views.py              # Register, Change Role, API key endpoints
│  ├─ authentication.py     # (optional) auth helpers
│  ├─ middleware.py         # WorkspaceFromApiKey + AuditLog middleware
│  ├─ urls.py               # Accounts routes
│  ├─ admin.py              # Django admin registrations
│  ├─ migrations/           # DB migrations for accounts app
│  └─ management/commands/  # Admin/ops scripts (e.g., setup_roles.py)
│
├─ mainapp/                 # Core LMS domain
│  ├─ models.py             # Teacher, Student, Guest, Course, Lesson, ...
│  ├─ serializers.py        # Per-model serializers
│  ├─ permissions.py        # IsUserInWorkspace, IsCourseOwnerOrReadOnly, ...
│  ├─ views.py              # ViewSets for courses/materials/assignments/etc.
│  ├─ views_seeds.py        # Dev endpoint: seed current workspace
│  ├─ seed_utils.py         # Reusable seeding logic (teachers/students/guests...)
│  ├─ urls.py               # Mainapp routes (ViewSets / routers)
│  ├─ migrations/           # DB migrations for mainapp
│  └─ management/commands/  # e.g., seed_demo.py (shared demo tenant)
│
├─ media/                   # Uploaded files (dev)
│  ├─ course_materials/     # CourseMaterial.file
│  └─ submissions/          # Submission.file
│
└─ postman/
   └─ collections/          # Postman collections for testing
      └─ <collection>.json
```

**Notes**

* **accounts.middleware** attaches `request.workspace` from the `X-API-Key` header and writes audit events.
* **mainapp.permissions** ensure the JWT user belongs to the same workspace (`IsUserInWorkspace`) and enforce object rules.
* **seed_utils.py** centralizes demo-data creation; **views_seeds.py** exposes a dev-only endpoint to seed the caller’s workspace.
* Keep `media/` out of version control in production and use a proper object store (e.g., S3, GCS).

---

## 6) Installation Guide

```bash
# 1) Clone
git clone https://github.com/your-org/lms-api.git
cd lms-api

# 2) Create venv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3) Install deps
pip install -r requirements.txt

# 4) Environment
cp .env.example .env
# set SECRET_KEY, DEBUG, DATABASE_URL, ALLOWED_HOSTS, etc.

# 5) Migrate
python manage.py migrate

# 6) (Optional) Create superuser
python manage.py createsuperuser

# 7) Run
python manage.py runserver
```

**Database**

* Local: SQLite works out of the box.
* Prod: Use PostgreSQL (`DATABASE_URL=postgres://...`).


---

## 7) API Usage

### Auth model at a glance

* **Header 1: API Key (tenant)**

  * `X-API-Key: <workspace-api-key>`
  * or `Authorization: ApiKey <workspace-api-key>`
* **Header 2: JWT (actor)**

  * `Authorization: Bearer <jwt>`

Most endpoints require **both**.

### 7.1 Create / Rotate Workspace API Key

**One key per workspace** (OneToOne). If a key exists and is active:

* Return existing (do **not** re-show plaintext), or
* Rotate if `force_rotate=true`.

```
POST /api/keys/create
Body:
{
  "username": "alice_workspace",
  "hours": 24,
  "force_rotate": true
}
```

**Response (created/rotated):**

```json
{
  "message": "API key created successfully",
  "api_key": "RAW-KEY-HERE",
  "expires_at": "2025-10-01T12:34:56Z",
  "hours": 24
}
```

**Response (already exists):**

```json
{
  "message": "API key already exists for this workspace",
  "api_key": "",
  "key_prefix": "AbCdEf12",
  "expires_at": "2025-10-01T12:34:56Z"
}
```

> **Best practice:** Protect this endpoint with `IsAuthenticated` + throttles.

### 7.2 Tenant-aware Registration

**Requires API Key header** to put the new user in the correct workspace.

```
POST /api/accounts/register/
Headers:
  X-API-Key: <workspace-api-key>
Body:
{
  "username": "teacher_jane",
  "email": "jane@example.com",
  "password": "pass123",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "teacher"
}
```

* Creates `User` + `Teacher/Student/Guest` profile **in this workspace** (atomic; rolls back on error).
* Assigns Group by role.

### 7.3 Tenant-aware Login (JWT)

Use the **tenant-aware** login so users **must** provide the workspace API key of their tenant.

```
POST /api/login/
Headers:
  X-API-Key: <workspace-api-key>
Body:
{
  "username": "teacher_jane",
  "password": "pass123"
}
```

**Response:**

```json
{
  "refresh": "<refresh-token>",
  "access": "<jwt-access-token>",
  "workspace_id": 123,
  "workspace_name": "alice_workspace"
}
```

**Refresh:**

```
POST /api/token/refresh/
Body: { "refresh": "<refresh-token>" }
```

> If a user tries to login with the **wrong workspace’s** API key, login fails.

### 7.4 Dev Seeding Endpoint (per-workspace)

Seeds demo Teachers, Students, Guests, Courses, Lessons, Assignments, Submissions, Progress **into the caller’s workspace**. Idempotent. Defaults: 2 teachers, 3 students, 2 guests.

```
POST /api/dev/seed/
Headers:
  X-API-Key: <workspace-api-key>
  Authorization: Bearer <jwt>
Body: {}
```

> Keep this **dev-only** (e.g., allowed only in `DEBUG` or staff users).

### 7.5 Core LMS Endpoints (examples)

> Replace with your actual routes/router paths if different.

* **Teachers**

  * `GET /api/teachers/`
  * `POST /api/teachers/` *(if allowed)*
* **Students**

  * `GET /api/students/`
* **Courses**

  * `GET /api/courses/`
  * `POST /api/courses/`

    * Teachers cannot set `instructor`; it’s auto-assigned to themselves.
    * Admins may set `instructor`, but it **must** be in the same workspace.
* **Lessons, Materials, Assignments, Submissions, Progress**

  * All `get_queryset()` filter by `request.workspace`.
  * All `perform_create()` force `workspace=ws` and validate cross-tenant relations.

**Headers required for most operations:**

```
X-API-Key: <workspace-api-key>
Authorization: Bearer <jwt>
```

### 7.6 Permissions

Add these to sensitive endpoints:

* `HasWorkspace` — requires a valid API key (tenant).
* `IsUserInWorkspace` — ensures JWT user’s profile belongs to the same workspace.
* `DjangoModelPermissions` — uses Groups/Permissions.
* `IsCourseOwnerOrReadOnly` — example object-level rule.
```
```

## 8) Postman Collection

Add your collection link here once published:

* **Postman docs:** *<paste your public documentation link>*

Tips:

* Create an environment with variables: `{{base_url}}`, `{{workspace_api_key}}`, `{{jwt}}`.
* Add default headers: `X-API-Key: {{workspace_api_key}}` and `Authorization: Bearer {{jwt}}`.

---

## 9) Contribution Guide

1. **Fork** the repo and create a feature branch:
   `git checkout -b feat/something-cool`
2. Install pre-commit hooks / linters (if configured).
3. Add tests where practical.
4. Open a **pull request** with a clear description.
5. Be kind, write small, reviewable PRs. 🙌

---

## 10) License
....

---

## 11) Contact

* Author/Maintainer: **Damisola Deboh-Ajiga**
* Email: **damisola.d.ajiga@gmail.com**
* Issues: use the repo **Issues** tab for bug reports & feature requests.

---

## Quick cURL Cheatsheet

**Register teacher in a workspace**

```bash
curl -X POST {{base_url}}/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: {{workspace_api_key}}" \
  -d '{
    "username":"teacher_jane",
    "email":"jane@example.com",
    "password":"pass123",
    "first_name":"Jane",
    "last_name":"Doe",
    "role":"teacher"
  }'
```

**Login (tenant-aware)**

```bash
curl -X POST {{base_url}}/api/login/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: {{workspace_api_key}}" \
  -d '{
    "username":"teacher_jane",
    "password":"pass123"
  }'
```

**Create a course (as teacher)**

```bash
curl -X POST {{base_url}}/api/courses/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: {{workspace_api_key}}" \
  -H "Authorization: Bearer {{jwt}}" \
  -d '{
    "title":"Intro to Python",
    "description":"Basics",
    "start_date":"2025-10-01",
    "end_date":"2025-12-01",
    "duration":60,
    "category":"Programming",
    "level":"beginner"
  }'
```

**Seed demo data into your workspace**

```bash
curl -X POST {{base_url}}/api/dev/seed/ \
  -H "X-API-Key: {{workspace_api_key}}" \
  -H "Authorization: Bearer {{jwt}}" \
  -d '{}'
```

> Always send **both** headers (`X-API-Key` + `Bearer <jwt>`) to access tenant-scoped endpoints.
