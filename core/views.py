from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from django.views.decorators.csrf import csrf_exempt
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

import json
import os
import pdfplumber
from django.conf import settings


from groq import Groq
from dotenv import load_dotenv

import requests
from django.core.files.base import ContentFile

load_dotenv()

from .forms import RegistrationForm, LoginForm, MicroInternshipForm, ApplicationForm, MessageForm, StudentProfileForm
from .models import MicroInternship, Application, UserProfile, MessageThread, Message

User = get_user_model()

# --- Helper Functions ---

def get_user_profile(user):
    return UserProfile.objects.filter(user=user).first()

def is_student(user):
    profile = get_user_profile(user)
    return profile is not None and profile.role == 'student'

def is_company(user):
    profile = get_user_profile(user)
    return profile is not None and profile.role == 'company'

def calculate_match_score(job_skills, candidate_skills):
    if not job_skills or not candidate_skills:
        return 0
    job_set = set([s.strip().lower() for s in job_skills.split(",")])
    candidate_set = set([s.strip().lower() for s in candidate_skills.split(",")])
    matched = job_set.intersection(candidate_set)
    return int((len(matched) / len(job_set)) * 100) if job_set else 0

# --- Public & Auth Views ---

def home(request):
    internships = MicroInternship.objects.filter(is_active=True).order_by('-created_at')[:5]
    return render(request, 'home.html', {'internships': internships})

def auth_view(request, page_type):
    if page_type == "register":
        form = RegistrationForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            user = form.save()
            
            user = authenticate(request, username=user.username, password=form.cleaned_data.get("password1"))
            login(request, user)
            return redirect("dashboard")
    else:
        form = LoginForm(request, data=request.POST or None)
        if request.method == "POST" and form.is_valid():
            login(request, form.get_user())
            return redirect("dashboard")
    return render(request, "auth.html", {"form": form, "page_type": page_type})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

# --- Dashboards ---

@login_required
def dashboard_view(request):
    if is_company(request.user):
        today = timezone.now().date()
        base_qs = MicroInternship.objects.filter(company=request.user)
        internships = base_qs.annotate(applicant_count=Count('application'))
        total_min_budget = base_qs.aggregate(Sum('min_salary'))['min_salary__sum'] or 0
        
        applications = Application.objects.filter(
            internship__company=request.user, status="pending"
        ).select_related('student', 'internship')

        for app in applications:
            app.match_score = calculate_match_score(app.internship.skills_required, app.skills)

        context = {
            'internships': internships,
            'total_applicants': applications.count(),
            'total_min_budget': total_min_budget,
            'today': today,
        }
        return render(request, 'company_dashboard.html', context)

    if is_student(request.user):
        profile = get_user_profile(request.user)
        if profile and not profile.profile_completed:
            return redirect('student_profile')
        
        # 1. Fetch the applications
        apps = Application.objects.filter(student=request.user).select_related('internship', 'internship__company')
        
        # 2. ADD THESE CALCULATIONS for your dashboard cards
        context = {
            'applications': apps,
            'total_applications': apps.count(),
            'active_applications': apps.filter(status='pending').count(),
            'accepted_applications': apps.filter(status='accepted').count(),
            'threads': MessageThread.objects.filter(student=request.user).select_related('company')
        }
        return render(request, 'student_dashboard.html', context)

    return redirect('select_role')

# --- Internship CRUD ---

def internship_list(request):
    internships = MicroInternship.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'internship_list.html', {'internships': internships})

def internship_detail(request, pk):
    internship = get_object_or_404(MicroInternship, pk=pk)
    
    # --- ADD THESE LINES ---
    # Fetch all applications for this specific internship
    applications = Application.objects.filter(internship=internship).select_related('student')
    
    # (Optional) Calculate match scores for the company view
    for app in applications:
        app.match_score = calculate_match_score(internship.skills_required, app.skills)
    # -----------------------

    has_applied = request.user.is_authenticated and Application.objects.filter(internship=internship, student=request.user).exists()
    
    return render(request, 'internship_detail.html', {
        'internship': internship,
        'applications': applications,  # <-- This sends the list to your HTML
        'has_applied': has_applied,
        'can_apply': is_student(request.user),
    })

@login_required
@user_passes_test(is_company)
def internship_create(request):
    if request.method == 'POST':
        # 1. Grab data directly from the POST dictionary
        min_sal = request.POST.get('min_salary')
        max_sal = request.POST.get('max_salary')
        title = request.POST.get('title')
        description = request.POST.get('description')
        role = request.POST.get('primary_role')
        pos_type = request.POST.get('type_of_position')
        exp = request.POST.get('work_experience')
        loc = request.POST.get('location')
        c_size = request.POST.get('company_size')
        skills = request.POST.get('skills_required')

        # 2. Create the object manually (Bypasses form.is_valid logic)
        try:
            new_job = MicroInternship.objects.create(
                company=request.user,
                title=title,
                description=description,
                primary_role=role,
                type_of_position=pos_type,
                work_experience=exp,
                location=loc,
                min_salary=min_sal if min_sal else 0,
                max_salary=max_sal if max_sal else 0,
                company_size=c_size,
                skills_required=skills
            )
            messages.success(request, "Project Published!")
            return redirect('dashboard')
        except Exception as e:
            # This will show you exactly which database field is complaining
            print(f"DATABASE ERROR: {e}")
            messages.error(request, f"Database Error: {e}")

    # For a GET request, we still send the form to render the fields
    form = MicroInternshipForm()
    return render(request, 'internship_form.html', {'form': form})

