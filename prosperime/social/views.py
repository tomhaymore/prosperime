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
from social.models import Comment, Conversation, Vote, FollowConversation
import utilities.helpers as helpers

logger = logging.getLogger(__name__)

def welcome(request):
	if request.user.is_authenticated():
		# user is logged in, display personalized information
		return HttpResponseRedirect('/home')
	return render_to_response('welcome.html',context_instance=RequestContext(request))

def home(request):

	# check if user is logged in
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/welcome')

	tags = [
		{"title":"Great Hours", "id":7, "type":"Good"},
		{"title":"What Perks", "id":7, "type":"Bad"},
		{"title":"Crazy Hours", "id":7, "type":"Bad"},
		{"title":"Strict Culture", "id":7, "type":"Eh"},
		{"title":"Great Pay", "id":7, "type":"Good"},
		{"title":"Great Cause", "id":7, "type":"Good"},
		{"title":"Just a Paycheck", "id":7, "type":"Bad"},
	]

	filters = [
		{"title":"Symbolic Systems", "id":7, "value":"major-7"},
		{"title":"Mechanical Engineering", "id":7, "value":"major-7"},
		{"title":"Banking", "id":7, "value":"major-7"},
		{"title":"First Job", "id":7, "value":"major-7"},
		{"title":"Internship", "id":7, "value":"major-7"},
	]

	data = {
		"most_recent":None, # [ {"user_pic", "title", "body", "tags[]", "comments[]", }]
		"popular_tags":tags, # [ {"title", "type", "id"} ]
		"filters":filters,
	}


	return render_to_response("social/home.html", data, context_instance=RequestContext(request))


# @login_required
def ask(request):

	tags = [
		{"title":"Great Hours", "id":7, "type":"Good"},
		{"title":"What Perks", "id":7, "type":"Bad"},
		{"title":"Crazy Hours", "id":7, "type":"Bad"},
		{"title":"Strict Culture", "id":7, "type":"Eh"},
		{"title":"Great Pay", "id":7, "type":"Good"},
		{"title":"Great Cause", "id":7, "type":"Good"},
		{"title":"Just a Paycheck", "id":7, "type":"Bad"},
	]

	data = {
		"tags": tags,  # {"title", "type", "id"}
	}

	return render_to_response("social/ask.html", data, context_instance=RequestContext(request))

