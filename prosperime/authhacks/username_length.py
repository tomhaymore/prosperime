# authhacks/username_length.py
import sys


def hack_models(length=72):
    from django.contrib.auth.models import User
    username = User._meta.get_field("username")
    email = User._meta.get_field("email")
    username.max_length = length
    email.max_length = length
    hack_validators(username.validators)
    hack_validators(email.validators)


def hack_forms(length=72, forms=[
        'django.contrib.auth.forms.UserCreationForm',
        'django.contrib.auth.forms.UserChangeForm',
        'django.contrib.auth.forms.AuthenticationForm',
    ]):
    """
    Hacks username length in django forms.
    """
    for form in forms:
        modulename, sep, classname = form.rpartition('.')
        if not modulename in sys.modules:
            __import__(modulename)
        module = sys.modules[modulename]
        klass = getattr(module, classname)
        hack_single_form(klass, length)


def hack_single_form(form_class, length=72):
    if hasattr(form_class, 'declared_fields'):
        fields = form_class.declared_fields
    elif hasattr(form_class, 'base_fields'):
        fields = form_class.base_fields
    else:
        raise TypeError('Provided object: %s doesnt seem to be a valid Form or '
                        'ModelForm class.' % form_class)
    username = fields['username']
    hack_validators(username.validators)
    username.max_length = length
    username.widget.attrs['maxlength'] = length
    if 'email' in fields:
        email = fields['email']
        hack_validators(email.validators)
        email.max_length = length
        email.widget.attrs['maxlength'] = length

def hack_validators(validators, length=72):
    from django.core.validators import MaxLengthValidator
    for key, validator in enumerate(validators):
        if isinstance(validator, MaxLengthValidator):
            validators.pop(key)
    validators.insert(0, MaxLengthValidator(length))
