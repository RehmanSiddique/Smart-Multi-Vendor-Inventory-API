import os
import django
from django.contrib.auth import authenticate
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User

email = 'admin@acme.com'
password = 'testpass123'

try:
    user = User.objects.get(email=email)
    print(f"USER_FOUND: {user.email}")
    print(f"IS_ACTIVE: {user.is_active}")
    print(f"IS_STAFF: {user.is_staff}")
    print(f"ROLE: {user.role}")
    
    auth_user = authenticate(email=email, password=password)
    if auth_user:
        print("AUTH_SUCCESS: True")
    else:
        print("AUTH_SUCCESS: False")
except User.DoesNotExist:
    print("USER_NOT_FOUND")
except Exception as e:
    print(f"ERROR: {str(e)}")
