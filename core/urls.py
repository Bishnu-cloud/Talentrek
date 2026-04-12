from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('login/', views.auth_view, {"page_type": "login"}, name="login"),
    path('register/', views.auth_view, {"page_type": "register"}, name="register"),
    path('logout/', views.logout_view, name='logout'),
    
    # Unified Dashboard (Let the view handle the role logic)
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Student Section
    path('student/profile/', views.student_profile_view, name='student_profile'), # Changed name to match template
    path('messages/', views.student_messages_list, name='student_messages_list'),
    path('messages/<int:company_id>/', views.student_message_thread, name='student_message_thread'),
    # urls.py
    path('profile/generate-avatar/', views.generate_avatar, name='generate_avatar'),

    # Internships
    path('internships/', views.internship_list, name='internship_list'),
    path('internships/create/', views.internship_create, name='internship_create'),
    path('internships/<int:pk>/', views.internship_detail, name='internship_detail'),
    path('internships/<int:pk>/edit/', views.internship_edit, name='internship_edit'),
    path('internships/<int:pk>/delete/', views.internship_delete, name='internship_delete'),

    # Applications
    path('internships/<int:pk>/apply/', views.apply_internship, name='apply_internship'),
    path('application/<int:pk>/', views.application_detail, name='application_detail'),
    path('application/<int:pk>/accept/', views.accept_application, name='accept_application'),
    path('application/<int:pk>/reject/', views.reject_application, name='reject_application'),
    path('application/<int:pk>/shortlist/', views.toggle_shortlist, name='toggle_shortlist'),
    path('applications/accepted/', views.accepted_applications, name='accepted_applications'), 

    # Company Section
    path('company/profile/', views.company_profile_view, name='company_profile'),
    path('company/students/', views.company_students_view, name='company_students'),
    path('company/messages/', views.company_messages_list, name='company_messages'),
    path('company/messages/<int:student_id>/', views.company_message_thread, name='company_message_thread'),

    # AI Tools
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('mock-interview/', views.mock_interview_view, name='mock_interview'),
]