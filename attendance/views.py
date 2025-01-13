from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import base64
import json
from .models import Student, Attendance
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
            data = json.loads(request.body)  # Correctly parse JSON data
            image_data = data.get('image')  # Get the image data from the JSON payload

            if not image_data:
                return JsonResponse({'message': 'No image data provided.'})

            # Decode the Base64 image data (the part after the 'base64,' prefix)
            image_bytes = base64.b64decode(image_data.split(',')[1])  # Ignore the "data:image/jpeg;base64," part
            np_arr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # Decode the image into an OpenCV format
            
            # Process the image
            encoding = get_face_encoding_from_frame(frame)
            if encoding is None:
                return JsonResponse({'message': "No face detected. Please retry."})
        
        # Check in database
            database_students = Student.objects.all()
            matched_student = None
            min_distance = float("inf")
            
            for student in database_students:
                db_encoding = np.frombuffer(student.facial_encoding)
                distance = np.linalg.norm(encoding - db_encoding)
                
                if distance < 0.6 and distance < min_distance:
                    min_distance = distance
                    matched_student = student
            
            if matched_student:
                # marking attendance
                today = date.today()
                attendance, created = Attendance.objects.get_or_create(student=matched_student, date=today) 
                if created:
                    attendance.status = 'Present'
                    attendance.save()
                return JsonResponse({'message': f"Attendance Done for {matched_student.name}!"})
        
            return JsonResponse({'message': "Unknown Face! Can't find in database."})
        except Exception as e:
            print("Error processing image:", e)
            return JsonResponse({'message': f"An error occurred during processing:{str(e)}"})
        
    return JsonResponse({'message': "Invalid request method."})


def register_student(request):
    if request. method == "POST":
        name = request.POST['name']
        photo = request.FILES['photo']
        
        # saves the image and generates facial encoding
        student = Student(name=name, photo=photo)
        student.save()
        encoding = get_face_encoding(student.photo.path)
        
        if encoding is not None:
            student.facial_encoding = encoding.tobytes()
            student.save()
            return redirect('register_student')
        else:
            student.delete()
            return render(request, 'register.html', {'error': "No faces detected in the uploaded photo."})
        
    return render(request, 'register.html')


def view_attendance(request):
    if request.method == "GET":    
        # Filter attendance records by date range
        today = date.today()
        start_date = today - timedelta(days=30)
        attendance_records = Attendance.objects.filter(date__range=[start_date, today])
        
        return render(request, 'attendance_records.html', {'records': attendance_records})
        
