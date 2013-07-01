# authhacks/models.py
from django.conf import settings
from authhacks import username_length


USERNAME_MAXLENGTH = getattr(settings, 'USERNAME_MAXLENGTH', 72)

username_length.hack_models()
username_length.hack_forms()