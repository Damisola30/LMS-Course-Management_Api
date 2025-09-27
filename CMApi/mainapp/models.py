from django.db import models
from django.conf import settings
from accounts.models import User
# Create your models here.


class Teacher(models.Model):
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.CASCADE, related_name="teachers", null = True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    specialization = models.CharField(max_length=100)
    experience = models.IntegerField(help_text="Years of teaching experience")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

# Student model representing a student(User-Group) in the LMS
class Student(models.Model):
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.CASCADE, related_name="students",null = True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    age = models.IntegerField()
    enrolled_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default = True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Guest (models.Model):
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.CASCADE, related_name="guests",null = True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
    
# Course model representing a course in the LMS
class Course(models.Model):
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.CASCADE, related_name="courses",null = True, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    instructor = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True)
    students = models.ManyToManyField(Student, related_name='courses', blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    duration = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.CharField(max_length=50, default='General')
    summary = models.TextField(blank=True, null=True)
    level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ])

    def __str__(self):
        return self.title
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["workspace","title"], name="uniq_course_title_per_workspace"),
        ]
        
# CourseMaterial model representing materials for courses
class CourseMaterial(models.Model):
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.CASCADE, null=True, blank=True, related_name="CourseMaterials")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name = "materials")
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to="course_materials/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return self.title
    
# Assignment model representing assignments for courses
class Assignment(models.Model):
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.CASCADE, null=True, blank=True, related_name="Assignments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=100)
    description = models.TextField()
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("grade_assignment", "Can grade assignments")
        ]
    def __str__(self):
        return f"{self.title} ({self.course.title})"

# Submission model representing student submissions for assignments
class Submission(models.Model):
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.CASCADE, null=True, blank=True, related_name="Submissions")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    file = models.FileField(upload_to="submissions/")
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.assignment.title}" 

# Lesson model representing individual lessons within a course
class Lesson(models.Model):
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.CASCADE, null=True, blank=True, related_name="Lessons")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=100)
    content = models.TextField()
    video_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.title

# Progress model to track lesson completion by students
class Progress(models.Model):
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.CASCADE, null=True, blank=True, related_name="Progress")
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE) 
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'lesson')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.student.user.get_full_name() or self.student.user.username} - {self.lesson.title}"















