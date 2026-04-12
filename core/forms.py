from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile, MicroInternship, Application, Message

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'headline', 'bio', 'skills', 
            'university', 'major', 'graduation_year', 'gpa',
            'linkedin_url', 'github_url', 'profile_picture', 'resume_pdf',
            'hair_type', 'has_specs'
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full bg-slate-900 border-slate-700 rounded-xl p-3 text-white'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full bg-slate-900 border-slate-700 rounded-xl p-3 text-white'}),
            'headline': forms.TextInput(attrs={'class': 'w-full bg-slate-900 border-slate-700 rounded-xl p-3 text-white', 'placeholder': 'Web Developer | Designer'}),
            'bio': forms.Textarea(attrs={'class': 'w-full bg-slate-900 border-slate-700 rounded-xl p-3 text-white', 'rows': 3}),
            'skills': forms.TextInput(attrs={'class': 'w-full bg-slate-900 border-slate-700 rounded-xl p-3 text-white', 'placeholder': 'Python, Django...'}),
            # FIXED: Used URLInput instead of URLField
            'linkedin_url': forms.URLInput(attrs={'class': 'w-full bg-slate-900 border-slate-700 rounded-xl p-3 text-white'}),
            'github_url': forms.URLInput(attrs={'class': 'w-full bg-slate-900 border-slate-700 rounded-xl p-3 text-white'}),
            'university': forms.TextInput(attrs={'class': 'w-full bg-slate-800 border-slate-700 rounded-lg h-12 text-white px-4'}),
            'major': forms.TextInput(attrs={'class': 'w-full bg-slate-800 border-slate-700 rounded-lg h-12 text-white px-4'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'w-full bg-slate-800 border-slate-700 rounded-lg h-12 text-white px-4'}),
            'gpa': forms.TextInput(attrs={'class': 'w-full bg-slate-800 border-slate-700 rounded-lg h-12 text-white px-4'}),
        }



class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            UserProfile.objects.create(user=user, role=self.cleaned_data['role'])
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

class MicroInternshipForm(forms.ModelForm):
    class Meta:
        model = MicroInternship
        # REMOVED: contact, subscribers, and tagged_coworkers from this list
        fields = [
            'title', 'description', 'primary_role', 'type_of_position', 
            'work_experience', 'skills_required', 'location', 
            'remote_work_details', 'min_salary', 'max_salary', 'equity', 'company_size'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Dark Theme Styling to all fields (Dropdowns, Text, etc.)
        standard_class = (
            "w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg "
            "text-white focus:ring-2 focus:ring-indigo-500 outline-none "
            "placeholder:text-slate-500"
        )
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': standard_class})
            
            # 2. Specific placeholders for the new Rupee fields
        self.fields['title'].widget.attrs.update({'placeholder': 'e.g. Django Developer Intern'})
        self.fields['description'].widget.attrs.update({'rows': '4', 'placeholder': 'Describe the mission...'})
        self.fields['min_salary'].widget.attrs.update({'placeholder': 'Min (e.g. 5000)'})
        self.fields['max_salary'].widget.attrs.update({'placeholder': 'Max (e.g. 15000)'})
        
        # Update other placeholders
        self.fields['work_experience'].widget.attrs.update({'placeholder': 'e.g. Fresher / 6 months'})
        self.fields['skills_required'].widget.attrs.update({'placeholder': 'e.g. Python, Django, HTML'})
        self.fields['location'].widget.attrs.update({'placeholder': 'e.g. Jaipur / Remote'})

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['resume', 'skills', 'experience', 'motivation', 'availability', 'portfolio', 'cover_letter']
        widgets = {
            'skills': forms.TextInput(attrs={
                'placeholder': 'e.g. Python, Django, React',
                'class': 'w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white outline-none'
            }),
            'experience': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe your past experience...',
                'class': 'w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white outline-none'
            }),
            'motivation': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Why do you want to work with this company?',
                'class': 'w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white outline-none'
            }),
            'availability': forms.TextInput(attrs={
                'placeholder': 'e.g. 20 hrs/week',
                'class': 'w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white outline-none'
            }),
            'portfolio': forms.URLInput(attrs={
                'placeholder': 'GitHub / Portfolio link',
                'class': 'w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white outline-none'
            }),
            'cover_letter': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Anything else...',
                'class': 'w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white outline-none'
            }),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Write a message...', 
                'class': 'w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:ring-2 focus:ring-indigo-500 outline-none'
            })
        }