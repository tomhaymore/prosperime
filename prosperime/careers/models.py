# Python
import datetime
import json

# Python
import datetime
	
# Django
from django.db import models
from django.contrib.auth.models import User

# Prosperime
from entities.models import Industry, Entity


class Position(models.Model):
	entity = models.ForeignKey(Entity,related_name="positions")
	person = models.ForeignKey(User,related_name="positions")
	careers = models.ManyToManyField("Career",related_name="positions")
	ideal_position = models.ForeignKey("IdealPosition",related_name="position",null=True)
	title = models.CharField(max_length=150,null=True)
	summary = models.CharField(max_length=450,null=True)
	description = models.TextField(null=True)
	current = models.BooleanField(default=True)
	start_date = models.DateField(null=True)
	end_date = models.DateField(null=True)
	type = models.CharField(max_length=450,null=True)
	degree = models.CharField(max_length=450,null=True)
	field = models.CharField(max_length=450,null=True)
	status = models.CharField(max_length=15,default="active")
	created = models.DateTimeField(auto_now_add=True, null=True)
	updated = models.DateTimeField(auto_now=True, null=True)

	def __unicode__(self):
		if self.title is not None:
			return self.title + " at " + self.entity.name
		elif self.summary is not None:
			return self.summary + " at " + self.entity.name
		else:
			return "unnamed position at " + self.entity.name

	def safe_title(self):
		if self.title is not None:
			return self.title
		elif self.summary is not None:
			return self.summary
		else:
			return "unnamed position"

	def duration(self):
		if self.start_date is not None and self.end_date is not None:
			return self.start_date.year - self.end_date.year
		else:
			return None

	def duration_in_months(self):
		if self.start_date is not None and self.end_date is not None:
			return (12 * (self.end_date.year - self.start_date.year)) + (self.end_date.month - self.start_date.month)
		elif self.start_date is not None:
			now = datetime.datetime.now()
			return (12 * (now.year - self.start_date.year)) + (now.month - self.start_date.month)
		else:
			return None

	def safe_start_time(self):
		if self.start_date is not None:
			return self.start_date.strftime("%b %Y")
		return None

	def safe_end_time(self):
		if self.end_date is not None:
			return self.end_date.strftime("%b %Y")
		return None

	def industries(self):
		return self.entity.domains.all()

class Career(models.Model):	
	short_name = models.CharField(max_length=450,null=True)
	long_name = models.CharField(max_length=450,null=True)
	description = models.TextField(null=True)
	parent = models.ForeignKey('self',related_name="children",null=True)
	census_code = models.CharField(max_length=10,null=True)
	soc_code = models.CharField(max_length=15,null=True)
	industry_code = models.CharField(max_length=15,null=True)
	industry = models.ManyToManyField(Industry)
	pos_titles = models.TextField(null=True)
	saved_people = models.ManyToManyField(User,related_name="saved_careers",through="SavedCareer")
	status = models.CharField(max_length=15,default="active")
	created = models.DateTimeField(auto_now_add=True, null=True)
	updated = models.DateTimeField(auto_now=True, null=True)

	def __unicode__(self):
		return self.long_name

	def get_pos_titles(self):
		"""
		returns list of positions titles associated with a career
		"""
		if self.pos_titles:
			return json.loads(self.pos_titles)
		return None

	def add_pos_title(self,t):
		"""
		takes position title and adds it to list of corresponding positions if not already present
		"""
		if self.pos_titles is not None:
			titles = json.loads(self.pos_titles)
			
			if t not in titles:
				titles.append(t.decode("utf8","ignore"))
		else:
			titles = [t.decode("utf8","ignore")]
		# print titles
		self.pos_titles = json.dumps(titles)
		self.save()

	def add_pos_title_list(self,t):
		"""
		takes list of position titles and adds to model
		"""
		if self.pos_titles is not None:
			titles = json.loads(self.pos_titles)
			for title in t:
				titles.append(t)
		else:
			titles = t
		self.pos_titles = json.dumps(titles)
		self.save()

	def siblings(self):
		"""
		return sibling careers, i.e., those with the same parent
		"""
		children = self.parent.children
		children.remove(self)
		return children

	def _name(self):
		"""
		returns short name or long name if no short name
		"""
		if self.short_name:
			return self.short_name
		return self.long_name

	def avg_duration_network(self,user):
		"""
		returns average length of time in career for users in focal user's network
		"""
		import careers.careerlib as careerlib
		return careerlib.avg_duration_network(self,user)

	def avg_duration_all(self):
		"""
		returns average length of time in career for all users
		"""
		import careers.careerlib as careerlib
		return careerlib.avg_duration_all(self)

	name = property(_name)