@login_required
@user_passes_test(is_company)
def internship_edit(request, pk):
    internship = get_object_or_404(MicroInternship, pk=pk, company=request.user)
    form = MicroInternshipForm(request.POST or None, instance=internship)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('dashboard')
    return render(request, 'internship_form.html', {'form': form, 'title': 'Edit Internship'})

@login_required
@user_passes_test(is_company)
def internship_delete(request, pk):
    internship = get_object_or_404(MicroInternship, pk=pk, company=request.user)
    if request.method == "POST":
        internship.delete()
        return redirect('dashboard')
    return render(request, 'confirm_delete.html', {'object': internship})

# --- Applications ---

@login_required
@user_passes_test(is_student)
def apply_internship(request, pk):
    internship = get_object_or_404(MicroInternship, pk=pk)
    form = ApplicationForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        app = form.save(commit=False)
        app.student, app.internship = request.user, internship
        app.save()
        return redirect('dashboard')
    return render(request, 'application_form.html', {'form': form, 'internship': internship})

@login_required
@user_passes_test(is_company)
def accept_application(request, pk):
    application = get_object_or_404(Application, pk=pk)
    application.status = "accepted"
    application.save()
    
    # 1. Create or Get the Thread
    thread, created = MessageThread.objects.get_or_create(
        company=request.user, 
        student=application.student
    )
    
    # 2. (Optional) Send an automated first message
    if created:
        Message.objects.create(
            thread=thread,
            sender=request.user,
            text=f"Hi {application.student.username}, I've accepted your application for '{application.internship.title}'. Let's discuss the next steps!"
        )

    messages.success(request, f"Accepted {application.student.username}! Chat started.")
    
    # 3. REDIRECT to the actual chat page
    return redirect('company_message_thread', student_id=application.student.id)

@login_required
@user_passes_test(is_company)
def reject_application(request, pk):
    application = get_object_or_404(Application, pk=pk)
    application.status = "rejected"
    application.save()
    return redirect("dashboard")

@login_required
@user_passes_test(is_company)
def toggle_shortlist(request, pk):
    app = get_object_or_404(Application, pk=pk)
    app.is_shortlisted = not app.is_shortlisted
    app.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
@user_passes_test(is_company)
def accepted_applications(request):
    internships = MicroInternship.objects.filter(company=request.user)
    return render(request, "accepted_applications.html", {"internships": internships})

# --- Messaging (The Fix) ---

@login_required
def company_messages_list(request):
    threads = MessageThread.objects.filter(company=request.user)
    return render(request, "company_messages_list.html", {"threads": threads})

@login_required
def company_message_thread(request, student_id):
    student = get_object_or_404(User, pk=student_id)
    thread, _ = MessageThread.objects.get_or_create(company=request.user, student=student)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.thread, msg.sender = thread, request.user
            msg.save()
            return redirect('company_message_thread', student_id=student_id)
    
    thread.messages.filter(sender=student, read=False).update(read=True)
    return render(request, 'company_message_thread.html', {
        'thread': thread, 'student': student, 'messages': thread.messages.order_by('sent_at'), 'form': MessageForm()
    })

@login_required
@user_passes_test(is_student)
def student_message_thread(request, company_id):
    company = get_object_or_404(User, pk=company_id)
    thread, _ = MessageThread.objects.get_or_create(company=company, student=request.user)
    if request.method == "POST":
        text = request.POST.get("message")
        if text: Message.objects.create(thread=thread, sender=request.user, text=text)
    return render(request, "student_message_thread.html", {
        'thread': thread, 'messages': thread.messages.order_by("sent_at"), 'company': company
    })


@login_required
@user_passes_test(is_student)
def student_messages_list(request):
    # This gets every thread where the student is involved
    threads = MessageThread.objects.filter(student=request.user).select_related('company')
    return render(request, "student_messages_list.html", {"threads": threads})

