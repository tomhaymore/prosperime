from django.conf import settings
from django.contrib.auth.models import User
from accounts.models import Account

class LinkedinBackend:

    supports_inactive_user = True

    def authenticate(self,acct_id=None):
        try:
            return User.objects.get(account__uniq_id=acct_id,profile__status='active')
            # acct = Account.objects.get(service="linkedin",uniq_id=acct_id)
        except:
            return None
        # return acct.owner

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class EmailOrUsernameModelBackend(object):
    def authenticate(self, username=None, password=None):
        if '@' in username:
            kwargs = {'email': username}
        else:
            kwargs = {'username': username}
        try:
            user = User.objects.get(**kwargs)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None