# Force login to view questions?
def question(request, question_id):


	popular_tags = [
		{"title":"Great Hours", "id":7, "type":"Good"},
		{"title":"What Perks", "id":7, "type":"Bad"},
		{"title":"Crazy Hours", "id":7, "type":"Bad"},
		{"title":"Strict Culture", "id":7, "type":"Eh"},
		{"title":"Great Pay", "id":7, "type":"Good"},
		{"title":"Great Cause", "id":7, "type":"Good"},
		{"title":"Just a Paycheck", "id":7, "type":"Bad"},
	]


	body1 = "Not the greatest experience, to be brutally honest. While no one can argue that passion at the company runs high, it just isn't a particularly well-run organization. Our particular division was beset by managerial issues and relationship tensions. All this stemmed from poor or weak top-down leadership."
	body2 = "An amazing experience!! Karen is the absolute best, pray that you work for her."
	body3 = "Use the sleeves of my sweater, let's have an adventure. The things that I think about, one heart, one mouth, one love, two mouths, one house, two blouses. Just us, you find out, and it's becoming increasingly difficult to make this look like a really long post. Oh what's this under my bed? Looks like chapstick. I'll use that."
	body4 = "Emma Way has been summonsed to court to answer driving charges A 21-year-old woman who tweeted she had knocked a cyclist off his bike after an alleged crash in Norfolk has been summonsed to appear in court. Emma Way is to answer charges of driving without due care and attention and failing to stop after an accident."
	body5 = "Use the sleeves of my sweater, let's have an adventure. The things that I think about, one heart, one mouth, one love, two mouths, one house, two blouses. Just us, you find out, and it's becoming increasingly difficult to make this look like a really long post. Oh what's this under my bed? Looks like chapstick. I'll use that."

	reviews = [
		{"pic":"/media/pictures/anon.jpg", "position":"Product Manager", "entity":"Genentech", "position_id":4, "entity_id":7, "id":11, "tags":[{"title":"Great Pay", "type":"Good", "id":12}, {"title":"Long Hours", "type":"Bad", "id":14}], "rating":4.5, "body":body1},
		{"pic":"/media/pictures/anon.jpg", "position":"Product Manager", "entity":"Genentech", "position_id":4, "entity_id":7, "id":11, "tags":[{"title":"Great Pay", "type":"Good", "id":12}, {"title":"Long Hours", "type":"Bad", "id":14}], "rating":2.0, "body":body2},
		{"pic":"/media/pictures/anon.jpg", "position":"Product Manager", "entity":"Genentech", "position_id":4, "entity_id":7, "id":11, "tags":[{"title":"Great Pay", "type":"Good", "id":12}, {"title":"Long Hours", "type":"Bad", "id":14}], "rating":5.0, "body":body3},
		{"pic":"/media/pictures/anon.jpg", "position":"Product Manager", "entity":"Genentech", "position_id":4, "entity_id":7, "id":11, "tags":[{"title":"Great Pay", "type":"Good", "id":12}, {"title":"Long Hours", "type":"Bad", "id":14}], "rating":3.5, "body":body4},
		{"pic":"/media/pictures/anon.jpg", "position":"Product Manager", "entity":"Genentech", "position_id":4, "entity_id":7, "id":11, "tags":[{"title":"Great Pay", "type":"Good", "id":12}, {"title":"Long Hours", "type":"Bad", "id":14}], "rating":3.0, "body":body5},
	]

	pics = ['https://prosperme_images.s3.amazonaws.com/pictures/vincent_cannon/vincent_cannon.jpg?Signature=7xxvfw%2Fm5w69ZWGHfNWztfpBFy4%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/patrick_carroll/patrick_carroll.jpg?Signature=0lzUGun%2BwW9Cx9to8V4X%2BVD%2FaVQ%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/melissa_arano/melissa_arano.jpg?Signature=eVa%2BcBanvN4hOLNLxZjhZrUBfck%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/amanda_berry/amanda_berry.jpg?Signature=UTojQ6FgK5WV09rZKf42M4LH7G4%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/annie_bezbatchenko/annie_bezbatchenko.jpg?Signature=ids6gN%2FO56RQkx23wyNvn2CZqho%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/tahira_%28taida%29_adaya/tahira_%28taida%29_adaya.jpg?Signature=VWfZ4rbUE0ERGi6VEQlpH0o9vN8%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/tara_adiseshan/tara_adiseshan.jpg?Signature=YcOlphSeufZZgSG7qAAw4At5jzE%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/william_clayton/william_clayton.jpg?Signature=y6wz0jGjo1dPwpgI3Pw5AH4yNrc%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/chike_amajoyi/chike_amajoyi.jpg?Signature=4uRwh%2Ftkll%2FtbOnbvlxUyJuZKns%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/emily_cox/emily_cox.jpg?Signature=ngLuwgSoGVuB7yVNpQCfi%2BU3CoE%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/carly_crandall/carly_crandall.jpg?Signature=xwNGhCmuDvJOHbgVkSqQE4h%2F8OI%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 '/media/pictures/anon.jpg',
 'https://prosperme_images.s3.amazonaws.com/pictures/yosem_companys/yosem_companys.jpg?Signature=PnJSInv8fXiCN4PNpOrMriHtQdI%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/christopher_condlin/christopher_condlin.jpg?Signature=OWZjiYaV9MtqB97PZj1Jd6SYBIk%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/stan_darger%2C_jr./stan_darger%2C_jr..jpg?Signature=5EsqyCdi7YM%2FzlrMK2ld5IbpFPs%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/heather_davidson/heather_davidson.jpg?Signature=5il3pSbUTPDnwWsq4cCFgvunVLI%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/jason_davies%2C_md%2C_phd/jason_davies%2C_md%2C_phd.jpg?Signature=246d%2BPgWxTdnQh4QY5AnqddPrgs%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/miles_davis/miles_davis.jpg?Signature=6h4i1%2BFzsDZ6ABHU1MlkJqpiFek%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/logan_deans/logan_deans.jpg?Signature=Co4yeSkjbEYwVEG62Mr0hClskpg%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/aidan_dunn/aidan_dunn.jpg?Signature=V3zww4EXagVcuh90tSov32RYwQk%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/marie_dutton/marie_dutton.jpg?Signature=TDW7qb7xld0f6ssKr11QC6bHFMk%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/greta_dyer/greta_dyer.jpg?Signature=fv%2Bzp%2Fl2u7%2BBs7x%2BK%2BjBdVa6ovo%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/michael_elgarico/michael_elgarico.jpg?Signature=w0wFtS%2Fp%2FbIMuFFE0FBBAkNM%2B08%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/solomon_k._enos/solomon_k._enos.jpg?Signature=NqRLRBFts0zM0%2Ffo9L7oF%2FveYnY%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/mike_field/mike_field.jpg?Signature=x1gjOjP5%2B3Ti9K48Q%2BVntCnDfrs%3D&Expires=1374270810&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82']

 	followers = [{"id":7, "pic":p, "name":"Christina Phillips"} for p in pics]
 	related_questions = [
 		{"title":"What can I do with my Math degree?", "id":7},
 		{"title":"What is the biggest professional mistake you've ever made?", "id":7},
 		{"title":"Are there any options out there for STS majors?", "id":7},
 		{"title":"What is like to work in Management Consulting from Stanford?", "id":7},
 		{"title":"What are the most important classes that you ever took? Why?", "id":7},
 	]

 	question = {
 		"title":"What can I do with my English degree?",
 		"body":"I don't want to go into editing or publishing or journalism... maybe tech? I just want to know what my options are. The only thing that I think I may be interested is the music industry, but I'm open to all new experiences. Are there any fellow alums out there who could shine some light on this? Thanks!",
 		"user_pic":pics[-1:][0],
 		"user_name":"Adam Jahn",
 		"tags":popular_tags[:3],
 		"user_id":7,
 	}

 	comments = [
 		{"user_name":"James Buchanan", "user_pic":pics[10], "body":"There are tons of options out there for English majors. These options may include: cutting brush, taking out the trash, walking cats, being a meathead, and/or depression fueled by narcotics and hipster alcohol. Please be advised, that, of these paths, taking out the trash is the most respected and, probably, the most safe.", "votes":"27"},
 		# {"user_name":"James Buchanan", "user_pic":pics[14], "body":" ", "votes":"27"},
 		# {"user_name":"James Buchanan", "user_pic":pics[14], "body":" ", "votes":"27"},
 		# {"user_name":"James Buchanan", "user_pic":pics[14], "body":" ", "votes":"27"},

 	]



	data = {
		"is_active":True, # boolean
		"is_following":False, # boolean
		"question":question, # {"title", "body", "user_pic", "user_name", "tags = []"}
		"stats":{"num_followers":17, "num_answers":12, "days_active":4}, # {"num_followers", "num_answers", "num_days_active"}
		"comments":comments, # [ {"body", "user_name", "user_pic", "votes"} ]
		"user_pic":request.user.profile.default_profile_pic(), # = profile_pic of the viewer
		"related_questions":related_questions,
		"followers":followers,
		"popular_tags":popular_tags, # [ {"title", "type", "id"} ]
		"url":request.build_absolute_uri(),
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

## API ##

def api_conversation_search(request):
	# get filters from url
	params = request.GET.get('query',None)
	# check to see that there are params
	if params:
		convos = Conversation.objects.filter(name__icontains=params).order_by("-created")[:10]
	else:
		convos = Conversation.objects.order_by("-created")[:10]
				
	convos_list = [{'id':c.id,'name':c.name,'summary':c.summary,'owner_id':c.owner.id,'owner_name':c.owner.profile.full_name(),'owner_pic':c.owner.profile.default_profile_pic(),'no_comments':len(c.comments.all()),'tags':[{'id':t.id,'name':t.name} for t in c.tags.all()],'comments':[{'id':comment.id,'body':comment.body,'owner_id':comment.owner.id,'owner_name':comment.owner.profile.full_name(),'owner_pic':comment.owner.profile.default_profile_pic()} for comment in c.comments.all()]} for c in convos]

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









	