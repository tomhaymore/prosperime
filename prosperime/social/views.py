# Python
import datetime
import json
import logging
import datetime
from urllib import unquote

# Django
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# ProsperMe
from accounts.models import Profile
from careers.models import SavedPath
from social.models import Comment, Conversation, Vote, FollowConversation, Tag
import utilities.helpers as helpers


logger = logging.getLogger(__name__)

# Welcome page, Guru V1
def welcome(request):
	if request.user.is_authenticated():
		# user is logged in, display personalized information
		## TODO - redirect to top aspiration
		return HttpResponseRedirect('/home')

	data = {"pics":['https://prosperme_images.s3.amazonaws.com/pictures/greta_dyer/greta_dyer.jpg?Signature=XzY2q1BH4U7cae1dGA%2FMUaF7uyI%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/michael_elgarico/michael_elgarico.jpg?Signature=sJNR1jQwV%2BYCmAb6UTVPvPvDji0%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/solomon_k._enos/solomon_k._enos.jpg?Signature=veYuWGqzp3bYzLfKykfEHlkZo0w%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/mike_field/mike_field.jpg?Signature=mc0yzXKO0YfIpE%2FoYMhSMxTjuOA%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/marybeth_gasman/marybeth_gasman.jpg?Signature=rqlPgZUGKN0oK3hABr7WPHRd%2FPI%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/jason_davies%2C_md%2C_phd/jason_davies%2C_md%2C_phd.jpg?Signature=sak9T6UwZzKINrwrGPPOatlS6LI%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/adam_gillrie/adam_gillrie.jpg?Signature=xgNkGdwpsaO%2FWQpruTdUiAbhn4k%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/matthew_gillrie/matthew_gillrie.jpg?Signature=pM9zNIDV1oSRHne9GEisYVZ%2FXIs%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/nandita_gupta/nandita_gupta.jpg?Signature=GaTWMpVSwgQ90nYlh7hvIPHd0ao%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/alec_gustafson/alec_gustafson.jpg?Signature=tq%2Fmche3G9l0Sg7DcOJRKugTODA%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/shannon_hawley_mataele/shannon_hawley_mataele.jpg?Signature=FV8j0L%2BvwRgqmf1LZfSvxKmC6KQ%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/luke_dyer/luke_dyer.jpg?Signature=DfMnnIAQ1L%2F%2B9t2XMkIMzH%2BUttU%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/linda_j._hollenback/linda_j._hollenback.jpg?Signature=39SNxxtz5rvpigfvAcpUgRhkdTA%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/stephanie_holson/stephanie_holson.jpg?Signature=cCCnMckh05sXrT06biSIUeU0oD4%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/christopher_esplin/christopher_esplin.jpg?Signature=ByxMOtnqfe2YybaVNH2lSwUrXSE%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/greg_jensen/greg_jensen.jpg?Signature=JIFYqoBCcRrqzP5NuHyQcdMb5oc%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82', 'https://prosperme_images.s3.amazonaws.com/pictures/sarah_jensen_clayton/sarah_jensen_clayton.jpg?Signature=gnHogtXW4UF430tRgFeE%2BN8Z%2BOE%3D&Expires=1376443440&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82']}
	# return render_to_response('welcome.html',context_instance=RequestContext(request))
	return render_to_response("welcome_v3.html",data, context_instance=RequestContext(request))


