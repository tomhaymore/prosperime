# Python
import datetime

# Django
from django.db import models
from django.contrib.auth.models import User
# from entities.models import Position
from django.db.models.signals import post_save

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
    public_url = models.URLField(max_length=450,null=True)
    status = models.CharField(max_length=15,default="active")
    
    # returns name
    def __unicode__(self):
        return self.service

class Profile(models.Model):

    user = models.OneToOneField(User)
    first_name = models.CharField(max_length=150,null=True)
    middle_name = models.CharField(max_length=150,null=True)
    last_name = models.CharField(max_length=150,null=True)
    headline = models.TextField(null=True)
    connections = models.ManyToManyField('self',through="Connection",symmetrical=False,related_name="connections+")
    status = models.CharField(max_length=15,default="active")

    def full_name(self):
        full_name = self.first_name + " " + self.last_name
        return full_name

    def std_name(self):
        return "_".join([self.first_name,self.last_name]).lower().replace(" ","_")

    def li_linked(self):
        accts = Account.objects.filter(owner=self.user,service="linkedin",status="active")
        if accts.exists():
            return True
        return False

    def no_of_positions(self):
        from entities.models import Position
        pos = Position.objects.filter(person=self.user)
        return len(pos)

    def _industries(self):
        all_domains = []
        positions = self.user.positions
        for pos in positions.all():
            domains = [i for i in pos.entity.domains.all() if i is not None ]
            all_domains = all_domains + domains
        return all_domains

    def default_profile_pic(self):
        if self.pictures.all():
            return self.pictures.all()[0].pic

    # domains = property(_industries)


class Picture(models.Model):

    # returns path for uploading pictures
    def _get_picture_path(self,filename):
        path = "pictures/" + self.person.std_name() + "/" + filename
        return path

    person = models.ForeignKey(Profile,related_name="pictures")
    pic = models.ImageField(max_length=450,upload_to=_get_picture_path)
    source = models.CharField(max_length=45,null=True)
    description = models.TextField(null=True)
    license = models.TextField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=15,default="active")


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