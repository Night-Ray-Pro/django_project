import re
from django.utils.timezone import datetime
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.shortcuts import redirect
from hello.forms import LogMessageForm, AssignPatientForm, UploadScanForm, ScanCommentForm, DoctorSettingsForm
from hello.models import LogMessage, Profile, PatientDoctor, Scan, ScanComment, DoctorInfo, Reminder
from django.views.generic import ListView
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth import update_session_auth_hash
from django.db.models import OuterRef, Subquery, Max, F



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
            DoctorInfo.objects.create(user=user)
            login(request, user)
            return redirect('login')
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
                return redirect('login')
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
    scans = Scan.objects.filter(doctor=request.user.id)
    reminders = Reminder.objects.filter(user=request.user.id).order_by('-created_at')
    user = request.user  # or any
    latest_comment_timestamps = (
        ScanComment.objects
        .filter(scan=OuterRef('scan'), author=user)
        .order_by('-timestamp')
        .values('timestamp')[:1]
    )
    
    # Filter only latest comments by user per scan
    latest_comments = (
        ScanComment.objects
        .filter(author=user)
        .annotate(latest_timestamp=Subquery(latest_comment_timestamps))
        .filter(timestamp=F('latest_timestamp'))
        .order_by('-timestamp')
    )

    return render(request, 'hello/doctor_dashboard2.html', {
        'form':form,
        'assigned_patients': assigned_patients,
        'reminders': reminders,
        'latest_comments': latest_comments,
        'scans': scans,
    })
    
@login_required
def patient_dashboard(request):
    if request.user.profile.isDoctor:  # Check if the user is NOT a patient (is a doctor)
        return redirect('doctor_dashboard')
    assigned_doctors = PatientDoctor.objects.filter(patient=request.user.profile.id)
    scans = Scan.objects.filter(patient=request.user.id)
    reminders = Reminder.objects.filter(user=request.user.id).order_by('-created_at')
    user = request.user  # or any
    latest_comment_timestamps = (
        ScanComment.objects
        .filter(scan=OuterRef('scan'), author=user)
        .order_by('-timestamp')
        .values('timestamp')[:1]
    )
    
    # Filter only latest comments by user per scan
    latest_comments = (
        ScanComment.objects
        .filter(author=user)
        .annotate(latest_timestamp=Subquery(latest_comment_timestamps))
        .filter(timestamp=F('latest_timestamp'))
        .order_by('-timestamp')
    )
    return render(request, 'hello/patient_dashboard2.html', {
        'assigned_doctors': assigned_doctors,
        'scans': scans,
        'reminders': reminders,
        'latest_comments': latest_comments,
        })



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

def patient_search(request):
    assigned_doctors = PatientDoctor.objects.filter(patient=request.user.profile.id)
    return render(request, 'hello/patient_search.html', {'assigned_doctors': assigned_doctors})

def doctor_search(request):
    assigned_patients = PatientDoctor.objects.filter(doctor=request.user.id)
    return render(request, 'hello/doctor_search.html', {'assigned_patients': assigned_patients})

def scan_search_dr(request):
    assigned_scans = Scan.objects.filter(doctor=request.user.id)
    return render(request, 'hello/scan_searchDr.html', {'assigned_scans': assigned_scans})

def scan_search_pt(request):
    assigned_scans = Scan.objects.filter(patient=request.user.id)
    return render(request, 'hello/scan_searchPt.html', {'assigned_scans': assigned_scans})

def doctor_searchAD(request):
    patients = Profile.objects.filter(isDoctor=False)
    assigned_patients = PatientDoctor.objects.filter(doctor=request.user.id)
    assigned_patient_ids = set(assigned_patients.values_list('patient', flat=True))
    return render(request, 'hello/doctor_searchAD.html', {
        'patients': patients,
        'assigned_patients': assigned_patients,
        'assigned_patient_ids': assigned_patient_ids,
        })

@csrf_exempt
@login_required
def add_reminder(request):
    if request.method == 'POST':
        reminder = Reminder.objects.create(user=request.user, message="")
        return JsonResponse({'id': reminder.id, 'message': reminder.message})

@csrf_exempt
@login_required
def update_reminder(request, reminder_id):
    if request.method == "POST":
        data = json.loads(request.body)
        reminder = Reminder.objects.get(id=reminder_id, user=request.user)
        reminder.message = data.get("message", "")
        reminder.save()
        return JsonResponse({"status": "success"})

@csrf_exempt
@login_required
def delete_reminder(request, reminder_id):
    if request.method == "POST":
        Reminder.objects.filter(id=reminder_id, user=request.user).delete()
        return JsonResponse({"status": "deleted"})


