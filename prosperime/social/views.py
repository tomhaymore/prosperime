# Python
import datetime
import json
import logging
import datetime

# Django
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


# ProsperMe
from careers.models import SavedPath
from social.models import Comment, Conversation, Vote, FollowConversation, Tag
import utilities.helpers as helpers


logger = logging.getLogger(__name__)

def welcome(request):
	if request.user.is_authenticated():
		# user is logged in, display personalized information
		return HttpResponseRedirect('/home')
	return render_to_response('welcome.html',context_instance=RequestContext(request))

@login_required
def home(request):

	# check if user is logged in
	if not request.user.is_authenticated():
		return render_to_response('welcome.html',context_instance=RequestContext(request))
	# check if user is from a partner school
	# if not school_is_partner(request.user):
	# 	data = {
	# 		"schools": request.user.schools()
	# 	}
	# 	return render_to_response('waiting_for_partnership.html',data=data,context_instance=RequestContext(request))
	
	popular_tags = Tag.objects.order_by("-count")[:10]

	data = {
		"most_recent": None, # [ {"user_pic", "title", "body", "tags[]", "comments[]", }]
		"popular_tags": popular_tags
	}


	return render_to_response("social/home.html", data, context_instance=RequestContext(request))


@login_required
def ask(request):

	data = {
		"tags": Tag.objects.all().values("name", "id"), # needed for autocomplete in Form
	}

	return render_to_response("social/ask.html", data, context_instance=RequestContext(request))

# Force login to view questions?
def question(request, conversation_id):

	## IF there's an error getting here, question_id will be -1, so redirect accordingly
	if conversation_id == -1:
		render_to_response("/404.html/", {}, context_instance=RequestContext(request))

	# THEN, check if INACTIVE
	# TODO: add inactive field to Conversation model
	is_active = True 

	# (1) Get Conversation 
	conversation = Conversation.objects.get(id=conversation_id)
 	question = {
 		"title":conversation.name,
 		"body":conversation.summary,
 		"user_pic":conversation.owner.profile.default_profile_pic(),
 		"user_name":conversation.owner.profile.full_name(),
 		"tags":conversation.tags.all(),
 		"user_id":conversation.owner.id
 	}

 	# (2) Get comments
 	comments = Comment.objects.filter(conversation=conversation).select_related("owner")
 	formatted_comments = [{"user_name":c.owner.profile.full_name(),"user_pic":c.owner.profile.default_profile_pic(),"body":c.body,"id":c.id,"votes":Vote.objects.filter(comment=c).count(),"created":c.created} for c in comments]
 	

 	# (3) Get followers
 	## TODO: optimize this query
 	followers = [{"id":u.id, "pic":u.profile.default_profile_pic(), "name":u.profile.full_name()} for u in conversation.followers.all()]

 	# (4) Get popular tags
 	## TODO: popular_tags API
 	popular_tags = Tag.objects.all()[:8].values("name", "id")

 	# (5) Get related questions
 	## TODO: related_questions API
 	related_questions = [{"name":c.name, "id":c.id} for c in Conversation.objects.all().exclude(id=conversation_id)[:5]]
 	
 	# (6) Check if following    (oh what up ternary operator, you thought I'd forgotten about you)
 	is_following = True if (request.user in conversation.followers.all()) else False

 	# (7) Get stats for conversation:
 	num_followers = conversation.followers.count()
 	num_answers = comments.count()
 	delta = datetime.datetime.now() - conversation.created
 	days_active = delta.days + 1
 	stats = {
 		"num_followers": num_followers,
 		"num_answers": num_answers,
 		"days_active": days_active
 	}

	data = {
		"is_active": is_active,                   # boolean
		"is_following":is_following,              # boolean
		"question":question,                      # {"title", "body", "user_pic", "user_name", "tags = []"}
		"stats": stats,                           # {"num_followers", "num_answers", "num_days_active"}
		"comments":formatted_comments,            # [ {"body", "user_name", "user_pic", "votes", "id"} ]
		"user_pic":request.user.profile.default_profile_pic(), # = profile_pic of the viewer
		"related_questions":related_questions,    # [ {"name", "id"} ]
		"followers":followers,                    # [ {"name", "id", "pic"} ]
		"popular_tags":popular_tags,              # [ {"title", "type", "id"} ]
		"url":request.build_absolute_uri(),       # used for sending the link to people... could be done in JS as well
	}


	return render_to_response("social/question.html", data, context_instance=RequestContext(request))


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

###############
##    API    ##
###############
def api_conversation_search(request):
	# get filters from url
	params = request.GET.get('query',None)
	# check to see that there are params
	if params:
		convos = Conversation.objects.filter(name__icontains=params).order_by("-created")[:10]
	else:
		convos = Conversation.objects.order_by("-created")[:10]
				
	convos_list = [{
		'id':c.id,
		'name':c.name,
		'summary':c.summary,
		'owner_id':c.owner.id,
		'owner_name':c.owner.profile.full_name(),
		'owner_pic':c.owner.profile.default_profile_pic(),
		'no_comments':len(c.comments.all()),
		'tags':[{
			'id':t.id,
			'name':t.name
			} for t in c.tags.all()],
		'comments':[{
			'id':comment.id,
			'body':comment.body,
			'owner_id':comment.owner.id,
			'owner_name':comment.owner.profile.full_name(),
			'owner_pic':comment.owner.profile.default_profile_pic()
			} for comment in c.comments.all()]
		} for c in convos]

	response = convos_list
	return HttpResponse(json.dumps(response))

