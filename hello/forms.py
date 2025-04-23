from django import forms
from django.contrib.auth.models import User
from hello.models import LogMessage, PatientDoctor, Profile, Scan, ScanComment

class LogMessageForm(forms.ModelForm):
    class Meta:
        model = LogMessage
        fields = ("message",)

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'email']
        help_texts = {
            'username': None,  # or use 'Custom message here' if you want a different message
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password != password_confirm:
            raise forms.ValidationError("Passwords do not match!")
        
        return cleaned_data
    
class AssignPatientForm(forms.ModelForm):
    class Meta:
        model = PatientDoctor
        fields = ['patient']
    
    def __init__(self, *args, **kwargs):
        doctor_profile = kwargs.pop('doctor_profile', None)
        super().__init__(*args, **kwargs)
        if doctor_profile:
            # Show only users who are patients
            self.fields['patient'].queryset = Profile.objects.filter(isDoctor=False)
            self.fields['patient'].label_from_instance = lambda obj: obj.user.username

class UploadScanForm(forms.ModelForm):
    class Meta:
        model = Scan
        fields = ['patient', 'file', 'description', 'scan_type']
    
    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        if doctor:
            # Get all PatientDoctor entries for this doctor
            patient_profiles = PatientDoctor.objects.filter(doctor=doctor).values_list('patient', flat=True)

            # Get corresponding User objects for those patient profiles
            patient_users = User.objects.filter(profile__id__in=patient_profiles)
            
            self.fields['patient'].queryset = patient_users
            
class ScanCommentForm(forms.ModelForm):
    class Meta:
        model = ScanComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your message...'}),
        }