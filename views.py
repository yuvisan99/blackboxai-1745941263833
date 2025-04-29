from django.shortcuts import render
import os
from django.conf import settings
import json
from .models import Test,Question,Material,Doubt
from Auth.models import Course,User,Subject,Result

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse,HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string

from datetime import datetime


@csrf_exempt
def add_test(request):
    # Authorization check
    if not ("user_info" in request.session and (request.session["user_info"]["type"] == 0 or request.session["user_info"]["type"] == 1)):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        print(request.session["user_info"])
        data = json.loads(request.body)
        print(data)
        # Fetch related user
        user = get_object_or_404(User, id=request.session["user_info"]["user_id"])

        # Parse and validate start_time and end_time
        try:
            start_time = timezone.make_aware(datetime.strptime(data.get('start_time'), '%Y-%m-%d %H:%M:%S'))
            end_time = timezone.make_aware(datetime.strptime(data.get('end_time'), '%Y-%m-%d %H:%M:%S'))
            duration = data.get("duration")
            name=data.get("name")
        except ValueError:
            return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD HH:MM:SS"}, status=400)
        
        # Create test instance
        test = Test.objects.create(
            name=name,
            created_by=user,
            start_time=start_time,
            end_time=end_time,
            duration=duration
        )
        
        # Process courseSubjects data (course IDs and associated subject IDs)
        course_subjects = data.get('courseSubjects', {})
        for course_id, subject_ids in course_subjects.items():
            course = get_object_or_404(Course, id=course_id)
            test.courses.add(course)  # Associate the course with the test
            
            # Add subjects to the test
            for subject_id in subject_ids:
                subject = get_object_or_404(Subject, id=subject_id)
                test.subjects.add(subject)  # Associate the subject with the test
        
        # Add questions to the test
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