class SavedCareer(models.Model):

	career = models.ForeignKey(Career)
	owner = models.ForeignKey(User)
	title = models.CharField(max_length=150,null=True)
	status = models.CharField(max_length=15,default="active")
	created = models.DateTimeField(auto_now_add=True, null=True)
	updated = models.DateTimeField(auto_now=True, null=True)

class SavedIndustry(models.Model):

	industry = models.ForeignKey(Industry)
	owner = models.ForeignKey(User)
	title = models.CharField(max_length=150,null=True)
	status = models.CharField(max_length=15,default="active")
	created = models.DateTimeField(auto_now_add=True, null=True)
	updated = models.DateTimeField(auto_now=True, null=True)	

class IdealPosition(models.Model):

	title = models.CharField(max_length=450, null=True)
	description = models.TextField(null=True)
	level = models.IntegerField(null=True)
	careers = models.ManyToManyField(Career,related_name="ideal_positions")
	people = models.ManyToManyField(User,through='GoalPosition')
	matches = models.TextField(null=True)
	status = models.CharField(max_length=15,default="active")
	created = models.DateTimeField(auto_now_add=True, null=True)
	updated = models.DateTimeField(auto_now=True, null=True)

	def __unicode__(self):
		return self.title

	def add_pos_match(self,match):
		"""
		adds title and industry information for matching positions to an ideal position
		"""
		# check to see if there are any matches
		if self.matches is not None:
			# load list and append new match
			matches = json.loads(self.matches)
			matches['title'] = matches['title'].lower()
			matches.append(match)
		else:
			# create new list with match as first entry
			matches = [match]
		
		# save model
		self.matches = json.dumps(matches)
		self.save()

	def get_matches_as_dict(self):
		"""
		returns matches as Python dict
		"""
		return json.loads(self.matches)

class GoalPosition(models.Model):

	position = models.ForeignKey(IdealPosition)
	owner = models.ForeignKey(User, related_name="goal_position")
	status = models.CharField(max_length=15,default="active")
	created = models.DateTimeField(auto_now_add=True, null=True)
	updated = models.DateTimeField(auto_now=True, null=True)

class SavedPath(models.Model):

	title = models.CharField(max_length=50, null=True)
	date_created = models.DateTimeField(auto_now_add=True,null=True)
	date_modified = models.DateTimeField(auto_now=True,null=True)
	owner = models.ForeignKey(User,related_name='savedPath')
	positions = models.ManyToManyField(Position, through='SavedPosition')
	last_index = models.CharField(max_length = 10, null=True)

	def path_simple(self):
		return [{'id':p.id,'title':p.title} for p in self.positions.all()]

	def get_next_index(self):
		return_val = int(self.last_index)
		self.last_index = str(return_val + 1)
		self.save()
		return return_val

	def __unicode__(self):
		if self.date_created:
			return "Saved Path. " + str(self.date_created)
		else:
			return "Saved Path."

class SavedPosition(models.Model):

	class Meta:
		ordering = ['-index']

	position = models.ForeignKey(Position, related_name='savedPosition')
	path = models.ForeignKey(SavedPath)
	index = models.CharField(max_length = 10, null=True)


class CareerDecision(models.Model):

	# # Current Types:
	# firstJob, college, internship, careerJuncture, 

	owner = models.ForeignKey(User, related_name='careerDecision')
	type = models.CharField(max_length=100, null=True)
	date_created = models.DateTimeField(auto_now_add=True, null=True)
	date_modified = models.DateTimeField(auto_now=True, null=True)
	privacy = models.CharField(max_length=25, default="public")
	position = models.ForeignKey(Position, related_name='careerDecision')
	winner = models.ForeignKey(Entity, related_name='winner')
	alternates = models.ManyToManyField(Entity, related_name='competitors')
	reason = models.TextField(null=True, blank=True)
	comments = models.TextField(null=True, blank=True)
	mentorship = models.PositiveSmallIntegerField(null=True, blank=True)
	social = models.PositiveSmallIntegerField(null=True, blank=True)
	skills = models.PositiveSmallIntegerField(null=True, blank=True)
	overall = models.PositiveSmallIntegerField(null=True, blank=True)

	def __unicode__(self):
		if self.winner is not None:
			return self.type + ': ' + self.winner.name
		else:
			return self.type








	