@login_required
def settingsDr(request):
    doctor_info = request.user.doctorinfo
    if request.method == 'POST':
        form = DoctorSettingsForm(request.POST, request.FILES, instance=doctor_info, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('settingsDr')  # or some success message
        if 'password_change' in request.POST:
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'New password must be at least 8 characters long.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keeps the user logged in
                messages.success(request, 'Password successfully changed.')
    else:
        form = DoctorSettingsForm(instance=doctor_info, user=request.user)

    return render(request, 'hello/doctor_settings.html', {'form': form})

@login_required
def settingsP(request):
    doctor_info = request.user.doctorinfo
    if request.method == 'POST':
        form = DoctorSettingsForm(request.POST, request.FILES, instance=doctor_info, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('settingsP')  # or some success message
        if 'password_change' in request.POST:
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'New password must be at least 8 characters long.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keeps the user logged in
                messages.success(request, 'Password successfully changed.')
    else:
        form = DoctorSettingsForm(instance=doctor_info, user=request.user)

    return render(request, 'hello/patient_settings.html', {'form': form})

@login_required
def add_patient(request, patient_id):
    if request.method == 'POST':
        doctor = request.user
        patient_profile = get_object_or_404(Profile, id=patient_id, isDoctor=False)

        # Create the relationship if it doesn't already exist
        PatientDoctor.objects.get_or_create(patient=patient_profile, doctor=doctor)

    return redirect('doctor_searchAD')  # replace with your actual view name

@login_required
def remove_patient(request, patient_id):
    if request.method == 'POST':
        patient = get_object_or_404(Profile, id=patient_id)
        PatientDoctor.objects.filter(doctor=request.user, patient=patient).delete()
    return redirect('doctor_searchAD')  # replace with the view name showing the patient list

####
import pydicom
import numpy as np
from PIL import Image
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from pydicom.pixel_data_handlers.util import convert_color_space

def dicom_to_png_bytes(dicom_path):
    ds = pydicom.dcmread(dicom_path)
    pixel_array = ds.pixel_array
    rgb_pixel_array = convert_color_space(pixel_array, 'YBR_FULL_422', 'RGB')
    print("DICOM read success:", ds.SOPInstanceUID)
    print("Pixel Array Shape:", rgb_pixel_array.shape)

    # Convert the pixel array based on shape
    if rgb_pixel_array.ndim == 3 and rgb_pixel_array.shape[-1] == 3:
        print("Detected RGB image")
        image = Image.fromarray(rgb_pixel_array.astype(np.uint8))  # already RGB
    else:
        print("Detected grayscale image")
        image = Image.fromarray(rgb_pixel_array).convert("L")

    output = BytesIO()
    image.save(output, format='PNG')
    # with open("preview_output.png", "wb") as f:
    #     f.write(output.getvalue())
    # print("Saved preview image to disk.")
    output.seek(0)
    return output

def create_scan_pdf(scan, dicom_png_io=None):
    print("Creating scan PDF...")
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 50, f"Scan Report")
    c.drawString(50, height - 80, f"Description: {scan.description}")
    c.drawString(50, height - 100, f"Scan Type: {scan.scan_type}")
    c.drawString(50, height - 120, f"Uploaded: {scan.upload_date.strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, height - 140, f"Doctor: Dr. {scan.doctor.username}")
    c.drawString(50, height - 160, f"Patient: {scan.patient.username}")

    if dicom_png_io:
        print("dicom_png_io is provided.")
        print("Type of dicom_png_io:", type(dicom_png_io))
        dicom_png_io.seek(0)
        try:
            image = ImageReader(dicom_png_io)
            iw, ih = image.getSize()
            print("Image size (pixels):", iw, ih)

            # Calculate scaled width and height preserving aspect ratio
            max_width = 400
            max_height = 400
            aspect = iw / ih

            if iw > ih:
                new_width = min(max_width, iw)
                new_height = new_width / aspect
            else:
                new_height = min(max_height, ih)
                new_width = new_height * aspect

            x = 50
            y = height - 200 - new_height  # leave space from top

            print("Drawing image at:", x, y, "with size:", new_width, new_height)

            c.drawImage(image, x, y, width=new_width, height=new_height, preserveAspectRatio=True)
            print("Image drawn on PDF.")
        except Exception as e:
            print("Error while drawing image:", e)
    else:
        print("No dicom_png_io provided.")

    margin_left = 50
    # Add comments header
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_left, y, "Comments:")
    y -= 20
    c.setFont("Helvetica", 10)

    # Iterate through comments ordered by timestamp ascending
    for comment in scan.comments.order_by('timestamp'):
        # Format: "[YYYY-MM-DD HH:MM] username: comment text"
        comment_text = f"[{comment.timestamp.strftime('%Y-%m-%d %H:%M')}] {comment.author.username}: {comment.text}"
        # Wrap the text if needed, simple approach:
        max_width = width - 2*margin_left
        wrapped_lines = []
        line = ""
        for word in comment_text.split():
            test_line = f"{line} {word}".strip()
            if c.stringWidth(test_line, "Helvetica", 10) < max_width:
                line = test_line
            else:
                wrapped_lines.append(line)
                line = word
        wrapped_lines.append(line)

        for line in wrapped_lines:
            if y < 50:  # start new page if too low
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 10)
            c.drawString(margin_left, y, line)
            y -= 14

    c.showPage()
    c.save()
    buffer.seek(0)
    print("PDF creation complete. Buffer size (bytes):", len(buffer.getvalue()))
    return buffer


def generate_scan_pdf(request, scan_id):
    scan = get_object_or_404(Scan, id=scan_id)

    dicom_png_io = None
    if scan.file.name.lower().endswith('.dcm'):
        try:
            dicom_png_io = dicom_to_png_bytes(scan.file.path)
            print("Type of dicom_png_io:", type(dicom_png_io))
            print("dicom_png_io.tell():", dicom_png_io.tell())  # Current cursor position
            print("dicom_png_io size (bytes):", len(dicom_png_io.getvalue()))
        except Exception as e:
            print(f"Error reading DICOM: {e}")

    pdf_buffer = create_scan_pdf(scan, dicom_png_io)
    return FileResponse(pdf_buffer, as_attachment=True, filename=f"scan_{scan.id}_report.pdf")