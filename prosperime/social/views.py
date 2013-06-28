# Python
import datetime
import json
import logging

# Django
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User

# ProsperMe
from careers.models import SavedPath
from social.models import Comment, Thread, Vote, FollowThread
import utilities.helpers as helpers

logger = logging.getLogger(__name__)

def recruiters(request):
	from social.forms import RecruiterInterestForm
	# check to see if email submitted
	if request.POST:
		form = RecruiterInterestForm(request.POST)
		
		
		# validate form
		
		if form.is_valid():
			from django.core.mail.backends.smtp import EmailBackend
			from django.core.mail import EmailMultiAlternatives
			backend = EmailBackend()
			msg = EmailMultiAlternatives("ProsperMe: New recruiter signup","New signup: " + form.cleaned_data['email'],"admin@prospr.me",["admin@prospr.me"])
			try:
				backend.send_messages([msg])
				logger.info("New recruiter added: "+form.cleaned_data['email'])
			except:
				logger.error("Failed to email new recruiter: "+form.cleaned_data['email'])
			return HttpResponseRedirect("/recruiters/thanks/")

	else:
		form = RecruiterInterestForm()

	return render_to_response("recruiters.html",{'form':form},context_instance=RequestContext(request))

def recruiters_thanks(request):

	return render_to_response("recruiters_thanks.html",context_instance=RequestContext(request))

def thread(request, thread_id):
	thread = Thread.objects.get(id=thread_id)
	comments = Comment.objects.filter(thread=thread).order_by("index")


	owner_positions = comments[0].owner.positions.all().order_by('-start_date').exclude(type="education")
	if owner_positions.exists():
		owner_current_position = {"title":owner_positions[0].title, "entity_id":owner_positions[0].id, "entity_logo":owner_positions[0].entity.default_logo()}
	else:
		owner_current_position = None

	if request.user in thread.followers.all():
		is_following = True
	else:
		is_following = False

	total_followers = thread.followers.all().count()
	## TODO: implement way to get "# followers from your network"
	network_followers = total_followers

	data = {
		"thread_id":thread_id,
		"is_following":is_following,
		"total_followers":total_followers,
		"network_followers":network_followers,
		"comments":[{"owner_name":c.owner.profile.first_name, "owner_id":c.owner.id, "owner_pic":c.owner.profile.default_profile_pic(), "goal":c.meta, "body":c.body, "id":c.id, "votes":Vote.objects.filter(owner=c.owner).count(), "created":helpers._formatted_date(c.created), "modified":helpers._formatted_date(c.updated)} for c in comments],
		"owner_current_position":owner_current_position,
	}


	return render_to_response("social/thread.html",data,context_instance=RequestContext(request))


def create_thread(request):

	data = {}
	data["foo"] = "bar"
	return render_to_response("social/createThread.html", data, context_instance=RequestContext(request))



##########################
#####      AJAX      #####
##########################

# Adds request user as a follower of a given thread
def followThread(request):

	try:
		thread = Thread.objects.get(id=request.POST.get("thread_id"))
	except:
		response = {
			"result":"failure",
			"errors":"No thread id or thread not found"
		}
		return HttpResponse(json.dumps(response))

	try:
		follow = FollowThread()
		follow.user = request.user
		follow.thread = thread
		follow.save()

		response = {
			"result":"success",
		}

	except:
		response = {
			"result":"success",
			"errors":"Error writing to DB",
		}

	return HttpResponse(json.dumps(response))

# Deletes FollowThread object between given thread + user
def unfollowThread(request):
	response = {}

	try:
		thread = Thread.objects.get(id=request.POST.get("thread_id"))
	except:
		response = {
			"result":"failure",
			"errors":"No thread id or thread not found"
		}
		return HttpResponse(json.dumps(response))

	try:
		follow = FollowThread.objects.get(thread=thread, user=request.user)
		follow.delete()

		response = {
			"result":"success",
		}

	except:
		response = {
			"result":"failure",
			"errors":"Error writing to DB",
		}


	return HttpResponse(json.dumps(response))


# Updates like total for a give comment of a particular thread
def updateVotes(request):
	response = {}

	try:
		num_votes = request.POST.get("num_votes")
		comment = Comment.objects.get(id=request.POST.get("comment_id"))
	except:
		response = {
			"result":"failure",
			"errors":"Can't find comment or missing data from template"
		}
		return HttpResponse(json.dumps(response))

	## how to do the inc/decr

	response = {
		"result":"success",
	}

	return HttpResponse(json.dumps(response))


# Adds a comment to a given thread
def postComment(request):
	response = {}
	try:
		thread = Thread.objects.get(id=request.POST.get("thread_id"))
		body = request.POST.get("body")
	except:
		response = {
			"result":"failure",
			"errors":"Can't find thread or missing data from template"
		}
		return HttpResponse(json.dumps(response))


	print body

	# id, owner_pic, owner_name, created


	response["result"] = "success"
	response["data"] = {
		"id":1,
		"owner_pic":request.user.profile.default_profile_pic(),
		"owner_name":request.user.profile.first_name,
		"created":helpers._formatted_date(datetime.datetime.now())
	}
	

	return HttpResponse(json.dumps(response))

# Creates a thread given a thread title, user, and comment body
def createThread(request):

	response = {}

	try:
		title = request.POST.get("title")
		body = request.POST.get("body")
	except:
		response["result"] = "failure"
		response["errors"] = "Missing data from template."
		return HttpResponse(json.dumps(response))

	t = Thread()
	t.name = title
	t.save()

	c = Comment()
	c.owner = request.user
	c.thread = t
	c.index = 0
	c.body = body
	c.save()

	response["result"] = "success"
	response["thread_id"] = t.id

	return HttpResponse(json.dumps(response))

def saveComment(request):

	response = {}

	if not request.POST:
		response["result"] = "failure"
		response["errors"] = "Incorrect request type"
		return HttpResponse(json.dumps(response))

	body = request.POST.get("body")
	path_id = request.POST.get("path_id")
	comment_type = request.POST.get("type")

	## Check all params, save comment, 
	##	then send back data needed to update DOM
	if len(body) > 0 and int(path_id) > 0 and len(comment_type) > 0:
		try:
			c = Comment()
			c.owner = request.user
			c.path = SavedPath.objects.get(pk=int(path_id))
			c.type = comment_type
			c.body = body
			c.save()
		except:
			response = {
				"result":"failure",
				"errors":"Error creating comment @ db level"
			}
			return HttpResponse(json.dumps(response))
	else:
		response = {
			"result":"failure",
			"errors":"one or more blank parameters"
		}
		return HttpResponse(json.dumps(response))

	response["user_name"] = request.user.profile.full_name()
	response["profile_pic"] = request.user.profile.default_profile_pic()
	response["date_created"] = helpers._formatted_date(c.created) ## need to format this
	response["result"] = "success"

	return HttpResponse(json.dumps(response))









	