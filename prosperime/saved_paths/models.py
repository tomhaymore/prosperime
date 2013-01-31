# Python
import datetime

# Django
from django.db import models
from django.contrib.auth.models import User

# Entities
from entities.models import Position

class Saved_Path(models.Model):

	title = models.CharField(max_length=50, null=True)
	date_created = models.DateTimeField(auto_now_add=True,null=True)
	date_modified = models.DateTimeField(auto_now=True,null=True)
	owner = models.ForeignKey(User, related_name='saved_path')
	positions = models.ManyToManyField(Position)

	# This bugs and dies and I don't know why
	# def __unicode__(self):
	# 	if date_created:
	# 		return "Saved Path. " + str(date_created)
	# 	else:
	# 		return "Saved Path."