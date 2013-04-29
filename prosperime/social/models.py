## from Python

## from Django
from django.db import models
from django.contrib.auth.models import User

## from Prosperme
from careers.models import SavedPath, GoalPosition, Position

class Notification(models.Model):
	target = models.ForeignKey(User,related_name='notifications')
	sender = models.CharField(max_length=450,null=True)
	type = models.CharField(max_length=150)
	body = models.TextField(null=True)
	status = models.CharField(max_length=15,default="active")
	created = models.DateTimeField(auto_now_add=True, null=True)
	updated = models.DateTimeField(auto_now=True, null=True)

class Comment(models.Model):
	owner = models.ForeignKey(User,related_name="comments")
	path = models.ForeignKey(SavedPath,related_name="comments",null=True)
	position = models.ForeignKey(Position,related_name="comments",null=True)
	goal_position = models.ForeignKey(GoalPosition,related_name="comments",null=True)
	meta = models.CharField(max_length=150,null=True)
	index = models.IntegerField(null=True)
	type = models.CharField(max_length=150,null=True)
	body = models.TextField(null=True)
	status = models.CharField(max_length=15,default="active")
	created = models.DateTimeField(auto_now_add=True, null=True)
	updated = models.DateTimeField(auto_now=True, null=True)

	def target_user(self):
		if self.type == "path":
			return self.path.owner
		elif self.type == "position":
			return self.position.person
		elif self.type == "goalposition":
			return self.goal_position.owner

	def target_name(self):
		if self.type == "path":
			return self.path.title
		elif self.type == "position":
			return self.position.title
		elif self.type == "goalposition":
			return self.goal_position.position.title

	def target_id(self):
		if self.type == "path":
			return self.path.id
		elif self.type == "position":
			return self.position.id
		elif self.type == "goalposition":
			return self.goal_position.id