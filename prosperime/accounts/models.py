# Python
import datetime

# Django
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

# Prosperime
from careers.models import Position, Career
import careers.careerlib as careerlib

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

    def _get_profile_pic_path(self, filename):
        path = "pictures/" + self.person.std_name() + "/" + filename
        return path

    user = models.OneToOneField(User)
    first_name = models.CharField(max_length=150,null=True)
    middle_name = models.CharField(max_length=150,null=True)
    last_name = models.CharField(max_length=150,null=True)
    headline = models.TextField(null=True)
    location = models.CharField(max_length=250,null=True)
    connections = models.ManyToManyField('self',through="Connection",symmetrical=False,related_name="connections+")
    status = models.CharField(max_length=15,default="active")
    prefs = models.TextField(null=True)
    # profile_pic = models.ImageField(max_length=450, upload_to=_get_profile_pic_path, blank=True, null=True)

    # returns a dictionary w/ frequencies of each career
    def get_all_careers(self):
        career_dict = {}

        # positions = Position.objects.filter(person=self.user).prefetch_related('careers')
        for p in self.user.positions.all():
            for c in p.careers.all():
                if career_dict.has_key(c):
                    career_dict[c] = career_dict[c] + 1
                else:
                    career_dict[c] = 1
        
        ## to test this beast
        # for item in career_dict:
        #      print item.short_name + ': ' + str(career_dict.get(item))

        return career_dict

    # returns career(s) w/ highest frequency among profile's positions
    def get_top_careers(self):
        all_careers = self.all_careers
        top_careers = []
        top_frequency = 0

        for career, frequency in all_careers.iteritems():
            if frequency > top_frequency:
                del top_careers[:] # this just clears the list
                top_frequency = frequency
                top_careers.append(career)
            if frequency == top_frequency:
                top_careers.append(career)
        return top_careers

    def get_top_career(self,limit=1):
       careers = careerlib.get_focal_careers(self.user,limit)
       return careers


    def get_all_careers(self,limit=5):
       careers = careerlib.get_focal_careers(self.user,limit)
       return careers

    # Properties of the Profile object
    top_careers = property(get_top_careers)
    all_careers = property(get_all_careers)

    ### Helpers ###
    def full_name(self):
        if self.first_name and self.last_name:
            full_name = self.first_name + " " + self.last_name
        elif self.first_name:
            full_name = self.first_name
        else:
            full_name = self.last_name
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

    def latest_position(self):
        positions = self.user.positions.all().order_by('-start_date').exclude(type="education")
        if positions.exists():
            return positions[0]
        else:
            return None

    def latest_position_with_ideal(self):
        positions = self.user.positions.all().order_by('-start_date').exclude(type="education").exclude(ideal_position=None)
        if positions.exists():
            return positions[0]
        else:
            return None

    def educations(self):
        return self.user.positions.all().filter(type="education").order_by('start_date')

    def _industries(self):
        all_domains = []
        positions = self.user.positions.all().order_by('-start_date')
        for pos in positions:
            domains = [i for i in pos.entity.domains.all() if i is not None ]
            all_domains = all_domains + domains
        return all_domains

    def default_profile_pic(self):
        if self.pictures.all():
            return self.pictures.all()[0].pic.url
        else:
            return "/media/pictures/anon.jpg"

    domains = property(_industries)
    
    # Strategy: grab top career path, find others w/ same top career path
    def get_similar_users(self):
        top_career_path = get_top_career(self)

    def add_pref(self,key,value):
        if self.prefs:
            prefs = json.loads(prefs)
            prefs[key] = value
        else:
            prefs = {
                key:value
            }
        self.prefs = json.dumps(prefs)
        self.save()

    def current_position(self):
        positions = self.user.positions.all().order_by('-start_date').exclude(type="education")
        if positions.exists():
            return positions[0].title + " at " + positions[0].entity.name
        else:
            return None

    def first_ideal(self):
        positions = self.user.positions.all().exclude(ideal_position=None).exclude(type="education").exclude(title="Student").order_by("start_date").select_related("entity")
        if positions.exists():
            return positions[0].ideal_position
        else:
            return None

    def bio_simple(self):
        return [{'title':p.title,'id':p.id} for p in self.user.positions.all()]

    def bio_simple_pretty_print(self):
        return [(p.title + " at " + p.entity.name + " --> ") for p in self.user.positions.all()]

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
