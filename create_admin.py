# create_admin.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talentrek.settings')
django.setup()

from django.contrib.auth.models import User

# Change these to what you want
username = 'admin_live'
email = 'admin@talentrek.com'
password = 'YourSecurePassword123' 

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"✅ Superuser {username} created successfully!")
else:
    print(f"ℹ️ Superuser {username} already exists.")