def api_conversation_autocomplete(request):
	# get params from get
	params = request.GET.get('q')
	# check for params
	if params: 
		convos = Conversation.objects.filter(name__icontains=params).order_by("-created")[:10]
		convos_list = [c.name for c in convos]

		response = convos_list
		return HttpResponse(json.dumps(response))



# Adds request user as a follower of a given thread
def api_follow_conversation(request):

	# instatiate vars
	response = {
		"result":None,
		"errors":[]
	}
	conversation_id = -1
	conversation = None

	# error checks
	if not request.is_ajax:
		response["errors"].append("Not AJAX")
	if not request.POST:
		response["errors"].append("Not POST")
	try:
		conversation_id = request.POST.get("conversation_id")
	except:
		response["errors"].append("Can't find params")
	try:
		conversation = Conversation.objects.get(id=conversation_id)
	except:
		response["errors"].append("Conversation not found")
	# check for duplicates
	if FollowConversation.objects.filter(user=request.user, conversation=conversation).count() > 0:
		response["errors"].append("Duplicate protection: Already following this Conversation!")

	# if errors, return early
	if len(response["errors"]) > 0:
		response["result"] = "failure"
		return HttpResponse(json.dumps(response))


	# Create new Object
	try:
		follow = FollowConversation()
		follow.user = request.user
		follow.conversation = conversation
		follow.save()
	except:
		response["errors"].append("Error creating new FollowConversation")

	if len(response["errors"]) > 0:
		response["result"] = "failure"
	else:
		response["result"] = "success"

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

# Adds comment to given conversation
def api_add_comment(request):
	# instantiate vars
	response = {
		"result":None,
		"errors":[]
	}
	conversation = None
	conversation_id = -1
	body = None

	# error checks:
	if not request.is_ajax:
		response["errors"].append("Not AJAX")
	if not request.POST:
		response["errors"].append("Not POST")
	try:
		conversation_id = request.POST.get("conversation_id")
		body = request.POST.get("body")
	except:
		response["errors"].append("Can't find params")
	try:
		conversation = Conversation.objects.get(id=conversation_id)
	except:
		response["errors"].append("Can't find Conversation id: " + str(conversation_id))

	# if errors, respond early
	if len(response["errors"]) > 0:
		response["result"] = "failure"
		return HttpResponse(json.dumps(response))

	# create new Comment
	try:
		c = Comment()
		c.owner = request.user
		c.conversation = conversation
		c.body = body
		c.save()
		print "New comment created"

	except:
		response["errors"].append("Error creating new Comment")

	# Last check for errors
	if len(response["errors"]) > 0:
		response["result"] = "failure"
	else:
		# TODO get delta for time

		response["result"] = "success"
		response["user_name"] = request.user.profile.full_name()
		response["user_pic"] = request.user.profile.default_profile_pic()
		response["user_id"] = request.user.id
		# response["timestamp"] = datetime.datetime.now() - c.created

	return HttpResponse(json.dumps(response))

# Creates upvote or downvote for given comment on given conversation
def api_vote_comment(request):

	# instantiate vars
	response = {
		"result":None,
		"errors":[]
	}
	conversation = None
	conversation_id = -1
	comment = None
	comment_id = -1
	value = 0

	# error checks:
	if not request.is_ajax:
		response["errors"].append("Not AJAX")
	if not request.POST:
		response["errors"].append("Not POST")
	try:
		conversation_id = request.POST.get("conversation_id")
		comment_id = request.POST.get("comment_id")
		value = request.POST.get("value")
	except:
		response["errors"].append("Can't find params")
	try:
		conversation = Conversation.objects.get(id=conversation_id)
		comment = Comment.objects.get(id=comment_id)
	except:
		response["errors"].append("Can't find Conversation id: " + str(conversation_id))

	# if errors, respond early
	if len(response["errors"]) > 0:
		response["result"] = "failure"
		return HttpResponse(json.dumps(response))

	try:
		v = Vote()
		v.owner = request.user
		v.comment = comment
		v.conversation = conversation
		v.value = value
		v.save()

	except:
		response["errors"].append("Error creating Vote object")


	if len(response["errors"]) > 0:
		response["result"] = "failure"
	else:
		response["result"] = "success"

	return HttpResponse(json.dumps(response))


# Starts a new conversation (AJAX)
def api_start_conversation(request):
	from social.forms import ConversationForm
	response = {
		"errors":[],
		"result":None,
	}

	# check that ajax and post
	if not request.is_ajax or not request.POST:
		response["errors"].append("Something went wrong with our connection, please try again.")
		return HttpResponse(json.dumps(response))

	# load form
	form = ConversationForm(request.POST)
	# validate form
	if form.is_valid():
		# create new conversation
		c = Conversation()
		c.name = form.cleaned_data['name']
		c.summary = form.cleaned_data['summary']
		c.owner = request.user
		c.save()
		# add tags
		for t in form.cleaned_data['tags']:
			c.tags.add(t)
		c.save()
		# add flags
		response["result"] = "success"
		response["conversation_id"] = c.id
		return HttpResponse(json.dumps(response))
	else:
		# dump form errors	
		response['errors'] = form.errors
		response['result'] = 'failure'
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










## DEPRECATED: keep around for now for code review
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

## DEPRECATED: keep around for now for code review
def create_thread(request):

	data = {}
	data["foo"] = "bar"
	return render_to_response("social/createThread.html", data, context_instance=RequestContext(request))





	