from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Course(models.Model):
    id = models.AutoField(primary_key=True)
    roll_count = models.IntegerField(blank=True, null=True, default=0)
    class_number = models.IntegerField()
    name = models.TextField(default='')

    def __str__(self):
        return self.name

class Subject(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')

    def __str__(self):
        return self.name

class User(AbstractUser):
    roll_no = models.IntegerField(blank=True, null=True, unique=True)
    fees = models.FloatField(blank=True, null=True)
    type = models.IntegerField(choices=[(0, 'Admin'), (1, 'Teacher'), (2, 'Student')], default=2)
    course = models.ForeignKey(Course, blank=True, null=True, on_delete=models.CASCADE, related_name='students')
    courses = models.ManyToManyField(Course, blank=True, related_name='teachers', help_text='Only applicable for teachers')
    subjects = models.ManyToManyField(Subject, blank=True, help_text='Applicable for teachers only')
    lec = models.BooleanField(default=False, help_text='Access to lectures')
    live = models.BooleanField(default=False, help_text='Access to live sessions')
    mat = models.BooleanField(default=False, help_text='Access to materials')
    tests = models.BooleanField(default=False, help_text='Access to tests')
    contact_number = models.CharField(max_length=15, unique=True, help_text="User's contact number")

    def __str__(self):
        return self.username

class Result(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    answers = models.JSONField(default=dict)
    total = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
