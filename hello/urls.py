from django.urls import path
from hello import views
from hello.models import LogMessage

home_list_view = views.HomeListView.as_view(
    queryset=LogMessage.objects.order_by("-log_date")[:5],  # :5 limits the results to the five most recent
    context_object_name="message_list",
    template_name="hello/home.html",
)

urlpatterns = [
    path("", home_list_view, name="home"),
    path("hello/<name>", views.hello_there, name="hello_there"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("log/", views.log_message, name="log"),
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path('doctor-dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('patient-dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('doctor-dashboard/upload_scan', views.upload_scan, name="upload_scan"),
    path('patient-dashboard/doctor_scans/<int:doctor_id>', views.doctor_scans, name='doctor_scans'),
    path('download-scan/<int:scan_id>/', views.download_scan, name='download_scan'),
    path('doctor-dashboard/patient_scans/<int:patient_id>', views.patient_scans, name='patient_scans'),
    path('scan/<int:scan_id>', views.scan_detail, name="scan_detail"),
]


