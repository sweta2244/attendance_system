from django.db import models
from datetime import date


class Teacher(models.Model):
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Student(models.Model):
    name = models.CharField(max_length=100)
    rollno = models.CharField(max_length=50, unique=True)
    photo = models.ImageField(upload_to='students/')
    facial_encoding = models.BinaryField()
    subject = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='students')

    def __str__(self):
        return self.name


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=date.today)
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')])

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.status}"