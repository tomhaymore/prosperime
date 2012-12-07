from django.db import models
from django.contrib.auth.models import User, Account


class Entity(models.Model):
	

	name = models.CharField(max_length=450)
	type = models.CharField(max_length=25) # org or person
	subtype = models.CharField(max_length=50,blank=True,null=True) # firm, professional services, etc.
	summary = models.TextField(blank=True,null=True) # quick 1-2 sentence overview of entity
	description = models.TextField(blank=True,null=True) # more comprehensive overview
	web_url = models.URLField(blank=True,null=True)
	blog_url = models.URLField(blank=True,null=True)
	twitter_handle = models.CharField(max_length=250,blank=True,null=True)
	aliases = models.TextField(blank=True,null=True)
	domain = models.CharField(max_length=250,blank=True,null=True)
	founded_date = models.DateTimeField(blank=True,null=True)
	deadpooled_date = models.DateTimeField(blank=True,null=True)
	cb_type = models.CharField(max_length=25,blank=True,null=True)
	cb_updated = models.DateTimeField(blank=True,null=True)
	cb_permalink = models.CharField(max_length=250,blank=True,null=True) # Cruncbhase permalink
	cb_url = models.URLField(blank=True,null=True) # Crunchbase URL
	li_uniq_id = models.CharField(max_length=150,null=True) # LinkedIn unique id
	li_univ_name = models.CharField(max_length=450,null=True) # LinkedIn universal name 
	li_type = models.CharField(max_length=15,null=True)	
	total_money = models.CharField(max_length=15,null=True,blank=True)
	rels = models.ManyToManyField('self',symmetrical=False,through="Relationship") # for advising, employment relationships 
	no_employees = models.IntegerField(blank=True,null=True)
	size_range = models.CharField(max_length=2,null=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)
	status = models.CharField(max_length=15,default="active")
	
	# returns name
	def __unicode__(self):
		return self.name

class Image(models.Model):
	
	# returns path for uploading logos
	def _getLogoPath(self,filename):
		path = "logos/" + self.full_name + "/" + filename
		return path

	entity = models.ForeignKey(Entity)
	logo = models.ImageField(max_length=450,upload_to=_getLogoPath)
	source = models.CharField(max_length=450,null=True)
	logo_type = models.CharField(max_length=15,null=True)
	description = models.TextField(null=True)
	license = models.TextField(null=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)
	status = models.CharField(max_length=15,default="active")

	def __unicode__(self):
		# concatenate entity name, description and logo
		return " ".join([self.entity.name,self.description,'logo'])

class Position(models.Model):
	entity = models.ForeignKey(Entity)
	person = models.ForeignKey(User)
	title = models.CharField(max_length=150,null=True)
	summary = models.CharField(max_length=450,null=True)
	description = models.TextField(null=True)
	current = models.BooleanField(default=True)
	start_date = models.DateField(null=True)
	end_date = models.DateField(null=True)
	status = models.CharField(max_length=15,default="active")

	def __unicode__(self):
		return self.title + " at " + self.entity.name

class Relationship(models.Model):
	entity1 = models.ForeignKey(Entity,related_name="entity1")
	entity2 = models.ForeignKey(Entity,related_name="entity2")
	description = models.CharField(max_length=150) # employee, advisor, etc
	current = models.BooleanField() #
	attribution = models.URLField(blank=True,null=True)

class Financing(models.Model):
	investors = models.ManyToManyField(Entity,through="Investment")
	target = models.ForeignKey(Entity,related_name="target")
	round = models.CharField(max_length=15)
	amount = models.DecimalField(max_digits=15,decimal_places=2,null=True)
	currency = models.CharField(max_length=5)
	date = models.DateField(blank=True,null=True)
	source_url = models.URLField(blank=True,null=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

class Investment(models.Model):
	investor = models.ForeignKey(Entity,related_name="investor")
	financing = models.ForeignKey(Financing)
	amount = models.DecimalField(decimal_places=2,max_digits=15,null=True)

class Office(models.Model):
	entity = models.ForeignKey(Entity)
	description = models.CharField(max_length=450,blank=True,null=True)
	is_hq = models.BooleanField(null=True)
	addr_1 = models.CharField(max_length=150,blank=True,null=True)
	addr_2 = models.CharField(max_length=150,blank=True,null=True)
	addr_3 = models.CharField(max_length=150,blank=True,null=True)
	zip_code = models.CharField(max_length=45,blank=True,null=True)
	city = models.CharField(max_length=250,blank=True,null=True)
	state_code = models.CharField(max_length=5,blank=True,null=True)
	country_code = models.CharField(max_length=50,blank=True,null=True)
	latitude = models.DecimalField(decimal_places=7,max_digits=10,null=True)
	longitude = models.DecimalField(decimal_places=7,max_digits=10,null=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return self.entity.name() + " office"

	def name(self):
		return self.entity.name() + " office"	
