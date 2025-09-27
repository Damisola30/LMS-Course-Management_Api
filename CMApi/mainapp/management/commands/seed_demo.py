# mainapp/management/commands/seed_demo.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import transaction

from mainapp.models import Teacher, Student, Course, Lesson, Assignment, Submission, Progress

User = get_user_model()

class Command(BaseCommand):
    help = "Seed demo data: groups, users, teacher/student profiles, courses, lessons, assignments, submissions, progress."

    def handle(self, *args, **options):
        with transaction.atomic():
            # Ensure groups (idempotent)
            for name in ["Teacher", "Student", "Admin", "Guest"]:
                Group.objects.get_or_create(name=name)

            # Superuser
            if not User.objects.filter(username="admin").exists():
                admin = User.objects.create_superuser("admin", "admin@example.com", "adminpass")
                admin.role = "admin"
                admin.save()
                self.stdout.write(self.style.SUCCESS("Created superuser 'admin' / password: adminpass"))
            else:
                admin = User.objects.get(username="admin")
                self.stdout.write("Superuser exists: admin")

            # Teachers (create user if missing; ensure Teacher profile exists)
            teacher_usernames = ["teacher1", "teacher2"]
            t_users = []
            for i, uname in enumerate(teacher_usernames, start=1):
                u, created = User.objects.get_or_create(
                    username=uname,
                    defaults={
                        "email": f"{uname}@example.com",
                        "first_name": f"T{i}",
                        "last_name": "Teacher"
                    }
                )
                if created:
                    u.set_password("pass123")
                    u.role = "teacher"
                    u.save()
                    self.stdout.write(self.style.SUCCESS(f"Created teacher user {uname}"))
                else:
                    # ensure role is set to teacher if previously created differently
                    if u.role != "teacher":
                        u.role = "teacher"
                        u.save()
                        self.stdout.write(self.style.WARNING(f"Updated role for existing user {uname} -> teacher"))

                # ensure group membership
                grp = Group.objects.get(name="Teacher")
                if not grp.user_set.filter(pk=u.pk).exists():
                    grp.user_set.add(u)

                # ensure Teacher profile exists
                teacher_profile = getattr(u, "teacher", None)
                if teacher_profile is None:
                    teacher_profile = Teacher.objects.create(user=u, specialization="General", experience=3)
                    self.stdout.write(self.style.SUCCESS(f"Created Teacher profile for {uname}"))
                t_users.append(teacher_profile)

            # Students
            student_usernames = ["student1", "student2", "student3"]
            s_students = []
            for i, uname in enumerate(student_usernames, start=1):
                u, created = User.objects.get_or_create(
                    username=uname,
                    defaults={
                        "email": f"{uname}@example.com",
                        "first_name": f"S{i}",
                        "last_name": "Student"
                    }
                )
                if created:
                    u.set_password("pass123")
                    u.role = "student"
                    u.save()
                    self.stdout.write(self.style.SUCCESS(f"Created student user {uname}"))
                else:
                    if u.role != "student":
                        u.role = "student"
                        u.save()
                        self.stdout.write(self.style.WARNING(f"Updated role for existing user {uname} -> student"))

                grp = Group.objects.get(name="Student")
                if not grp.user_set.filter(pk=u.pk).exists():
                    grp.user_set.add(u)

                student_profile = getattr(u, "student", None)
                if student_profile is None:
                    student_profile = Student.objects.create(user=u, age=20 + i)
                    self.stdout.write(self.style.SUCCESS(f"Created Student profile for {uname}"))
                s_students.append(student_profile)

            # Create sample courses (one per teacher)
            courses = []
            for idx, teacher in enumerate(t_users, start=1):
                instructor_username = teacher.user.username if teacher and teacher.user else f"teacher{idx}"
                title = f"Demo Course {idx} - {instructor_username}"
                course, created = Course.objects.get_or_create(
                    title=title,
                    defaults={
                        "description": f"Sample course {idx}",
                        "instructor": teacher,
                        "start_date": timezone.now().date(),
                        "end_date": (timezone.now() + timezone.timedelta(days=60)).date(),
                        "duration": 60,
                        "category": "Demo",
                        "level": "beginner",
                    }
                )
                # enroll demo students for the first course
                if idx == 1 and s_students:
                    course.students.set(s_students)
                courses.append(course)
                self.stdout.write(self.style.SUCCESS(f"Course ensured: {course.title}"))

            # Lessons and assignments + submissions
            for course in courses:
                # Create multiple lessons
                for n in range(1, 4):  # 3 lessons
                    Lesson.objects.get_or_create(
                        course=course,
                        title=f"Lesson {n} - {course.title}",
                        defaults={"content": f"Demo content for lesson {n}", "order": n}
                    )

                # Create multiple assignments
                for a in range(1, 3):  # 2 assignments
                    assignment, _ = Assignment.objects.get_or_create(
                        course=course,
                        title=f"Assignment {a} - {course.title}",
                        defaults={
                            "description": f"Demo assignment {a}",
                            "due_date": timezone.now() + timezone.timedelta(days=7*a)
                        }
                    )

                # Create submissions for every student
                for student in course.students.all():
                    filename = f"demo_{student.user.username}_a{a}.txt"
                    content = ContentFile(b"Demo submission content", name=filename)
                    Submission.objects.get_or_create(
                        assignment=assignment,
                        student=student,
                        defaults={"file": content}
                    )
                 # --- Progress: create an entry for every student for every lesson ---
                # This ensures Progress rows exist (completed=False by default).
                for lesson in course.lessons.all():
                    for student in course.students.all():
                        Progress.objects.get_or_create(
                            student=student,
                            lesson=lesson,
                            defaults={"completed": False}
                        )
                # Optionally, mark the first student's first lesson as completed (keep for demo)
                if course.students.exists() and course.lessons.exists():
                    first_student = course.students.first()
                    first_lesson = course.lessons.first()
                    Progress.objects.update_or_create(
                        student=first_student,
                        lesson=first_lesson,
                        defaults={"completed": True}
                    )

            # Progress (mark first lesson of first course completed for first student)
            if courses and s_students:
                first_course = courses[0]
                first_lesson = first_course.lessons.first()
                if first_lesson:
                    p, created = Progress.objects.get_or_create(student=s_students[0], lesson=first_lesson, defaults={"completed": True})
                    if created:
                        self.stdout.write(self.style.SUCCESS("Created progress entry"))
                    else:
                        self.stdout.write("Progress entry exists")

            self.stdout.write(self.style.SUCCESS("Demo seed complete."))
