from django.contrib import admin
from .models import Profile, Scan, PatientDoctor, ScanComment, DoctorInfo, Reminder
# Register your models here.

admin.site.register(Profile)
admin.site.register(Scan)
admin.site.register(PatientDoctor)
admin.site.register(ScanComment)
admin.site.register(DoctorInfo)
admin.site.register(Reminder)