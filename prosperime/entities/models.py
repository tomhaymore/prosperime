from django.db import models

# Create your models here.
class Entity(models.Model):
	full_name = models.CharField(max_length=250)
	first_name = models.CharField(max_length=150)
	middle_name = models.CharField(max_length=150)
	last_name = models.CharField(max_length=150)
	type = models.CharField(max_length=25) # org or person
	subtype = models.CharField(max_length=50,blank=True,null=True) # firm, professional services, etc.
	summary = models.TextField(blank=True,null=True) # quick 1-2 sentence overview of entity
	description = models.TextField(blank=True,null=True) # more comprehensive overview
	url = models.URLField(blank=True,null=True)
	twitter_handle = models.CharField(blank=True,null=True)
	aliases = models.TextField(blank=True,null=True)
	domain = models.CharField(blank=True,null=True)
	founded_date = models.DateField(blank=True,null=True)
	deadpooled_date = models.DateField(blank=True,null=True)
	created = models.TimeField(auto_now_add=True)
	updated = models.TimeField(auto_now=True)
	cb_permalink = models.CharField(max_length=250,blank=True,null=True)
	cb_url = models.URLField(blank=True,null=True)
	logo = models.URLField(blank=True,null=True)
	total_money = modelsDecimalField(blank=True,null=True)
	relationship = models.ManyToManyField('self',symmetrical=False,through="Relationship") # for advising, employment relationships 
	no_employees = models.IntegerField(blank=True,null=True)
	
	# returns name
	def __unicode__(self):
		return self.name

class Relationship(models.Model):
	entity1 = models.ForeignKey(Entity)
	entity2 = models.ForeignKey(Entity)
	type = models.CharField(max_length=150) # employee, advisor, etc
	current = models.BooleanField() #
	attribution = models.URLField(blank=True,null=True)

class Financing(models.Model):
	investors = models.ManyToManyField(Entity)
	round = models.CharField(max_length=15)
	amount = models.DecimalField(max_length=15)
	currency = models.CharField(max_length=5)
	date = models.DateField(blank=True,null=True)
	source_url = models.URLField(blank=True,null=True)

class Office(models.Model):
	entity = models.ForeignKey(Entity)
	description = models.CharField(blank=True,null=True)
	addr_1 = models.CharField(max_length=150)
	addr_2 = models.CharField(max_length=150,blank=True,null=True)
	addr_3 = models.CharField(max_length=150,blank=True,null=True)
	zip_code = models.IntegerField(max_length=9)
	city = models.CharField(max_length=250)
	state_code = models.CharField(max_length=5)
	country_code = models.CharField(max_length=50)
	latitute = models.DecimalField()
	longitute = models.DecimalField()

class Scan(models.Model):
	entity = models.ForeignKey(Entity) # entity