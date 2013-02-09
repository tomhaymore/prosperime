# Python
import datetime

# Django
from django.db import models
from django.contrib.auth.models import User

# Entities
from entities.models import Position

class SavedPath(models.Model):

	title = models.CharField(max_length=50, null=True)
	date_created = models.DateTimeField(auto_now_add=True,null=True)
	date_modified = models.DateTimeField(auto_now=True,null=True)
	owner = models.ForeignKey(User,related_name='savedpath')
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

	
