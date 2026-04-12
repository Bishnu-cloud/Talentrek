import os
from django.db import models
from django.contrib.auth.models import User

def student_file_path(instance, filename):
    # Organizes uploads by user ID
    return os.path.join('students', str(instance.user.id), filename)

# models.py
class UserProfile(models.Model):
     
    ROLE_CHOICES = [('student', 'Student'), ('company', 'Company')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    role = models.CharField(max_length=10, choices=[('student', 'Student'), ('company', 'Company')])
    
    # NEW FIELDS (Notice: No "placeholder" here!)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    headline = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(max_length=1000, blank=True, null=True)
    skills = models.CharField(max_length=500, blank=True, null=True)
    linkedin_url = models.URLField(max_length=500, blank=True, null=True)
    github_url = models.URLField(max_length=500, blank=True, null=True)
    resume_pdf = models.FileField(upload_to='resumes/', blank=True, null=True)

    # EXISTING FIELDS
    university = models.CharField(max_length=255, blank=True, null=True)
    major = models.CharField(max_length=255, blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)
    gpa = models.CharField(max_length=10, blank=True, null=True)

    company_name = models.CharField(max_length=255, blank=True, null=True)
    website_link = models.URLField(max_length=500, blank=True, null=True)
    
    profile_completed = models.BooleanField(default=False)

    # New Likeness Fields
    HAS_SPECS_CHOICES = [(True, 'Yes'), (False, 'No')]
    HAIR_CHOICES = [('wavy', 'Wavy'), ('straight', 'Straight'), ('curly', 'Curly'), ('bald', 'Bald')]
    
    has_specs = models.BooleanField(default=False, choices=HAS_SPECS_CHOICES)
    hair_type = models.CharField(max_length=20, choices=HAIR_CHOICES, default='straight')
    generated_avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def get_avatar_prompt(self):
        """Assembles the prompt based on your identity"""
        specs_text = "wearing glasses" if self.has_specs else ""
        return f"A professional 3D Pixar-style avatar of a web developer with {self.hair_type} hair {specs_text}, high quality, cinematic lighting, solid background."

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class MicroInternship(models.Model):
    PRIMARY_ROLE_CHOICES = [
        ('Engineering', (
            ('software_eng', 'Software Engineer'),
            ('mobile_dev', 'Mobile Developer'),
            ('frontend_eng', 'Frontend Engineer'),
            ('backend_eng', 'Backend Engineer'),
            ('fullstack_eng', 'Full-Stack Engineer'),
            ('machine_learning', 'Machine Learning Engineer'),
        )),
        ('Design', (
            ('uiux_designer', 'UI/UX Designer'),
            ('product_designer', 'Product Designer'),
            ('graphic_designer', 'Graphic Designer'),
        )),
        ('Operations', (
            ('hr', 'H.R.'),
            ('finance', 'Finance/Accounting'),
            ('ops_manager', 'Operations Manager'),
        )),
        ('Sales/Marketing', (
            ('business_dev', 'Business Development'),
            ('marketing_mgr', 'Marketing Manager'),
            ('content_creator', 'Content Creator'),
        )),
    ]

    class PositionType(models.TextChoices):
        FULL_TIME = 'FT', 'Full-time Employee'
        CONTRACTOR = 'CON', 'Contractor'
        COFOUNDER = 'COF', 'Cofounder'
        INTERN = 'INT', 'Intern'

    class RemoteDetails(models.TextChoices):
        IN_OFFICE = 'OFF', 'In Office'
        ONSITE = 'ONS', 'Onsite'
        REMOTE = 'REM', 'Remote'
        REMOTE_ONLY = 'REMO', 'Remote Only'

    class CompanySize(models.TextChoices):
        S1 = '1-10', '1-10 Employees'
        S2 = '11-50', '11-50 Employees'
        S3 = '51-200', '51-200 Employees'
        S4 = '501+', '501+ Employees'

    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name="internships")
    title = models.CharField(max_length=255)
    description = models.TextField()
    primary_role = models.CharField(max_length=50, choices=PRIMARY_ROLE_CHOICES, default='software_eng')
    type_of_position = models.CharField(max_length=10, choices=PositionType.choices, default=PositionType.INTERN)
    
    # Placeholder removed from here to prevent TypeError
    work_experience = models.CharField(max_length=100) 
    skills_required = models.TextField(blank=True, help_text="Comma separated skills")
    
    location = models.CharField(max_length=255)
    remote_work_details = models.CharField(max_length=10, choices=RemoteDetails.choices, default=RemoteDetails.IN_OFFICE)

    duration = models.PositiveIntegerField(help_text="Duration in weeks", default=4)
    
    min_salary = models.PositiveIntegerField(default=0, help_text="Min stipend in ₹")
    max_salary = models.PositiveIntegerField(default=0, help_text="Max stipend in ₹")
    equity = models.CharField(max_length=100, blank=True, null=True)
    
    primary_recruiting_contact = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_jobs")
    subscribers = models.ManyToManyField(User, related_name="subscribed_jobs", blank=True)
    tagged_coworkers = models.ManyToManyField(User, related_name="tagged_jobs", blank=True)
    
    company_size = models.CharField(max_length=20, choices=CompanySize.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def skill_list(self):
        if not self.skills_required:
            return []
        return [s.strip() for s in self.skills_required.split(",") if s.strip()]

class Application(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    internship = models.ForeignKey(MicroInternship, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/')
    motivation = models.TextField(blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    availability = models.CharField(max_length=100, blank=True, null=True)
    portfolio = models.URLField(blank=True, null=True)
    skills = models.CharField(max_length=255, blank=True)
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    is_shortlisted = models.BooleanField(default=False)
    match_score = models.IntegerField(default=0)

    @property
    def get_match_score(self):
        if not self.internship.skills_required or not self.skills:
            return 0
        # Normalize and compare skills
        job_set = set([s.strip().lower() for s in self.internship.skills_required.split(",")])
        candidate_set = set([s.strip().lower() for s in self.skills.split(",")])
        matched = job_set.intersection(candidate_set)
        
        if not job_set: return 0
        return int((len(matched) / len(job_set)) * 100)

class MessageThread(models.Model):
    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_threads')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_threads')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('company', 'student')
        ordering = ['-created_at']

class Message(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    class Meta:
        ordering = ['sent_at']