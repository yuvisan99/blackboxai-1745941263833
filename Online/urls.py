from django.urls import path
from Edu import views

urlpatterns = [
    path('tests', views.fetch_tests, name='fetch Test'),
    path('add-test', views.add_test, name='add Test'),
    path('student-tests', views.get_student_tests, name='Student Tests'),
    path('student-test/<int:test_id>', views.get_test_details, name='get_test_details'),
    path('submit-test/<int:test_id>', views.submit_test, name='Submit Test'),
    path('test-answers/<int:test_id>', views.test_answers, name='Answer Test'),
    path('materials/add', views.add_material, name='Add Materials'),
    path('fetch-materials', views.fetch_materials, name='fetch Materials'),
    path('submit-doubt', views.submit_doubt, name='Submit Doubts'),
    path('fetch-doubts', views.fetch_student_doubts, name='fetch Doubts'),
    path('teacher/unanswered-doubts', views.fetch_teacher_doubts, name='fetch Stu Mats'),
    path('teacher/submit-answer', views.answer_doubt, name='fetch Stu Mats'),
    path('fetch-student-materials', views.fetch_student_materials, name='fetch Stu Mats'),
]
