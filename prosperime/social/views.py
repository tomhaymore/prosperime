# Python
import datetime
import json

# Django
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User

# ProsperMe
from careers.models import SavedPath
from social.models import Comment, Thread, Vote, FollowThread
import utilities.helpers as helpers


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

	data = {
		"thread_id":thread_id,
		"is_following":is_following,
		"total_followers":total_followers,
		"comments":[{"owner_name":c.owner.profile.first_name, "owner_id":c.owner.id, "owner_pic":c.owner.profile.default_profile_pic(), "goal":c.meta, "body":c.body, "id":c.id, "votes":Vote.objects.filter(owner=c.owner).count(), "created":helpers._formatted_date(c.created), "modified":helpers._formatted_date(c.updated)} for c in comments],
		"owner_current_position":owner_current_position,
	}


	return render_to_response("social/thread.html",data,context_instance=RequestContext(request))


    # url(r'^social/followThread/$', 'social.views.followThread'),
    # url(r'^social/updateLikes/$', 'social.views.updateLikes'),
    # url(r'^social/postComment/$', 'social.views.postComment'),





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









	