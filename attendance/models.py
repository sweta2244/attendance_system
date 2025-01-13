from django.db import models
from datetime import date 

class Student(models.Model):
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='students/')
    facial_encoding = models.BinaryField()
    
    def _str_(self):
        return self.name
    
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=date.today)
    status = models.CharField(max_length=10, choices=[('Present','Present'),('Absent','Absent')])

    class Meta:
        #ensure no duplicate records for the same day
        unique_together = ('student', 'date')
        ordering = ['-date']
        
    def _str_(self):
        return f"{self.student.name} - {self.date} - {self.status}"