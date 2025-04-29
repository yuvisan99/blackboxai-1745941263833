from django.urls import path
from .views import *

urlpatterns = [
    path('tests', fetch_tests, name='fetch Test'),
    path('add-test', add_test, name='add Test'),
    path('student-tests', get_student_tests, name='Student Tests'),
    path('student-test/<int:test_id>', get_test_details, name='get_test_details'),
    path('submit-test/<int:test_id>', submit_test, name='Submit Test'),
    path('test-answers/<int:test_id>', test_answers, name='Answer Test'),
    path('materials/add', add_material, name='Add Materials'),
    path('fetch-materials', fetch_materials, name='fetch Materials'),
    path('submit-doubt', submit_doubt, name='Submit Doubts'),
    path('fetch-doubts', fetch_student_doubts, name='fetch Doubts'),
    path('teacher/unanswered-doubts', fetch_teacher_doubts, name='fetch Stu Mats'),
    path('teacher/submit-answer', answer_doubt, name='fetch Stu Mats'),
    path('fetch-student-materials', fetch_student_materials, name='fetch Stu Mats'),
    path('sample', sample_page, name='sample_page'),
]
