import re
from django.utils.timezone import datetime
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.shortcuts import redirect
from hello.forms import LogMessageForm, AssignPatientForm, UploadScanForm, ScanCommentForm
from hello.models import LogMessage, Profile, PatientDoctor, Scan, ScanComment
from django.views.generic import ListView
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404


# Replace the existing home function with the one below
class HomeListView(ListView):
    """Renders the home page, with a list of all messages."""
    model = LogMessage

    def get_context_data(self, **kwargs):
        context = super(HomeListView, self).get_context_data(**kwargs)
        return context

def about(request):
    return render(request, "hello/about.html")

def contact(request):
    return render(request, "hello/contact.html")

def log_message(request):
    form = LogMessageForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            message = form.save(commit=False)
            message.log_date = datetime.now()
            message.save()
            return redirect("home")
    else:
        return render(request, "hello/log_message.html", {"form": form})
    
def hello_there(request, name):
    print(request.build_absolute_uri())
    return render(
        request,
        'hello/hello_there.html',
        {
            'name': name,
            'date': datetime.now
        }
    )

####

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            Profile.objects.create(user=user, isDoctor=False)
            login(request, user)
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'hello/register.html', {'form': form})

def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)

                if user.profile.isDoctor:
                    return redirect('doctor_dashboard')
                else:
                    return redirect('patient_dashboard')
            else:
                form.add_error(None, "Invalid username or password")
    else:
        form = AuthenticationForm()
        return render(request, 'hello/login.html', {'form': form})
    
@login_required
def doctor_dashboard(request):
    if not request.user.profile.isDoctor:  # Assuming Profile model has 'isDoctor' field
        return redirect('patient_dashboard')
    if request.method == "POST":
        form = AssignPatientForm(request.POST, doctor_profile=request.user.profile)
        if form.is_valid():
            try:
                assignment = form.save(commit=False)
                assignment.doctor = request.user
                assignment.save()
                messages.success(request, 'Patient assigned successfully.')
            except:
                messages.warning(request, 'This patient is already assigned to you.')

            return redirect('doctor_dashboard')
    else:
        form = AssignPatientForm(doctor_profile=request.user.profile)
    assigned_patients = PatientDoctor.objects.filter(doctor=request.user.id)

    return render(request, 'hello/doctor_dashboard.html', {
        'form':form,
        'assigned_patients': assigned_patients
    })
    
@login_required
def patient_dashboard(request):
    if request.user.profile.isDoctor:  # Check if the user is NOT a patient (is a doctor)
        return redirect('doctor_dashboard')
    assigned_doctors = PatientDoctor.objects.filter(patient=request.user.profile.id)

    return render(request, 'hello/patient_dashboard.html', {'assigned_doctors': assigned_doctors})



def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def upload_scan(request):
    if not request.user.profile.isDoctor:
        return redirect('patient_dashboard')
    if request.method == 'POST':
        form = UploadScanForm(request.POST, request.FILES, doctor=request.user)
        if form.is_valid():
            scan = form.save(commit=False)
            scan.doctor = request.user
            scan.save()
            return redirect('doctor_dashboard')
    else:
        form = UploadScanForm(doctor=request.user)
    
    return render(request, 'hello/upload_scan.html', {'form': form})

def doctor_scans(request, doctor_id):
    doctor = User.objects.get(id=doctor_id)
    scans = Scan.objects.filter(doctor=doctor, patient=request.user)
    return render(request, 'hello/doctor_scans.html', {'scans':scans, 'doctor':doctor})

def patient_scans(request, patient_id):
    patient = User.objects.get(id=patient_id)
    scans = Scan.objects.filter(doctor = request.user, patient=patient)
    return render(request, 'hello/patient_scans.html', {'scans':scans, 'patient':patient})

def download_scan(request, scan_id):
    try:
        scan = Scan.objects.get(id=scan_id)
        file_path = scan.file.path
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    except (Scan.DoesNotExist, FileNotFoundError):
        raise Http404("File not found")
    
def scan_detail(request, scan_id):
    scan = get_object_or_404(Scan, id=scan_id)

    if request.user != scan.patient and request.user != scan.doctor:
        return HttpResponseForbidden("You're not allowed to view this scan.") 

    comments = ScanComment.objects.filter(scan=scan).order_by('timestamp')
    is_dicom = scan.file.name.lower().endswith(".dcm")
    if request.method == "POST":
        form =ScanCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.scan = scan
            comment.author = request.user
            comment.save()
            return redirect('scan_detail', scan_id=scan_id)
    else:
        form =ScanCommentForm()

    return render(request, 'hello/scan_detail.html', {
        'scan':scan,
        'comments': comments,
        'form': form,
        'is_dicom': is_dicom,
        })
