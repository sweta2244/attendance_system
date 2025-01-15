from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import base64
import json
from django.contrib import messages
from .models import Student, Attendance, Teacher
from .forms import TeacherLoginForm, StudentRegistrationForm
from datetime import timedelta, date
from .utils import get_face_encoding_from_frame, match_face
import cv2
import numpy as np

def capture_face(request):
    if request.method == 'GET':
        return render(request, 'capture.html')
    
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body)
            image_data = data.get('image')  # Get the image data from the JSON payload

            if not image_data:
                return JsonResponse({'message': 'No image data provided.'})

            # Decode the Base64 image data
            image_bytes = base64.b64decode(image_data.split(',')[1])  # Ignore the "data:image/jpeg;base64," part
            np_arr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # Decode the image into an OpenCV format
            
            # Process the image to get encoding
            encoding = get_face_encoding_from_frame(frame)
            if encoding is None:
                return JsonResponse({'message': "No face detected. Please retry."})

            # Check in database for a match
            database_students = Student.objects.all()
            matched_student = None
            min_distance = float("inf")
            
            for student in database_students:
                db_encoding = np.frombuffer(student.facial_encoding)  # Get stored encoding from database
                if db_encoding.size == 0:  # Skip invalid or empty encodings
                    continue
                
                # Compare the encodings
                distance = np.linalg.norm(encoding - db_encoding)
                if distance < 0.6 and distance < min_distance:
                    min_distance = distance
                    matched_student = student

            if matched_student:
                # Mark attendance
                today = date.today()
                attendance, created = Attendance.objects.get_or_create(student=matched_student, date=today)
                if created:
                    attendance.status = 'Present'
                    attendance.save()
                return JsonResponse({'message': f"Attendance Done for {matched_student.name}!"})

            return JsonResponse({'message': "Unknown Face! Can't find in database."})
        except Exception as e:
            print("Error processing image:", e)
            return JsonResponse({'message': f"An error occurred during processing: {str(e)}"})
        
    return JsonResponse({'message': "Invalid request method."})




def teacher_login(request):
    if request.method == 'POST':
        form = TeacherLoginForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            subject = form.cleaned_data.get('subject')  # Use .get() for safety

            try:
                # Ensure subject is handled even if it's missing
                if not subject:
                    form.add_error('subject', 'Subject is required')
                    return render(request, 'teacher_login.html', {'form': form})

                teacher = Teacher.objects.get(name=name, password=password, subject=subject)
                
                # Store teacher details in session
                request.session['teacher_id'] = teacher.id
                request.session['name'] = teacher.name
                request.session['subject'] = teacher.subject

                return redirect('teacher_dashboard')
            except Teacher.DoesNotExist:
                form.add_error(None, 'Invalid credentials')
    else:
        form = TeacherLoginForm()

    return render(request, 'teacher_login.html', {'form': form})


def teacher_dashboard(request):
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('teacher_login')

    teacher = Teacher.objects.get(id=teacher_id)
    students = Student.objects.filter(subject=teacher)

    return render(request, 'teacher_dashboard.html', {'teacher': teacher, 'students': students})


def teacher_dashboard(request):
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('teacher_login')

    teacher = Teacher.objects.get(id=teacher_id)
    students = Student.objects.filter(subject=teacher)

    return render(request, 'teacher_dashboard.html', {'teacher': teacher, 'students': students})


def register_student(request):
    teacher_id = request.session.get('teacher_id')  # Get the logged-in teacher's ID
    if not teacher_id:
        return redirect('teacher_login')  # Redirect to login if teacher is not logged in

    teacher = Teacher.objects.get(id=teacher_id)  # Fetch the logged-in teacher

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            student.subject = teacher  # Assign the logged-in teacher to the student's subject
            
            # Process the student's photo and extract facial encoding
            photo = form.cleaned_data.get('photo')
            if photo:
                # Convert the image to a format usable by OpenCV
                image = cv2.imdecode(np.frombuffer(photo.read(), np.uint8), cv2.IMREAD_COLOR)

                # Get the face encoding from the image
                encoding = get_face_encoding_from_frame(image)
                if encoding is not None:
                    student.facial_encoding = encoding.tobytes()  # Store the encoding as binary in the database
                else:
                    messages.error(request, "No face detected in the photo. Please try again.")
                    return redirect('register_student')

            try:
                student.save()  # Save the student to the database
                messages.success(request, f"Student {student.name} has been registered successfully!")
                return redirect('teacher_dashboard')  # Redirect to the teacher dashboard
            except Exception as e:
                messages.error(request, f"Error while registering student: {str(e)}")
                return redirect('register_student')  # Redirect back to the registration page
        else:
            # If form is not valid, show the errors
            messages.error(request, "Form is not valid. Please check the input fields.")
            return redirect('register_student')
    else:
        form = StudentRegistrationForm()

    return render(request, 'register_student.html', {'form': form})

def view_attendance(request):
    teacher_id = request.session.get('teacher_id')  # Fetch the logged-in teacher's ID
    if not teacher_id:
        return redirect('teacher_login')

    teacher = Teacher.objects.get(id=teacher_id)  # Get the Teacher instance
    students = Student.objects.filter(subject=teacher)  # Filter students taught by the teacher
    attendance_records = Attendance.objects.filter(student__in=students).order_by('-date')

    return render(request, 'view_attendance.html', {'attendance_records': attendance_records, 'teacher': teacher})

        
