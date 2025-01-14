from django.contrib import admin
from .models import Student, Attendance, Teacher

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'rollno', 'subject')
    list_filter = ('subject',)
    
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')  # Display name and subject in the admin list
    list_filter = ('subject',)  # Add filter for subject
    
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status')
    list_filter = ('date', 'status')
