from django.db import models
from django.contrib.postgres.fields import ArrayField
from Auth.models import User,Course,Result,Subject




class Question(models.Model):
    id = models.AutoField(primary_key=True)
    question = models.CharField()
    options = ArrayField(models.CharField(), size=4, default=list) 
    answer = models.IntegerField(default=0)

    def __str__(self):
        return f'Question {self.id}'


class Test(models.Model):
    name=models.TextField()
    id = models.AutoField(primary_key=True)
    courses = models.ManyToManyField(Course)  # Changed from ForeignKey to ManyToManyField
    questions = models.ManyToManyField(Question)
    created_by = models.ForeignKey(User, null=False, blank=False, on_delete=models.CASCADE)
    students = models.ManyToManyField(Result)
    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    subjects = models.ManyToManyField(Subject)  # Changed from CharField to ManyToManyField
    duration = models.IntegerField(default=1)

    def __str__(self):
        course_ids = ", ".join(str(course.id) for course in self.courses.all())
        subject_names = ", ".join(subject.name for subject in self.subjects.all())  # Assuming Subject model has a 'name' field
        return f'Test {self.id} for Courses {course_ids} and Subjects {subject_names}'





class Lecture(models.Model):
    id = models.AutoField(primary_key=True)
    video_path = models.CharField(max_length=255)
    courses = models.ManyToManyField(Course) 
    subjects = models.ManyToManyField(Subject)
    name=models.TextField()
    def __str__(self):
        return f'Lecture {self.id} for Course {self.course.id}'


class Material(models.Model):
    id = models.AutoField(primary_key=True)
    pdf_path = models.CharField(max_length=255)
    courses = models.ManyToManyField(Course) 
    subjects = models.ManyToManyField(Subject)
    name=models.TextField()

    def __str__(self):
        return f'Lecture {self.id} for Course {self.course.id}'
    
    
class Doubt(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="doubts")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_doubts", null=True) 
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="doubts",null=True)
    question_text = models.TextField(blank=True, null=True)
    question_image_path = models.CharField(max_length=500, blank=True, null=True)
    answer_text = models.TextField(blank=True, null=True)
    answer_image_path = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_answered = models.BooleanField(default=False)

