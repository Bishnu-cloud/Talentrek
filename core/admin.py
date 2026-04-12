from django.contrib import admin
from .models import UserProfile, MicroInternship, Application, MessageThread, Message

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'university', 'profile_completed')
    list_filter = ('role', 'graduation_year')
    search_fields = ('user__username', 'university', 'major')

@admin.register(MicroInternship)
class MicroInternshipAdmin(admin.ModelAdmin):
    # Fixed: Removed 'is_remote' and 'duration_weeks' which caused the crash
    list_display = (
        'title', 
        'company', 
        'primary_role', 
        'type_of_position', 
        'location', 
        'is_active', 
        'created_at'
    )
    # Added filters for your new Wellfound-style categories
    list_filter = ('is_active', 'primary_role', 'type_of_position', 'remote_work_details', 'company_size')
    search_fields = ('title', 'description', 'company__username', 'location')
    ordering = ('-created_at',)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('internship', 'student', 'status', 'is_shortlisted', 'match_score', 'created_at')
    list_filter = ('status', 'is_shortlisted')
    search_fields = ('internship__title', 'student__username', 'skills')

@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ('company', 'student', 'created_at')
    search_fields = ('company__username', 'student__username')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'thread', 'sent_at', 'read')
    list_filter = ('read', 'sent_at')
    search_fields = ('text', 'sender__username')