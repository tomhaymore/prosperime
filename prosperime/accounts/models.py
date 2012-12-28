# Python
import datetime

# Django
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

class Profile(models.Model):

    user = models.OneToOneField(User)
    first_name = models.CharField(max_length=150,null=True)
    middle_name = models.CharField(max_length=150,null=True)
    last_name = models.CharField(max_length=150,null=True)
    headline = models.TextField(null=True)
    connections = models.ManyToManyField('self',through="Connection",symmetrical=False)
    status = models.CharField(max_length=15,default="active")

    def full_name(self):
        full_name = self.first_name + " " + self.last_name
        return full_name

class Account(models.Model):
    service = models.CharField(max_length=45)
    owner = models.ForeignKey(User,related_name='account')
    address = models.CharField(max_length=450,null=True)
    access_token = models.CharField(max_length=200,null=True)
    token_secret = models.CharField(max_length=200,null=True)
    expires_on = models.DateTimeField(null=True)
    linked_on = models.DateTimeField(auto_now_add=True,null=True)
    last_scanned = models.DateTimeField(null=True)
    scanning_now = models.BooleanField(default=False)
    uniq_id = models.CharField(max_length=150,null=True)
    status = models.CharField(max_length=15,default="active")
    
    # returns name
    def __unicode__(self):
        return self.service

class Connection(models.Model):
    person1 = models.ForeignKey(Profile,related_name="person1")
    person2 = models.ForeignKey(Profile,related_name="person2")
    linked_on = models.DateTimeField(auto_now_add=True,null=True)
    service = models.CharField(max_length=45)
    status = models.CharField(max_length=15,default="active")

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)