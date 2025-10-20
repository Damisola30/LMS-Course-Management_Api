# mainapp/seed_utils.py
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from django.db import transaction
from django.core.files.base import ContentFile
from django.utils.text import slugify

from .models import Teacher, Student, Guest, Course, Lesson, Assignment, Submission, Progress

User = get_user_model()

def ensure_groups():
    for name in ["Teacher", "Student", "Admin", "Guest"]:
        Group.objects.get_or_create(name=name)

@transaction.atomic
def seed_into_developer(developer, username_prefix: str | None = None,
                        teacher_count=2, student_count=3, guest_count=2):
    """
    Idempotently seed demo data INTO the given developers account.
    username_prefix ensures global username uniqueness across workspaces.
    """
    ensure_groups()

    # default prefix based on workspace name (avoids global username collisions)
    if username_prefix is None:
        username_prefix = f"{slugify(developer.username)}__"

    # --- Teachers ---
    t_profiles = []
    for i in range(1, teacher_count + 1):
        uname = f"{username_prefix}teacher{i}"
        u, created = User.objects.get_or_create(
            username=uname,
            defaults={
                "email": f"{uname}@example.com",
                "first_name": f"T{i}",
                "last_name": "Teacher",
                "role": "teacher",
            },
        )
        if created:
            u.set_password("pass123")
            u.save()
        Group.objects.get(name="Teacher").user_set.add(u)

        teacher = getattr(u, "teacher", None)
        if teacher is None:
            teacher = Teacher.objects.create(
                user=u, developer=developer, specialization="General", experience=3
            )
        elif teacher.developer_id != developer.id:
            # Same username already used in another tenant → skip
            continue
        t_profiles.append(teacher)

    # --- Students ---
    s_profiles = []
    for i in range(1, student_count + 1):
        uname = f"{username_prefix}student{i}"
        u, created = User.objects.get_or_create(
            username=uname,
            defaults={
                "email": f"{uname}@example.com",
                "first_name": f"S{i}",
                "last_name": "Student",
                "role": "student",
            },
        )
        if created:
            u.set_password("pass123")
            u.save()
        Group.objects.get(name="Student").user_set.add(u)

        student = getattr(u, "student", None)
        if student is None:
            student = Student.objects.create(
                user=u, developer=developer, age=20 + i
            )
        elif student.developer_id != developer.id:
            continue
        s_profiles.append(student)

    # --- Guests (new) ---
    g_profiles = []
    for i in range(1, guest_count + 1):
        uname = f"{username_prefix}guest{i}"
        u, created = User.objects.get_or_create(
            username=uname,
            defaults={
                "email": f"{uname}@example.com",
                "first_name": f"G{i}",
                "last_name": "Guest",
                "role": "guest",
            },
        )
        if created:
            u.set_password("pass123")
            u.save()
        Group.objects.get(name="Guest").user_set.add(u)

        guest = getattr(u, "guest", None)
        if guest is None:
            guest = Guest.objects.create(user=u, developer=developer)
        elif guest.developer_id != developer.id:
            continue
        g_profiles.append(guest)

    # --- Courses (one per teacher) ---
    courses = []
    for idx, teacher in enumerate(t_profiles, start=1):
        title = f"Demo Course {idx} - {teacher.user.username}"
        course, _ = Course.objects.get_or_create(
            developer=developer,
            title=title,
            defaults={
                "description": f"Sample course {idx}",
                "instructor": teacher,
                "start_date": timezone.now().date(),
                "end_date": (timezone.now() + timezone.timedelta(days=60)).date(),
                "duration": 60,
                "category": "Demo",
                "level": "beginner",
            },
        )
        # Enroll students to the first course
        if idx == 1 and s_profiles:
            course.students.set(s_profiles)
        courses.append(course)

    # --- Lessons, Assignments, Submissions, Progress ---
    for course in courses:
        # Lessons
        for n in range(1, 4):
            Lesson.objects.get_or_create(
                developer=developer,
                course=course,
                title=f"Lesson {n} - {course.title}",
                defaults={"content": f"Demo content for lesson {n}", "order": n},
            )

        # Assignments
        created_assignments = []
        for a in range(1, 2 + 1):
            assignment, _ = Assignment.objects.get_or_create(
                developer=developer,
                course=course,
                title=f"Assignment {a} - {course.title}",
                defaults={
                    "description": f"Demo assignment {a}",
                    "due_date": timezone.now() + timezone.timedelta(days=7 * a),
                },
            )
            created_assignments.append(assignment)

        # Submissions (every student → every assignment)
        for assignment in created_assignments:
            for student in course.students.all():
                filename = f"demo_{student.user.username}_{assignment.id}.txt"
                content = ContentFile(b"Demo submission content", name=filename)
                Submission.objects.get_or_create(
                    developer=developer,
                    assignment=assignment,
                    student=student,
                    defaults={"file": content},
                )

        # Progress for every student/lesson; mark first one completed
        for lesson in course.lessons.all():
            for student in course.students.all():
                Progress.objects.get_or_create(
                    developer=developer,
                    student=student,
                    lesson=lesson,
                    defaults={"completed": False},
                )
        if course.students.exists() and course.lessons.exists():
            first_student = course.students.first()
            first_lesson = course.lessons.first()
            Progress.objects.update_or_create(
                developer=developer,
                student=first_student,
                lesson=first_lesson,
                defaults={"completed": True},
            )