# Main view for a single Aspiration, Guru V1
@login_required
def single_aspiration(request, aspiration_slug):

	## Fake "Reason" Data ##
	# need all of these things to customize the form language around different questions, best to do this server side
	questions = [
		{"alias":"why", "body":"What inspired this goal?", "placeholder":"Because I want to change the world", "submit":"That's why"},
		{"alias":"how", "body":"How are you going to accomplish this goal?", "placeholder":"By rising above", "submit":"That's how"},
		{"alias":"why-not", "body":"Why aren't you pursuing this goal now?", "placeholder":"I am","submit":"Boom"},
		{"alias":"obstacle", "body":"What is the biggest obstacle in your way?", "placeholder":"I have to finish my degree first", "submit":"But then..."}
	]
	## Fake "Aspiration" Data ## 
	aspiration = {
		"name":"I want to run for the U.S. Senate",
		"id":7,
		"slug":str(helpers.slugify("I want to run for the U.S. Senate"))
	}
	## Fake "Guru" Data ##
		# NOTE: data should be sorted by '-num_votes'
	gurus = [
		{"name":"Tom Sawyer" ,"count":7,"id":1},
		{"name":"Ernest Hemingway" ,"count":3,"id":2},
		{"name":"Corey Booker" ,"count":2,"id":3},
		{"name":"George \"Dubya\" Bush","count":1,"id":4},
		{"name":"Mihaly Csikszentmihalyi" ,"count":1,"id":5},
	]

	## Random "Users who share this Aspiration" Data ##
	profile_objs = Profile.objects.filter(id__in=[137237, 136725, 136265, 136931, 136259, 136260, 136129, 136459, 136460, 136261]) # random id_s
	import random
	members = [{
			"pic":p.default_profile_pic(),
			"name":p.full_name(),
			"first_position":p.current_position(),
			"num_aspirations":random.randint(0,10),
			"entities":p.entities(),
			"id":p.id,
			}
		 for p in profile_objs]

	fake_reasons = [
		"Because changing the world is so noble and, like, awesome!",
		"I have a dream, and that is to be the first Asian president. Using the rhetoric of MLK, of course.",
		"HOPE.",
		"I was inspired to pursue a future in U.S. Government after I saw the injustice that inflicted upon my people in the wake of Hurricane Katrina. Beauracracy and torpor led to the needless deaths of thousands of my fellow city-dwellers, and it was then that I pledged my life to ensure that such a tragedy never happens again.",
		"Senators get tons of girls."
	]
	reasons = []
	count = 0
	# get top 'N' reasons related to current question
	for p in profile_objs[:5]:
		reasons.append({"pic":p.default_profile_pic(), "id":p.id, "reason":fake_reasons[count]})
		count += 1



	data = {
		"aspiration":aspiration,
		"question":questions[0],
		"members":members,
		"gurus":gurus,
		"reasons":reasons,
		"user_pic":request.user.profile.default_profile_pic()
	}

	return render_to_response("social/aspiration.html", data, context_instance=RequestContext(request))


## 8/15, Guru V1, not in use ## 
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

## 8/15, Guru V1, not currently in use (From QA Branch) ##
## Also, untested ##
@login_required
def search(request):
	popular_tags = Tag.objects.order_by("-count")[:10]
	data = {"popular_tags": popular_tags}
	return render_to_response("social/search.html", data, context_instance=RequestContext(request))


## 8/15, Guru V1, not currently in use (From QA Branch) ##
@login_required
def tags(request,tag_name):
	# get popular tags
	popular_tags = Tag.objects.order_by("-count")[:10]	
	# get tag
	tag = Tag.objects.get(url_name=tag_name)
	questions = Conversation.objects.filter(tags=tag)

	data = {
		"tag": tag,
		"questions": questions,
		"popular_tags": popular_tags
	}

	return render_to_response("social/tags.html", data, context_instance=RequestContext(request))

## 8/15, Guru V1, not currently in use (From QA Branch) ##
@login_required
def ask(request):
	data = {"tags": Tag.objects.all().values("name", "id")} # needed for autocomplete in Form
	return render_to_response("social/ask.html", data, context_instance=RequestContext(request))

