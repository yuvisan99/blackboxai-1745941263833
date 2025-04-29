from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
import json
import os
from django.conf import settings

from .models import Test, Question, Material, Doubt
from Auth.models import User, Course, Subject, Result

def sample_page(request):
    return render(request, "base.html")

@csrf_exempt
def fetch_tests(request):
    if not ("user_info" in request.session and request.session["user_info"]["type"] in [0, 1]):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        user_info = request.session["user_info"]
        if user_info["type"] != 0:
            user = get_object_or_404(User, id=user_info["user_id"])
            tests = Test.objects.filter(created_by=user)
        else:
            tests = Test.objects.all()
        data = []
        for test in tests:
            cour_sub = {}
            for course in test.courses.all():
                subjects = [subject.name for subject in test.subjects.all() if subject.course == course]
                if subjects:
                    cour_sub[course.name] = subjects
            test_data = {
                "name": test.name,
                "id": test.id,
                "start_time": test.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                "end_time": test.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                "duration": test.duration,
                "questions": len(test.questions.all()),
                "course_subjects": cour_sub
            }
            data.append(test_data)
        return JsonResponse(data, safe=False, status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def get_student_tests(request):
    if "user_info" not in request.session or request.session["user_info"]["type"] != 2:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        user_info = request.session["user_info"]
        student_id = user_info["user_id"]
        student = User.objects.get(id=student_id)
        if not student.course:
            return JsonResponse({"error": "Student has no course assigned"}, status=400)
        student_course = student.course
        current_time = timezone.now()
        tests = Test.objects.filter(courses=student_course).distinct()
        tests_data = []
        for test in tests:
            has_attempted = Result.objects.filter(student_id=student_id, test=test).exists()
            if test.start_time >= student.date_joined and not has_attempted:
                tests_data.append({
                    "id": test.id,
                    "name": test.name,
                    "start_time": test.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "end_time": test.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "duration": test.duration,
                    "subjects": [
                        subject.name
                        for subject in test.subjects.all()
                        if subject.course == student_course
                    ],
                })
        return JsonResponse(tests_data, safe=False, status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def add_test(request):
    if not ("user_info" in request.session and (request.session["user_info"]["type"] == 0 or request.session["user_info"]["type"] == 1)):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        data = json.loads(request.body)
        user = get_object_or_404(User, id=request.session["user_info"]["user_id"])
        start_time = timezone.make_aware(datetime.strptime(data.get('start_time'), '%Y-%m-%d %H:%M:%S'))
        end_time = timezone.make_aware(datetime.strptime(data.get('end_time'), '%Y-%m-%d %H:%M:%S'))
        duration = data.get("duration")
        name = data.get("name")
        test = Test.objects.create(
            name=name,
            created_by=user,
            start_time=start_time,
            end_time=end_time,
            duration=duration
        )
        course_subjects = data.get('courseSubjects', {})
        for course_id, subject_ids in course_subjects.items():
            course = get_object_or_404(Course, id=course_id)
            test.courses.add(course)
            for subject_id in subject_ids:
                subject = get_object_or_404(Subject, id=subject_id)
                test.subjects.add(subject)
        for question_data in data.get('questions', []):
            question = Question.objects.create(
                question=question_data['question'],
                options=question_data['options'],
                answer=question_data['answer']
            )
            test.questions.add(question)
        return JsonResponse({"message": "Test created successfully"}, status=201)
    except Exception as e:
        print(e)
        return HttpResponse(status=500)

@csrf_exempt
def get_test_details(request, test_id):
    if "user_info" not in request.session or request.session["user_info"]["type"] != 2:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        test = get_object_or_404(Test, id=test_id)
        user = User.objects.get(id=request.session["user_info"]["user_id"])
        if user.course not in test.courses.all():
            return JsonResponse({"error": "Unauthorized"}, status=403)
        if not test.end_time.strftime('%Y-%m-%d %H:%M:%S') >= datetime.now().strftime('%Y-%m-%d %H:%M:%S'):
            return JsonResponse({"error": "Unauthorized"}, status=400)
        if Result.objects.filter(student=user, id__in=test.students.all()).exists():
            return JsonResponse({"error": "Test already submitted"}, status=405)
        questions = test.questions.all()
        test_data = {
            "id": test.id,
            "name": test.name,
            "start_time": test.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            "end_time": test.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            "duration": test.duration,
            "questions": [
                {
                    "id": question.id,
                    "question": question.question,
                    "options": [
                        [option, idx]
                        for idx, option in enumerate(question.options)
                    ],
                }
                for question in questions
            ],
            "subjects": [
                subject.name
                for subject in test.subjects.all()
                if subject.course == user.course
            ],
        }
        return JsonResponse(test_data, status=200)
    except Exception as e:
        print(f"Error fetching test details: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def submit_test(request, test_id):
    if "user_info" not in request.session or request.session["user_info"]["type"] != 2:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        data = json.loads(request.body)
        user = User.objects.get(id=request.session["user_info"]["user_id"])
        test = get_object_or_404(Test, id=test_id)
        if user.course not in test.courses.all():
            return JsonResponse({"error": "Unauthorized"}, status=403)
        if Result.objects.filter(student=user, id__in=test.students.all()).exists():
            return JsonResponse({"error": "Test already submitted"}, status=405)
        answers = data.get("answers", {})
        total = 0
        for question in test.questions.all():
            qid = str(question.id)
            if qid in answers and answers[qid] == question.answer:
                total += 1
        result = Result.objects.create(student=user, total=total)
        test.students.add(result)
        return JsonResponse({"message": "Test submitted successfully", "total": total}, status=200)
    except Exception as e:
        print(f"Error submitting test: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def test_answers(request, test_id):
    if "user_info" not in request.session or request.session["user_info"]["type"] != 1:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        test = get_object_or_404(Test, id=test_id)
        answers = []
        for question in test.questions.all():
            answers.append({
                "id": question.id,
                "answer": question.answer
            })
        return JsonResponse(answers, safe=False, status=200)
    except Exception as e:
        print(f"Error fetching test answers: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def add_material(request):
    if not ("user_info" in request.session and (request.session["user_info"]["type"] == 0 or request.session["user_info"]["type"] == 1)):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        data = json.loads(request.body)
        user = get_object_or_404(User, id=request.session["user_info"]["user_id"])
        name = data.get("name")
        pdf_path = data.get("pdf_path")
        courses_ids = data.get("courses", [])
        subjects_ids = data.get("subjects", [])
        material = Material.objects.create(name=name, pdf_path=pdf_path)
        for course_id in courses_ids:
            course = get_object_or_404(Course, id=course_id)
            material.courses.add(course)
        for subject_id in subjects_ids:
            subject = get_object_or_404(Subject, id=subject_id)
            material.subjects.add(subject)
        return JsonResponse({"message": "Material added successfully"}, status=201)
    except Exception as e:
        print(f"Error adding material: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def fetch_materials(request):
    if not ("user_info" in request.session and (request.session["user_info"]["type"] == 0 or request.session["user_info"]["type"] == 1)):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        materials = Material.objects.all()
        data = []
        for material in materials:
            data.append({
                "id": material.id,
                "name": material.name,
                "pdf_path": material.pdf_path,
                "courses": [course.name for course in material.courses.all()],
                "subjects": [subject.name for subject in material.subjects.all()]
            })
        return JsonResponse(data, safe=False, status=200)
    except Exception as e:
        print(f"Error fetching materials: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def submit_doubt(request):
    if "user_info" not in request.session or request.session["user_info"]["type"] != 2:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        data = json.loads(request.body)
        user = User.objects.get(id=request.session["user_info"]["user_id"])
        doubt_text = data.get("doubt")
        doubt = Doubt.objects.create(student=user, doubt=doubt_text)
        return JsonResponse({"message": "Doubt submitted successfully"}, status=201)
    except Exception as e:
        print(f"Error submitting doubt: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def fetch_student_doubts(request):
    if "user_info" not in request.session or request.session["user_info"]["type"] != 2:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        user = User.objects.get(id=request.session["user_info"]["user_id"])
        doubts = Doubt.objects.filter(student=user)
        data = []
        for doubt in doubts:
            data.append({
                "id": doubt.id,
                "doubt": doubt.doubt,
                "answer": doubt.answer,
                "answered": doubt.answered,
            })
        return JsonResponse(data, safe=False, status=200)
    except Exception as e:
        print(f"Error fetching student doubts: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def fetch_teacher_doubts(request):
    if "user_info" not in request.session or request.session["user_info"]["type"] not in [0, 1]:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        doubts = Doubt.objects.filter(answered=False)
        data = []
        for doubt in doubts:
            data.append({
                "id": doubt.id,
                "doubt": doubt.doubt,
                "student": doubt.student.id,
                "student_name": doubt.student.user_name,
            })
        return JsonResponse(data, safe=False, status=200)
    except Exception as e:
        print(f"Error fetching teacher doubts: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def answer_doubt(request):
    if "user_info" not in request.session or request.session["user_info"]["type"] not in [0, 1]:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        data = json.loads(request.body)
        doubt_id = data.get("doubt_id")
        answer_text = data.get("answer")
        doubt = get_object_or_404(Doubt, id=doubt_id)
        doubt.answer = answer_text
        doubt.answered = True
        doubt.save()
        return JsonResponse({"message": "Doubt answered successfully"}, status=200)
    except Exception as e:
        print(f"Error answering doubt: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def fetch_student_materials(request):
    if "user_info" not in request.session or request.session["user_info"]["type"] != 2:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        user = User.objects.get(id=request.session["user_info"]["user_id"])
        materials = Material.objects.filter(courses=user.course)
        data = []
        for material in materials:
            data.append({
                "id": material.id,
                "name": material.name,
                "pdf_path": material.pdf_path,
                "subjects": [subject.name for subject in material.subjects.all() if subject.course == user.course]
            })
        return JsonResponse(data, safe=False, status=200)
    except Exception as e:
        print(f"Error fetching student materials: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
