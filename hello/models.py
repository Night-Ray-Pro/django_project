from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class LogMessage(models.Model):
    message = models.CharField(max_length=300)
    log_date = models.DateTimeField("date logged")

    def __str__(self):
        """Returns a string representation of a message."""
        date = timezone.localtime(self.log_date)
        return f"'{self.message}' logged on {date.strftime('%A, %d %B, %Y at %X')}"

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    isDoctor = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({'Doctor' if self.isDoctor else 'Patient'})"

class PatientDoctor(models.Model):
    patient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='doctor_links')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patirnt_link')
    
    class Meta:
        unique_together = ('patient', 'doctor') #prevents duplicates
    
    def __str__(self):
        return f"Doctor {self.doctor.username} <-> Patient {self.patient.user.username}"

class Scan(models.Model):
    SCAN_TYPES = [
    ('X-Ray', 'X-Ray'),
    ('CT', 'CT Scan'),
    ('MRI', 'MRI'),
    ('Ultrasound', 'Ultrasound'),
    ('PET', 'PET Scan'),
    ('ECG', 'ECG'),
    ('Other', 'Other'),
]
    file = models.FileField(upload_to="scans/")
    description = models.TextField()
    upload_date = models.DateTimeField(auto_now_add=True)
    scan_type = models.CharField(max_length=50, choices=SCAN_TYPES)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scan_uploaded_by")
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scan_received_by")

    def __str__(self):
        return f"Scan {self.id} for {self.patient.username} by Dr. {self.doctor.username}"
    
class ScanComment(models.Model):
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on scan {self.scan.id}"


