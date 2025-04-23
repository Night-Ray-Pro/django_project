from django.contrib import admin
from .models import Profile, Scan, PatientDoctor, ScanComment
# Register your models here.

admin.site.register(Profile)
admin.site.register(Scan)
admin.site.register(PatientDoctor)
admin.site.register(ScanComment)
