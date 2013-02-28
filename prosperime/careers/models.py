# Python
import datetime

# Python
import datetime
	
# Django
from django.db import models
from django.contrib.auth.models import User

# Entities
from entities.models import Entity, Industry, Position


class SavedPath(models.Model):

	title = models.CharField(max_length=50, null=True)
	date_created = models.DateTimeField(auto_now_add=True,null=True)
	date_modified = models.DateTimeField(auto_now=True,null=True)
	owner = models.ForeignKey(User,related_name='savedPath')
	positions = models.ManyToManyField(Position, through='SavedPosition')
	last_index = models.CharField(max_length = 10, null=True)

	def get_next_index(self):
		return_val = int(self.last_index)
		self.last_index = str(return_val + 1)
		self.save()
		return return_val

	# This bugs and dies and I don't know why
	# def __unicode__(self):
	# 	if date_created:
	# 		return "Saved Path. " + str(date_created)
	# 	else:
	# 		return "Saved Path."

class SavedPosition(models.Model):

	class Meta:
		ordering = ['-index']

	position = models.ForeignKey(Position)
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








	