## 8/15, Guru V1, not currently in use (From QA Branch) ##
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
 		"user_id":conversation.owner.id,
 		"tags":conversation.tags.all(),
 		"user_id":conversation.owner.id,
 		"id":conversation.id
 	}

 	# (2) Get comments
 	comments = Comment.objects.filter(conversation=conversation).select_related("owner")
 	formatted_comments = [{"user_name":c.owner.profile.full_name(), "user_id":c.owner.id, "user_pic":c.owner.profile.default_profile_pic(),"body":c.body,"id":c.id,"votes":Vote.objects.filter(comment=c).count(),"created":c.created} for c in comments]
 	
 	# (3) Get followers
 	## TODO: optimize this query
 	followers = [{"id":u.id, "pic":u.profile.default_profile_pic(), "name":u.profile.full_name()} for u in conversation.followers.all()]

 	# (4) Get popular tags
 	popular_tags = Tag.objects.order_by("-count")[:10]

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
 	# dummy data
 	advisors = [
	 	{'id':1,'alumni':'true','school':'Stanford University','school_id':1234,'name':'Alexander Hamilton','position':'Product Manager at Google','pic':'/media/pictures/anon.jpg','educations':[{'degree':'PhD'}],'methods':'all'},
	 	{'id':1,'alumni':'false','school':None,'school_id':None,'name':'Alexander Hamilton','position':'Product Manager at Google','pic':'/media/pictures/anon.jpg','educations':[{'degree':'PhD'}],'methods':'em'},
	 	{'id':1,'alumni':'true','school':'Stanford University','school_id':1234,'name':'Alexander Hamilton','position':'Product Manager at Google','pic':'/media/pictures/anon.jpg','educations':[{'degree':'PhD'}],'methods':'li+fb'},
	 	{'id':1,'alumni':'false','school':None,'school_id':None,'name':'Alexander Hamilton','position':'Product Manager at Google','pic':'/media/pictures/anon.jpg','educations':[{'degree':'PhD'}],'methods':'li'},
	 	{'id':1,'alumni':'true','school':'Stanford University','school_id':1234,'name':'Alexander Hamilton','position':'Product Manager at Google','pic':'/media/pictures/anon.jpg','educations':[{'degree':'PhD'}],'methods':'fb'}
	 ]

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
		"advisors":advisors
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


def partners(request):
	return render_to_response("partners.html",context_instance=RequestContext(request))


###############
##    API    ##
###############
def api_conversation_search(request):
	# get filters from url
	params = request.GET.get('query',None)
	# check to see that there are params
	print params
	if params:
		convos = Conversation.objects.filter(name__icontains=unquote(params)).order_by("-created")[:10]
	else:
		convos = Conversation.objects.order_by("-created")[:10]
				
	print convos

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
			'name':t.name,
			'url_name':t.url_name
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

def api_aspiration_autocomplete(request):

	params = request.GET.get("query") # ?query= ... using a different autocomplete library

	# TODO: implement this API
	# sample: {value:"I want to rule the world", data: 7 } <-- id
	suggestions = [
		{"value":"King of the world", "data": 7},
		{"value":"a lawyer", "data": 8},
		{"value":"a professional soccer player", "data": 9},
		{"value":"World's Strongest Man", "data": 10}
	]

	## response must follow this weird format
	response = {
		"query":params,
		"suggestions":suggestions
	}

	return HttpResponse(json.dumps(response))

def api_vote(request):
	response = {}

	vote_type = request.GET.get("type")
	aspiration_id = request.GET.get("aspiration_id")
	guru_id = request.GET.get("guru_id")

	# TODO: proper error checking


	# TODO: implement
	response["result"] = "success"
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
	print request.POST.getlist("tags[]")
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
		print form.cleaned_data["tags"]
		for t in form.cleaned_data['tags']:
			c.tags.add(t)
		c.save()
		# add flags
		response["result"] = "success"
		response["conversation_id"] = c.id

		# user follows his own Conversation
		f = FollowConversation()
		f.user = request.user
		f.conversation = c
		f.save()

		return HttpResponse(json.dumps(response))
	else:
		# dump form errors	
		response['errors'] = form.errors
		response['result'] = 'failure'
		return HttpResponse(json.dumps(response))	

def api_ask_advisor(request):
	response = {}
	from social.forms import AskAdvisorForm
	from social.models import AdvisorRequest
	from social.tasks import send_advisor_request
	if request.POST:
		# load form
		form = AskAdvisorForm(request.POST)
		# validate form

		if form.is_valid():
			# create new request
			r = AdvisorRequest()
			r.user = request.user
			r.advisor = form.cleaned_data['advisor']
			r.subject = form.cleaned_data['subject']
			r.body = form.cleaned_data['body']
			r.question = form.cleaned_data['question']
			r.method = form.cleaned_data['method']
			r.save()
			# fire off connection
			task_id = send_advisor_request.delay(r)
			# register response

			response['result'] = 'success'
		else:
			response['errors'] = form.errors
			response['result'] = 'failure'
	else:
		response['errors'] = 'wrong format'
		response['result'] = 'failure'

	return HttpResponse(json.dumps(response))

def api_add_reason(request):


	response = {}


	return HttpResponse(json.dumps(response))
