# LMS Course Management API

This project is a **Learning Management System (LMS)** built using **Django** and **Django REST Framework**.
It provides a robust backend API for managing courses, teachers, students, assignments, materials, lessons, and student progress.

---

## Features

* **Teacher Management** – Add, view, update, and delete teacher profiles.
* **Student Management** – Manage student details and enrollment status.
* **Course Management** – Assign instructors, enroll students, set course schedules, and track categories/levels.
* **Course Materials** – Upload and organize materials for each course.
* **Assignments & Submissions** – Create assignments and manage student submissions with grading.
* **Lessons & Progress Tracking** – Organize lessons and track student completion.
* **Category & Level Support** – Categorize courses and set difficulty levels.
* **RESTful API** – Easy to integrate with any frontend or mobile app.

---

##  Tech Stack

* **Backend Framework**: Django
* **API Framework**: Django REST Framework (DRF)
* **Database**: SQLite (default, can be changed to PostgreSQL/MySQL)
* **Language**: Python 3.x
* **File Storage**: Django's default file handling 

---

##  Models Overview

### 1. **Teacher**

* `name`, `email`, `bio`, `specialization`, `experience`, `is_active`

### 2. **Student**

* `name`, `email`, `age`, `enrolled_date`, `is_active`

### 3. **Course**

* `title`, `description`, `instructor`, `students`, `start_date`, `end_date`, `duration`, `category`, `level`, `summary`, `is_active`

### 4. **CourseMaterial**

* `course`, `title`, `file`

### 5. **Assignment**

* `course`, `title`, `description`, `due_date`

### 6. **Submission**

* `assignment`, `student`, `file`, `grade`

### 7. **Lesson**

* `course`, `title`, `content`, `video_url`, `order`

### 8. **Progress**

* `student`, `lesson`, `completed`

---

##  Project Structure

```
CMApi/
│
├── CMApi/              # Project configuration
├── mainapp/              # App containing models, views, serializers, urls
├── media/                # Uploaded files (course materials, submissions)
├── manage.py
└── requirements.txt
```

---

## Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/lms-course-management-api.git
cd lms-course-management-api
```

### 2️⃣ Create Virtual Environment & Install Dependencies

```bash
python -m venv env
source env/bin/activate   # On Mac/Linux
env\Scripts\activate      # On Windows

pip install -r requirements.txt
```

### 3️⃣ Apply Migrations

```bash
python manage.py migrate
```

### 4️⃣ Create Superuser

```bash
python manage.py createsuperuser
```

### 5️⃣ Run Development Server

```bash
python manage.py runserver
```

---

## 📡 API Endpoints (Examples)
reference the postman documentation for more detailed explanation 

## 🧑‍💻 Author

**Damisola Deboh-Ajiga**
[GitHub Profile](https://github.com/yourusername)

---

