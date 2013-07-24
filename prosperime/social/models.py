## from Python

## from Django
from django.db import models
from django.contrib.auth.models import User

## from Prosperme
from careers.models import SavedPath, GoalPosition, Position, IdealPosition

class Notification(models.Model):
	target = models.ForeignKey(User,related_name='notifications')
	sender = models.CharField(max_length=450,null=True)
	type = models.CharField(max_length=150)
	body = models.TextField(null=True)
	status = models.CharField(max_length=15,default="active")
	created = models.DateTimeField(auto_now_add=True, null=True)
	updated = models.DateTimeField(auto_now=True, null=True)

	def __unicode__(self):
		return self.type + " for " + self.target.username

class Conversation(models.Model):
	name = models.CharField(max_length=450,null=True)
	summary = models.TextField(null=True)
	followers = models.ManyToManyField(User,related_name="followers",through="FollowConversation")
	owner = models.ForeignKey(User,related_name="conversations")
	tags = models.ManyToManyField("Tag",related_name="tags")
	satus = models.CharField(max_length=45,default="inactive")
	created = models.DateTimeField(auto_now_add=True, null=True)
	updated = models.DateTimeField(auto_now=True, null=True)

	def __unicode__(self):
		return self.name

class Comment(models.Model):
	owner = models.ForeignKey(User,related_name="comments")
	conversation = models.ForeignKey(Conversation,related_name="comments")
	meta = models.CharField(max_length=150,null=True)
	index = models.IntegerField(null=True)
	body = models.TextField(null=True)
	status = models.CharField(max_length=15,default="active")
	created = models.DateTimeField(auto_now_add=True, null=True)
	updated = models.DateTimeField(auto_now=True, null=True)

	def __unicode__(self):
		return "Comment #" + str(self.index) + " on " + self.thread.name

class FollowConversation(models.Model):
	conversation = models.ForeignKey(Conversation)
	user = models.ForeignKey(User)
	status = models.CharField(max_length=45,default="active")
	created = models.DateTimeField(auto_now_add=True, null=True)
	updated = models.DateTimeField(auto_now=True, null=True)

class Vote(models.Model):
	owner = models.ForeignKey(User,related_name="votes")
	comment = models.ForeignKey(Comment,related_name="votes",null=True)
	conversation = models.ForeignKey(Conversation,related_name="votes",null=True)
	value = models.IntegerField(default=1)
	type = models.CharField(max_length=50,null=True)
	created = models.DateTimeField(auto_now_add=True, null=True)
	updated = models.DateTimeField(auto_now=True, null=True)

	def __unicode__(self):
		if self.value == 1:
			return "Up vote by " + self.owner.username + " on " + self.comment
		else:
			return "Down vote by " + self.owner.username + " on " + self.comment

class Tag(models.Model):
	name = models.CharField(max_length=450)

	def tag_count(self):
		return len(Conversation.objects.filter(tags=self))

	def __unicode__(self):
		return self.name