def fetch_tests(request):
    """
    Fetch all tests with their details.
    """
    # Check for user authorization
    if not ("user_info" in request.session and request.session["user_info"]["type"] in [0, 1]):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        user_info = request.session["user_info"]
        
        # Fetching user object if needed
        if user_info["type"] != 0:
            user = get_object_or_404(User, id=user_info["user_id"])
            tests = Test.objects.filter(created_by=user)
        else:
            tests = Test.objects.all()

        data = []
        for test in tests:
            # Fetching associated courses and subjects
            cour_sub = {}
            for course in test.courses.all():
                subjects = [subject.name for subject in test.subjects.all() if subject.course.id == course.id]
                if subjects:
                    cour_sub[course.name] = subjects

            test_data = {
                "name": test.name,
                "id": test.id,
                "start_time": test.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                "end_time": test.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                "duration": test.duration,
                "questions": len(test.questions.all()),
                "course_subjects": cour_sub  # Courses with their associated subjects
            }
            data.append(test_data)

        return JsonResponse(data, safe=False, status=200)

    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        print(f"Error fetching tests: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
    
from django.utils.timezone import now

@csrf_exempt
def get_student_tests(request):
    """
    Fetch upcoming tests for the logged-in student user based on their course and join date.
    """
    if "user_info" not in request.session or request.session["user_info"]["type"] != 2:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        user_info = request.session["user_info"]
        student_id = user_info["user_id"]
        student = User.objects.get(id=student_id)

        if not student.course:
            return JsonResponse({"error": "Student has no course assigned"}, status=400)

        student_course = student.course
        current_time = now()

        # Fetch tests associated with the student's course
        tests = Test.objects.filter(courses=student_course).distinct()
        tests_data = []

        for test in tests:
            has_attempted = Result.objects.filter(student_id=student_id, test=test).exists()
            if (
                test.start_time >= student.date_joined and not has_attempted
                
            ):
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
        print(f"Error fetching student tests: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
    
    
    
@csrf_exempt   
def get_test_details(request, test_id):
    """
    Fetch the details of a specific test including its questions.
    """
    
    if "user_info" not in request.session or request.session["user_info"]["type"] != 2:
        print(print(request.session["user_info"]))
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        # Get the specific test by its ID
        
        test = get_object_or_404(Test, id=test_id)
        user=User.objects.get(id=request.session["user_info"]["user_id"])
        if user.course not in test.courses.all():
            
            return JsonResponse({"error": "Unauthorized"}, status=403)
        if not test.end_time.strftime('%Y-%m-%d %H:%M:%S') >= datetime.now().strftime('%Y-%m-%d %H:%M:%S'):
            return JsonResponse({"error": "Unauthorized"}, status=400)
        if Result.objects.filter(student=user, id__in=test.students.all()).exists():
            return JsonResponse({"error": "Test already submitted"}, status=405)
        # Fetch the questions associated with this test
        questions = test.questions.all()
        
        # Prepare the data for the response
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
                [option,idx]  # Including index and option
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

        # Return the test data along with questions
        return JsonResponse(test_data, status=200)

    except Exception as e:
        print(f"Error fetching test details: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
    
    
@csrf_exempt
def submit_test(request,test_id):
    # Authorization check
    if not ("user_info" in request.session and (request.session["user_info"]["type"]==2)):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        
        data = json.loads(request.body)
        print(data)
        test = get_object_or_404(Test, id=test_id)
        user=User.objects.get(id=request.session["user_info"]["user_id"])
        if user.course not in test.courses.all():
            return JsonResponse({"error": "Unauthorized"}, status=403)
        if Result.objects.filter(student=user, id__in=test.students.all()).exists():
            return JsonResponse({"error": "Test already submitted"}, status=400)
        total=0
        for question in data:
            obj=Question.objects.get(id=question)
            if(obj.answer==data[question]):
                print("true")
                total+=1
            else:print(False)
        print("total",total)
        res=Result(student=user,total=total,answers=data)
        res.save()
        test.students.add(res)
        
        return JsonResponse({"total":total},status=200)
        
    except Exception as e:
        print(e)
        return HttpResponse(status=400)
    
    
@csrf_exempt
def test_answers(request, test_id):
    if not ("user_info" in request.session and request.session["user_info"]["type"] == 2):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        # Fetch the Test object
        test = get_object_or_404(Test, id=test_id)
        user = User.objects.get(id=request.session["user_info"]["user_id"])

        # Check if the user is authorized to access the test
        if user.course not in test.courses.all():
            return JsonResponse({"error": "Unauthorized"}, status=403)

        # Fetch the Result for this test and student
        result = test.students.filter(student=user).first()

        if not result:
            return JsonResponse({"error": "No results found for this test"}, status=404)

        # Fetch questions and their data
        questions = test.questions.all()

        # Prepare the response data
        response_data = []
        for question in questions:
            student_answer = result.answers.get(str(question.id))  
            response_data.append({
                "id": question.id,
                "text": question.question,
                "options": question.options,  # Assuming 'options' is a list of options
                "correct_answer": question.answer,  # Correct answer for the question
                "student_answer": student_answer  # Student's answer
            })

        return JsonResponse(response_data, safe=False, status=200)

    except Exception as e:
        print(f"Error in test_answers: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
    
    
    
@csrf_exempt
def add_material(request):
    """
    Adds a new material for selected courses and subjects.
    Saves the file and stores its path in the database.
    """
    if not ("user_info" in request.session and (request.session["user_info"]["is_superuser"] or request.session["user_info"]["type"] == 1)):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        material_name = request.POST.get("material_name")
        file = request.FILES.get("file")
        courses = json.loads(request.POST.get("courses", "[]"))

        if not material_name or not file:
            return JsonResponse({"error": "Missing fields"}, status=400)

        # Generate a unique file name
        file_extension = os.path.splitext(file.name)[1]
        unique_file_name = f"{get_random_string(12)}{file_extension}"

        # Save file to a specific directory
        save_path = os.path.join(settings.MEDIA_ROOT, "materials", unique_file_name)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)

        # Save material record in the database
        material = Material.objects.create(
            name=material_name,
            pdf_path=os.path.join("materials", unique_file_name)  # Save relative path
        )

        # Link the material to selected courses and subjects
        for course in courses:
            course_obj = Course.objects.get(id=course["courseId"])
            material.courses.add(course_obj)
            for subject_id in course["subjectIds"]:
                subject_obj = Subject.objects.get(id=subject_id, course=course_obj)
                material.subjects.add(subject_obj)

        return HttpResponse(status=201)

    except Exception as e:
        print(e)
        return JsonResponse({"error": str(e)}, status=500)
    


@csrf_exempt
def fetch_materials(request):
    """
    Fetch all materials for teachers and admins.
    """
    
    if not ("user_info" in request.session and request.session["user_info"]["type"] in [0, 1]):
        print(request.session["user_info"])
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        user_info = request.session["user_info"]

        # Filter materials based on user type
        if user_info["type"] == 1:  # Teacher
            user = get_object_or_404(User, id=user_info["user_id"])
            materials = Material.objects.filter(subjects__in=user.subjects.all()).distinct()
        else:  # Admin
            materials = Material.objects.all()

        data = []
        for material in materials:
            cour_sub = {}
            for subject in material.subjects.all():
                course_name = subject.course.name
                cour_sub.setdefault(course_name, []).append(subject.name)

            data.append({
                "id": material.id,
                "name": material.name,
                "pdf_path": material.pdf_path,
                "course_subjects": cour_sub,
            })

        return JsonResponse(data, safe=False, status=200)
    except Exception as e:
        print(f"Error fetching materials: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@csrf_exempt
def fetch_student_materials(request):
    """
    Fetch materials for the logged-in student based on their courses and subjects.
    """
    if "user_info" not in request.session or request.session["user_info"]["type"] != 2:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        user_info = request.session["user_info"]
        student_course = Course.objects.get(id=user_info["course"]["id"])
        materials = Material.objects.filter(subjects__course=student_course).distinct()

        data = []
        for material in materials:
            subjects = [
                subject.name for subject in material.subjects.all() if subject.course == student_course
            ]
            if subjects:
                data.append({
                    "id": material.id,
                    "name": material.name,
                    "pdf_path": material.pdf_path,
                    "subjects": subjects,
                })

        return JsonResponse(data, safe=False, status=200)
    except Exception as e:
        print(f"Error fetching student materials: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
    
    
@csrf_exempt
def submit_doubt(request):
    if "user_info" not in request.session or request.session["user_info"]["type"] != 2:  # Check if the user is a student
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        user_info = request.session["user_info"]
        data = request.POST
        # Retrieve subject and teacher
        subject = Subject.objects.get(id=data.get("subject_id"))
        

        # Save image path
        question_image_path = None
        if request.FILES.get("question_image"):
            file = request.FILES["question_image"]
            file_path = os.path.join("questions", file.name)
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            # Save file to the media directory
            with open(full_path, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)

            question_image_path = file_path

        # Create the doubt
        
        
        doubt = Doubt.objects.create(
            student=User.objects.get(id=user_info["user_id"]),
            subject=subject,
            question_text=data.get("question_text", ""),
            question_image_path=question_image_path,
        )

        return JsonResponse({"message": "Doubt submitted successfully!", "doubt_id": doubt.id}, status=201)
    except Exception as e:
        print(e)
        return JsonResponse({"error": str(e)}, status=500)
    

@csrf_exempt
def answer_doubt(request):
    if "user_info" not in request.session or request.session["user_info"]["type"] != 1:  # Check if the user is admin or teacher
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        user_info = request.session["user_info"]
        data = request.POST
        doubt = Doubt.objects.get(id=data.get("doubt_id", ""))

        
        # Save image path
        answer_image_path = None
        if request.FILES.get("answer_image"):
            file = request.FILES["answer_image"]
            file_path = os.path.join("answers", file.name)
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            # Save file to the media directory
            with open(full_path, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)

            answer_image_path = file_path

        # Update doubt with the answer and save the teacher
        doubt.answer_text = data.get("answer_text", "")
        doubt.answer_image_path = answer_image_path
        doubt.is_answered = True

        # Save the teacher who answered
        if not doubt.teacher:
            teacher=User.objects.get(id=user_info["user_id"])
            doubt.teacher = teacher

        doubt.save()

        return JsonResponse({"message": "Doubt answered successfully!"}, status=200)
    except Doubt.DoesNotExist:
        return JsonResponse({"error": "Doubt not found"}, status=404)
    except Exception as e:
        print(e)
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
def fetch_student_doubts(request):
    """
    Fetch all doubts asked by a student.
    """
    if "user_info" not in request.session or request.session["user_info"]["type"] != 2:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        user_info = request.session["user_info"]
        student=User.objects.get(id=user_info["user_id"])
        doubts = Doubt.objects.filter(student=student).select_related("subject", "teacher")
        
        data = [
            {
                "id": doubt.id,
                "subject_name": doubt.subject.name,
                "question_text": doubt.question_text,
                "question_image_path": doubt.question_image_path,
                "answer": doubt.answer_text,
                "answer_image_path": doubt.answer_image_path,
                "answered_by": doubt.teacher.name if doubt.teacher  else None
            }
            for doubt in doubts
        ]
        return JsonResponse(data, safe=False, status=200)

    except Exception as e:
        print(f"Error fetching student doubts: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

    
@csrf_exempt
def fetch_teacher_doubts(request):
    """
    Fetch all doubts (answered and unanswered) for a teacher that match the courses and subjects they handle.
    """
    if "user_info" not in request.session or request.session["user_info"]["type"] != 1:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        teacher = User.objects.get(id=request.session["user_info"]["user_id"])
        all_doubts = Doubt.objects.filter(
            subject__course__teachers=teacher
        ).select_related("subject", "subject__course")

        unanswered = []
        answered = []

        for doubt in all_doubts:
            data = {
                "id": doubt.id,
                "subject_name": doubt.subject.name,
                "course_name": doubt.subject.course.name,
                "question_text": doubt.question_text,
                "question_image_path": doubt.question_image_path,
                "answer_text": doubt.answer_text,
                "answer_image_path": doubt.answer_image_path,
            }

            if doubt.answer_text:
                answered.append(data)
            else:
                unanswered.append(data)

        return JsonResponse({
            "unanswered_doubts": unanswered,
            "answered_doubts": answered,
        }, status=200)

    except Exception as e:
        print(f"Error fetching doubts: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)