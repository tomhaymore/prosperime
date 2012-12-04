# Python
import datetime

# Django
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

class Profile(models.Model):
	
	# returns path for uploading logos
	def _getFullName(self):
		full_name = self.first_name + " " + self.last_name
		return full_name

	user = models.OneToOneField(User)
	full_name = models.CharField(max_length=250,null=True,default=_getFullName)
	first_name = models.CharField(max_length=150,null=True)
	middle_name = models.CharField(max_length=150,null=True)
	last_name = models.CharField(max_length=150,null=True)
	headline = models.TextField(null=True)

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

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)