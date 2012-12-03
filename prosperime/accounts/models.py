# Python
import datetime

# Django
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
	user = models.OneToOneField(User)
	full_name = models.CharField(max_length=250,null=True)
	first_name = models.CharField(max_length=150,null=True)
	middle_name = models.CharField(max_length=150,null=True)
	last_name = models.CharField(max_length=150,null=True)

class Account(models.Model):
    service = models.CharField(max_length=45)
    owner = models.ForeignKey(User)
    address = models.CharField(max_length=450)
    access_token = models.CharField(max_length=200)
    token_secret = models.CharField(max_length=200)
    expires_on = models.DateTimeField(null=True)
    linked_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15,default="active")
    
    # returns name
    def __unicode__(self):
        return self.service