# --- AI & Profile ---
@csrf_exempt
@login_required
def chatbot_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message')
        except:
            user_message = request.POST.get('message')

        if not user_message:
            return JsonResponse({'reply': "I didn't catch that. Could you say it again?"})

        # Fetch active jobs and include the new salary range in the prompt
        active_jobs = MicroInternship.objects.filter(is_active=True)
        job_details = ""
        for job in active_jobs:
            # We provide the AI with the specific range now
            job_details += (
                f"- {job.title} at {job.company.username}. "
                f"Location: {job.location}. "
                f"Stipend Range: ₹{job.min_salary} to ₹{job.max_salary}\n"
            )

        if not job_details:
            job_details = "No active jobs currently available."

        api_key = os.getenv("GROQ_API_KEY")
        client = Groq(api_key=api_key)

        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "You are the Talentrek Scout. Your goal is to help students find projects. "
                            f"Here are the current available listings:\n{job_details}\n"
                            "Be professional, concise, and always mention the stipend range if asked about pay."
                        )
                    },
                    {"role": "user", "content": user_message}
                ],
            )
            return JsonResponse({'reply': completion.choices[0].message.content})
            
        except Exception as e:
            print(f"GROQ ERROR: {e}") 
            return JsonResponse({'reply': "I'm having a bit of trouble reaching the database. Please try again later!"})

    return JsonResponse({'error': 'Invalid request'}, status=400)
            
@login_required
@user_passes_test(is_student)
def mock_interview_view(request):
    return render(request, 'mock_interview.html')

@login_required
def student_profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # request.FILES is required for profile_picture and resume_pdf
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            form.save() # This saves everything in the fields list at once
            profile.profile_completed = True
            profile.save()
            messages.success(request, "Profile saved successfully!")
            return redirect('dashboard')
    else:
        form = StudentProfileForm(instance=profile)
    
    return render(request, 'student_profile.html', {'form': form})

@login_required
@user_passes_test(is_company)
def company_students_view(request):
    students = User.objects.filter(userprofile__role="student")
    return render(request, "company_students.html", {"students_applied": students})

@login_required
@user_passes_test(is_company)
def application_detail(request, pk):
    application = get_object_or_404(Application, pk=pk)
    # Ensure the company viewing this actually owns the internship
    if application.internship.company != request.user:
        return redirect('dashboard')

    application.match_score = calculate_match_score(
        application.internship.skills_required, 
        application.skills
    )
        
    return render(request, 'application_detail.html', {'application': application})

@login_required
@user_passes_test(is_company)
def company_profile_view(request):
    # Get or create profile for the company user
    profile, created = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'company'})
    
    if request.method == 'POST':
        profile.company_name = request.POST.get('company_name')
        profile.website_link = request.POST.get('website_link')
        profile.profile_completed = True
        profile.save()
        
        messages.success(request, "Company profile updated successfully!")
        return redirect('dashboard')
        
    return render(request, 'company_profile.html', {'profile': profile})

@login_required
def generate_avatar(request):
    profile = request.user.userprofile
    
    # 1. Get your prompt (e.g., "web developer with wavy hair and glasses")
    raw_prompt = profile.get_avatar_prompt()
    
    # 2. Clean the prompt for a URL (removes spaces/special characters)
    encoded_prompt = requests.utils.quote(raw_prompt)
    
    # 3. Use Pollinations.ai (Free, no key needed!)
    image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=512&height=512&model=flux&seed=42"

    try:
        # Download the generated image
        response = requests.get(image_url, timeout=30)
        
        if response.status_code == 200:
            # 4. Save to your model
            profile.generated_avatar.save(
                f"avatar_{request.user.id}.png", 
                ContentFile(response.content),
                save=True
            )
            profile.save()
            messages.success(request, "Digital Likeness Synchronized via Flux Engine!")
        else:
            messages.error(request, "The AI imaging satellite is offline. Try again later.")

    except Exception as e:
        print(f"Error: {e}")
        messages.error(request, "Connection to AI Protocol failed.")
        
    return redirect('student_profile')

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        # Ensure a profile exists the moment they sign up
        UserProfile.objects.get_or_create(user=user)
        return user

    def pre_social_login(self, request, sociallogin):
        # Connect existing email accounts to Google automatically
        user = sociallogin.user
        if user.id:
            return
        try:
            customer = User.objects.get(email=user.email)
            sociallogin.connect(request, customer)
        except User.DoesNotExist:
            pass
    
def select_role(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.role = role
        profile.save()
        return redirect('dashboard')
    return render(request, 'select_role.html')

def login_redirect_view(request):
    # Get the user's profile
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        # If no profile exists, create one and ask for a role
        UserProfile.objects.create(user=request.user)
        return redirect('select_role')

    # If they haven't picked a role yet, send them to the selection page
    if not profile.role:
        return redirect('select_role')
    
    # If they are a student, send to student dashboard
    if profile.role == 'student':
        return redirect('student_dashboard')
    
    # If they are a company, send to company dashboard
    elif profile.role == 'company':
        return redirect('company_dashboard')
    
    # Default fallback
    return redirect('select_role')

try:
    if not User.objects.filter(username='admin_live').exists():
        User.objects.create_superuser('admin_live', 'admin@test.com', 'YourPassword123')
        print("✅ Live Admin Created!")
except Exception as e:
    print(f"Admin creation skipped: {e}")