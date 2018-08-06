import os
import sys
path = '/media/data/hatzimin/web/'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'IMCProject.settings'

from django.contrib.auth.models import User
from provider.oauth2.models import Client
print sys.argv[1]
print sys.argv[0]

user = User(username=sys.argv[1],email=sys.argv[3])
user.set_password(sys.argv[2])
user.save()

