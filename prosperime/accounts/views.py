# from Python
import oauth2 as oauth
import cgi
from datetime import datetime, timedelta
import urlparse
import math
import json
import os
import logging
import random
import time

# from django.contrib.auth.decorators import  _required
from django.contrib.auth import authenticate, logout as auth_logout, login as auth_login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import simplejson
from django.db.models import Count, Q, fields
from django.contrib import messages
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

# Prosperime
from accounts.models import Account, Profile, Picture, Connection
from careers.models import SavedPath, CareerDecision, Position, SavedPosition, SavedCareer, GoalPosition, IdealPosition
from entities.models import Entity, Region
from social.models import Conversation, FollowConversation, Comment

from accounts.tasks import process_li_profile, process_li_connections, send_welcome_email, update_li_profile
from accounts.forms import FinishAuthForm, AuthForm, RegisterForm
import utilities.helpers as helpers
import careers.careerlib as careerlib
from lilib import LIProfile


logger = logging.getLogger(__name__)
critical_logger = logging.getLogger("benchmarks")


@login_required
def profile(request, user_id):
	# get user
	user = User.objects.get(id=user_id)

	# TODO: optimize this query
		# because user follows their own conversations, just filter single QuerySet
	# following & started conversations
	conversations = FollowConversation.objects.filter(user=user).select_related("conversation")
	followed_conversations = [{"name":f.conversation.name, "summary":f.conversation.summary, "id":f.conversation.id, "stats":{"num_followers":f.conversation.followers.count(), "num_answers":f.conversation.comments.count()}} for f in conversations.exclude(conversation__owner=user)]
	started_conversations = [{"name":f.conversation.name, "summary": f.conversation.summary, "id":f.conversation.id, "stats":{"num_followers":f.conversation.followers.count(), "num_answers":f.conversation.comments.count()}} for f in conversations.filter(conversation__owner=user)]

	# connections
	connections = user.profile.connections.all().distinct()
	num_connections = len(connections)
	connections = [{"pic":p.default_profile_pic(), "name":p.full_name(), "id":p.user.id} for p in connections[:4]] # limit to 4 pics for now

	data = {
		"profile_pic":user.profile.default_profile_pic(),
		"own_profile":(user.id == request.user.id),
		"user_name":user.profile.full_name(),
		"positions":json.dumps(_prepare_positions_for_timeline(user.positions.all())),
		"connections":connections, 
		"num_connections":num_connections,
		"followed_conversations":followed_conversations,
		"started_conversations":started_conversations,
	}

	return render_to_response("social/profile.html", data, context_instance=RequestContext(request))

# public-facing page, for marketing to advisors
def faq(request):

	data = {}
	return render_to_response("faq.html",data,context_instance=RequestContext(request))


def login(request):
	# from django.contrib.auth.forms import AuthenticationForm
	# print request.session['_auth_user_backend']
	if request.user.is_authenticated():
		return HttpResponseRedirect('/home/')
	if request.method == "POST":
		# make sure using proper authentication backend
		request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
		
		form = AuthForm(request,request.POST)
		if form.is_valid():
			user = authenticate(username=form.cleaned_data['username'],password=form.cleaned_data['password'])
			if user is not None:
				auth_login(request,user)
				messages.success(request, 'You have successfully logged in.')

				# if last scan > 1 week ago, update profile
				## DEV ##
				# try:
				# 	acct = Account.objects.get(owner=user)
				# 	if acct.last_scanned is None or (datetime.now() - user.last_scanned).days > 7:
				# 		# call task and set task_ids to session
				# 		update_task = update_li_profile.delay(user.id, acct.id)
				# 		request.session['tasks'].update({"update": update_task.id})
				# except:
				# 	logger.error("Couldn't find an Account for user_id: " + str(request.user.id))

			
				return HttpResponseRedirect('/')


		
	else:
		form = AuthForm()

	return render_to_response('accounts/login.html',{'form':form},context_instance=RequestContext(request))

def terms(request):

	return render_to_response('terms.html',context_instance=RequestContext(request))

def privacy(request):

	return render_to_response('privacy.html',context_instance=RequestContext(request))

def copyright(request):

	return render_to_response('copyright.html',context_instance=RequestContext(request))

def use(request):

	return render_to_response('use.html',context_instance=RequestContext(request))

def unsubscribe(request):
	from accounts.forms import EmailUnsubscribeForm
	import accounts.emaillib as emaillib
	if request.POST:

		form = EmailUnsubscribeForm(request.POST)

		if form.is_valid():
			# if user is auth'd, update prferences
			if request.user.is_authenticated():
				try:
					pref = Pref(user=request.user,name="notification")
				except:
					pref = Pref(user=user,name="notification")
				# save new value
				pref.value = 0
				pref.save()
				
			# if anonymous, send email to admins to remove
			else:
				notification = emaillib.NotificationEmail("Add following user to blocklist: " + form.cleaned_data['email'])
				notification.trigger()
			# log flash message
			messages.success(request, 'You have successfully unsubscribed.')
			return HttpResponseRedirect('/unsubscribe')
		else:
			email = request.POST['email']
	else:
		# empty form
		form = EmailUnsubscribeForm(request.POST)
		# check if email specified in URL
		if 'email_address' in request.GET:
			email = request.GET['email_address']
		elif request.user.is_authenticated():
			email = request.user.email
		else:
			email = None
	return render_to_response('accounts/unsubscribe.html',{'form':form,'email':email},context_instance=RequestContext(request))

def register_slim(request):

	if request.user.is_authenticated():
		return HttpResponseRedirect('/majors/')

	return render_to_response('accounts/register_li_only.html',context_instance=RequestContext(request))

def register(request):

	if request.user.is_authenticated():
		return HttpResponseRedirect('/majors/')

	if request.method == "POST":
		form = RegisterForm(request.POST)

		if form.is_valid():
			# grab cleaned values from form
			username = form.cleaned_data['username']
			email = form.cleaned_data['username']
			location = form.cleaned_data['location']
			headline = form.cleaned_data['headline']
			password = form.cleaned_data['password']

			# create user
			user = User.objects.create_user(username,email,password)
			# user.save()

			# create provile
			user.profile.headline = headline
			user.profile.location = location
			user.profile.save()

			# make sure using right backend
			request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
			
			# log user in
			user = authenticate(username=username,password=password)
			
			# make sure authentication worked
			if user is not None:
				auth_login(request,user)

			# send to personalization
			return HttpResponseRedirect('/')
	else:
		form = RegisterForm()

	return render_to_response('accounts/register.html',{'form':form},context_instance=RequestContext(request))

@login_required
def logout(request):
	auth_logout(request)
	return HttpResponseRedirect('/welcome')

def linkedin_refused(request):
	return render_to_response('accounts/refused.html',context_instance=RequestContext(request))

def linkedin_authorize(request):
		
	liparser = LIProfile()
	redirect_url, request_token = liparser.authorize()
	# check for a redirect parameter
	if request.GET.get('next'):
		request.session['next'] = request.GET.get('next')
	request.session['request_token'] = request_token

	return HttpResponseRedirect(redirect_url)
  
# @login_required
def linkedin_authenticate(request):  
	
	liparser = LIProfile()
	# verify that oauth_verifier was returned
	if request.GET.getlist("oauth_verifier"):
		access_token, linkedin_user_info = liparser.authenticate(request.session['request_token'],request.GET['oauth_verifier'])
	# check for official LI error
	elif request.GET.getlist("oauth_problem"):
		# fetch error
		li_error = request.GET.getlist('oauth_problem')[0]
		# user refused access
		if li_error == 'user_refused':
			return HttpResponseRedirect('/account/refused')
	
	# check if user is already logged on
	request.session['linkedin_user_info'] = linkedin_user_info
	request.session['access_token'] = access_token

	if request.user.is_authenticated():
		# if logged in, link accounts and return
		print ("@ accounts/authenticate, request.user.is_authenticated = true")
		return HttpResponseRedirect('/account/link')

	request.session['_auth_user_backend'] = 'prosperime.accounts.backends.LinkedinBackend'
	
	user = authenticate(acct_id=linkedin_user_info['id'])
	# print user
	# print linkedin_user_info['id']
	if user is not None:
		

		auth_login(request,user)
		if 'next' in request.session:
			return HttpResponseRedirect(request.session['next'])
		else:
			return HttpResponseRedirect('/')
	else:
		# store information in a cookie
		request.session['linkedin_user_info'] = linkedin_user_info
		request.session['access_token'] = access_token

	# check to see if user is currently logged in
	if request.user.is_authenticated():
		# if loged in, link accounts and return
		return HttpResponseRedirect('/account/link')
	else:
		# if not logged in, ask to finish user registration process
		return HttpResponseRedirect('/account/finish')


def finish_registration_old(request):

	import accounts.emaillib as emaillib
	# get linkedin info from session
	linkedin_user_info = request.session['linkedin_user_info']
	access_token = request.session['access_token']

	# check for dormant user
	try: 
		user = User.objects.get(profile__status="dormant",account__uniq_id=linkedin_user_info['id'])
		user.email=linkedin_user_info['emailAddress']
		logger.info("activated dormant user "+linkedin_user_info['emailAddress'])
		existing = True
	except:
		# create user
		user = User.objects.create_user(linkedin_user_info['emailAddress'],linkedin_user_info['emailAddress'])
		logger.info("created new user "+linkedin_user_info['emailAddress'])
		user.save()
		existing = False
		
	# set user properties
	password = User.objects.make_random_password()
	user.set_password(password)
	user.save()	
	# set profile status
	user.profile.status = "active"
	user.profile.first_name = linkedin_user_info['firstName']
	user.profile.last_name = linkedin_user_info['lastName']
	user.profile.save()
	user.username = linkedin_user_info['emailAddress']
	user.is_active = True
	user.save()	
	
	# send welcome email
	send_welcome_email.delay(user)
	
	# check to see if user provided a headline
	if 'headline' in linkedin_user_info:
		user.profile.headline = linkedin_user_info['headline']
		user.profile.save()
	# check to see if user has a linkedin picture
	if 'pictureUrls' in linkedin_user_info:
		li_parser = LIProfile()
		li_parser.add_profile_pic(user,linkedin_user_info['pictureUrls']['values'][0])

	# update LI account
	if existing:
		# get existing LI account
		acct = Account.objects.get(owner=user,service="linkedin")
	else:
		# create LinkedIn account
		acct = Account()
	
	acct.owner = user
	acct.access_token = access_token['oauth_token']
	acct.token_secret = access_token['oauth_token_secret']
	acct.service = 'linkedin'
	acct.expires_on = datetime.now() + timedelta(seconds=int(access_token['oauth_authorization_expires_in']))
	acct.uniq_id = linkedin_user_info['id']
	acct.status = "active"
	acct.save()
		
	# finish processing LI profile
	profile_task = process_li_profile.delay(user.id,acct.id)

	# start processing connections
	connections_task = process_li_connections.delay(user.id,acct.id)

	# save task ids to session
	request.session['tasks'] = {
		'profile': profile_task.id,
		'connections': connections_task.id
	}

	request.session['_auth_user_backend'] = 'prosperime.accounts.backends.LinkedinBackend'
	
	user = authenticate(acct_id=linkedin_user_info['id'])
	
	if user is not None:
	
		auth_login(request,user)

		if 'next' not in request.session:
			return HttpResponseRedirect('/majors/')
		else:
			return HttpResponseRedirect(request.session['next'])
	
def finish_registration(request):
	# get linkedin info from session
	linkedin_user_info = request.session['linkedin_user_info']
	access_token = request.session['access_token']
	
	# if request.POST:
	if request.method == "POST":
		# form submitted
		form = FinishAuthForm(request.POST)
		if form.is_valid():
			from accounts.models import Pref
			import accounts.emaillib as emaillib
			# grab cleaned values from form
			username = form.cleaned_data['username']
			email = form.cleaned_data['username']
			# location = form.cleaned_data['location']
			# headline = form.cleaned_data['headline']
			password = form.cleaned_data['password']

			# fetch LI data
			# linkedin_user_info = request.session['linkedin_user_info']
			# access_token = request.session['access_token']

			# check to see if dormant user already exists
			try: 
				# logger.info('@ accounts.finish -- checking for dormant user')
				user = User.objects.get(profile__status="dormant",account__uniq_id=linkedin_user_info['id'])
				existing = True
				user.profile.status = "active"
				user.profile.save()
				user.set_password(password)
				user.username = username
				user.is_active = True
				user.save()
				logger.info("activate dormant user: " + username)
				critical_logger.info("created new user: " + username)
			except:
				# logger.info('@ accounts.finish -- new user')
				# create user
				user = User.objects.create_user(username,email,password)
				user.save()
				
				existing = False
				user.profile.status = "active"
				user.profile.save()
				logger.info("created new user: " + username)
				critical_logger.info("created new user: " + username)
			# send welcome email
			welcome = emaillib.WelcomeEmail(user)
			try:
				res = welcome.trigger()
			except:
				logger.error("couldn't send welcome email")
			# add email prefs
			if form.cleaned_data['notification']:
				pref = Pref(user=user,name="notification",value=1)
				pref.save()
			else:
				pref = Pref(user=user,name="notification",value=0)
				pref.save()
			# make sure using right backend
			request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
			# log user in
			user = authenticate(username=username,password=password)
			
			# make sure authentication worked
			if user is not None:
				# print 'in to auth login'
				auth_login(request,user)
			else:
				# try logging in now with LinkedIn
				request.session['_auth_user_backend'] = 'prosperime.accounts.backends.LinkedinBackend'
				try:
					user = authenticate(acct_id=linkedin_user_info['id'])
					if user is not None:
						auth_login(request,user)	
				except:
					# somehow authentication failed, redirect with error message
					messages.error(request, 'Something went wrong. Please try again.')
					return render_to_response('accounts/finish_login.html',{'form':form},context_instance=RequestContext(request))



			# update user profile
			# user.profile.full_name = request.session['linkedin_user_info']['firstName'] + " " + request.session['linkedin_user_info']['lastName']		
			user.profile.first_name = linkedin_user_info['firstName']
			user.profile.last_name = linkedin_user_info['lastName']
			# user.profile.location = location
			# check to see if user provided a headline
			# if headline:
			# 	user.profile.headline = headline
			# else:
			user.profile.headline = linkedin_user_info['headline']
			user.profile.save()

			# add pofile picture
			# if 'pictureUrl' in linkedin_user_info:
			# 	# _add_profile_pic(user,linkedin_user_info['pictureUrl'])
			# 	li_parser = LIProfile()
			# 	li_parser.add_profile_pic(user,linkedin_user_info['pictureUrl'])

			if 'pictureUrls' in linkedin_user_info:
				li_parser = LIProfile()
				li_parser.add_profile_pic(user,linkedin_user_info['pictureUrls']['values'][0])


			if existing:
				# get existing LI account
				acct = Account.objects.get(owner=user,service="linkedin")
			else:
				# create LinkedIn account
				acct = Account()
			
			acct.owner = user
			acct.access_token = access_token['oauth_token']
			acct.token_secret = access_token['oauth_token_secret']
			acct.service = 'linkedin'
			acct.expires_on = datetime.now() + timedelta(seconds=int(access_token['oauth_authorization_expires_in']))
			acct.uniq_id = linkedin_user_info['id']
			acct.status = "active"
			acct.save()

			# finish processing LI profile
			try:
				profile_task = process_li_profile.delay(user.id,acct.id)
				request.session['tasks']['profile'] = profile_task.id
			except:
				logger.error("Failed to process LI profile for user: " + username)

			# start processing connections
			try:
				connections_task = process_li_connections.delay(user.id,acct.id)
				request.session['tasks']['connections'] = connections_task.id
			except:
				logger.error("Failed to process LI connections for user: " + username)

			# save task ids to session
			
			# request.session['tasks'] = {
			# 	'profile': profile_task.id,
			# 	'connections': connections_task.id
			# }
			logger.info("added tasks to session")

			#return HttpResponseRedirect('/account/success')
			if 'next' not in request.session:
				return HttpResponseRedirect('/')
			else:
				return HttpResponseRedirect(request.session['next'])
	else:
		form = FinishAuthForm()

	return render_to_response('accounts/finish_registration.html',{'form':form,'email_address':linkedin_user_info['emailAddress']},context_instance=RequestContext(request))

def finish_login(request):
	# TODO: redirect if not not authenticated through LinkedIn already
	
	# if request.POST:
	if request.method == "POST":
		# form submitted
		form = FinishAuthForm(request.POST)
		if form.is_valid():
			from accounts.models import Pref
			import accounts.emaillib as emaillib
			# grab cleaned values from form
			username = form.cleaned_data['username']
			email = form.cleaned_data['email']
			# location = form.cleaned_data['location']
			# headline = form.cleaned_data['headline']
			password = form.cleaned_data['password']

			# fetch LI data
			linkedin_user_info = request.session['linkedin_user_info']
			access_token = request.session['access_token']

			# check to see if dormant user already exists
			try: 
				print '@ accounts.finish -- checking for dormant user'
				user = User.objects.get(profile__status="dormant",account__uniq_id=linkedin_user_info['id'])
				existing = True
				user.profile.status = "active"
				user.profile.save()
				user.set_password(password)
				user.username = username
				user.is_active = True
				user.save()
				print "@ accounts.finish -- user already exists"
			except:
				print '@ accounts.finish -- new user'
				# create user
				user = User.objects.create_user(username,email,password)
				user.save()
				
				existing = False
				user.profile.status = "active"
				user.profile.save()
				print "@ accounts.finish -- created new user"
			# send welcome email
			welcome = emaillib.WelcomeEmail(user)
			welcome.send_email()
			# add email prefs
			if form.cleaned_data['notification']:
				pref = Pref(user=user,name="notification",value=1)
				pref.save()
			else:
				pref = Pref(user=user,name="notification",value=0)
				pref.save()
			# make sure using right backend
			request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
			# log user in
			user = authenticate(username=username,password=password)
			
			# make sure authentication worked
			if user is not None:
				print 'in to auth login'
				auth_login(request,user)
			else:
				# try logging in now with LinkedIn
				request.session['_auth_user_backend'] = 'prosperime.accounts.backends.LinkedinBackend'
				try:
					user = authenticate(acct_id=linkedin_user_info['id'])
					if user is not None:
						auth_login(request,user)	
				except:
					# somehow authentication failed, redirect with error message
					messages.error(request, 'Something went wrong. Please try again.')
					return render_to_response('accounts/finish_login.html',{'form':form},context_instance=RequestContext(request))



			# update user profile
			# user.profile.full_name = request.session['linkedin_user_info']['firstName'] + " " + request.session['linkedin_user_info']['lastName']		
			user.profile.first_name = linkedin_user_info['firstName']
			user.profile.last_name = linkedin_user_info['lastName']
			# user.profile.location = location
			# check to see if user provided a headline
			# if headline:
			# 	user.profile.headline = headline
			# else:
			user.profile.headline = linkedin_user_info['headline']
			user.profile.save()

			# add pofile picture
			# if 'pictureUrl' in linkedin_user_info:
			# 	# _add_profile_pic(user,linkedin_user_info['pictureUrl'])
			# 	li_parser = LIProfile()
			# 	li_parser.add_profile_pic(user,linkedin_user_info['pictureUrl'])

			if 'pictureUrls' in linkedin_user_info:
				li_parser = LIProfile()
				li_parser.add_profile_pic(user,linkedin_user_info['pictureUrls']['values'][0])


			if existing:
				# get existing LI account
				acct = Account.objects.get(owner=user,service="linkedin")
			else:
				# create LinkedIn account
				acct = Account()
			
			acct.owner = user
			acct.access_token = access_token['oauth_token']
			acct.token_secret = access_token['oauth_token_secret']
			acct.service = 'linkedin'
			acct.expires_on = datetime.now() + timedelta(seconds=int(access_token['oauth_authorization_expires_in']))
			acct.uniq_id = linkedin_user_info['id']
			acct.status = "active"
			acct.save()

			# finish processing LI profile
			profile_task = process_li_profile.delay(user.id,acct.id)

			# start processing connections
			connections_task = process_li_connections.delay(user.id,acct.id)

			# save task ids to session
			request.session['tasks'] = {
				'profile': profile_task.id,
				'connections': connections_task.id
			}

			#return HttpResponseRedirect('/account/success')
			if 'next' not in request.session:
				return HttpResponseRedirect('/majors/')
			else:
				return HttpResponseRedirect(request.session['next'])
	else:
		form = FinishAuthForm()

	return render_to_response('accounts/finish_login.html',{'form':form},context_instance=RequestContext(request))


def finish_link(request):
	# get info for creating an account
	linkedin_user_info = request.session['linkedin_user_info']
	access_token = request.session['access_token']

	# delete LI info from session
	del request.session['linkedin_user_info']
	del request.session['access_token']

	# add profile if it doesn't exit (for superadmin after reset)
	# try:
	# 	request.user.profile
	# except:
	# 	request.user.profile = Profile()
	# 	request.user.profile.first_name = linkedin_user_info['firstName']
	# 	request.user.profile.last_name = linkedin_user_info['lastName']
	# 	request.user.profile.headline = linkedin_user_info['headline']
	# 	request.user.profile.save()

	try:
		request.user.profile
	except:
		request.user.profile = Profile()

	request.user.profile.first_name = linkedin_user_info['firstName']
	request.user.profile.last_name = linkedin_user_info['lastName']
	request.user.profile.headline = linkedin_user_info['headline']
	request.user.profile.save()

	# create LinkedIn account
	acct = Account()
	acct.owner = request.user
	acct.access_token = access_token['oauth_token']
	acct.token_secret = access_token['oauth_token_secret']
	acct.service = 'linkedin'
	acct.expires_on = datetime.now() + timedelta(seconds=int(access_token['oauth_authorization_expires_in']))
	acct.uniq_id = linkedin_user_info['id']
	acct.save()

	# add pofile picture
	if 'pictureUrl' in linkedin_user_info:
		li_parser = LIProfile()
		li_parser.add_profile_pic(request.user,linkedin_user_info['pictureUrl'])
		# _add_profile_pic(request.user,linkedin_user_info['pictureUrl'])

	# finish processing LI profile
	profile_task = process_li_profile.delay(request.user.id,acct.id)

	# start processing connections
	connections_task = process_li_connections.delay(request.user.id,acct.id)

	# save task ids to session
	request.session['tasks'] = {
		'profile': profile_task.id,
		'connections': connections_task.id
	}

	messages.success(request, 'Your LinkedIn account has been successfully linked.')

	if 'next' not in request.session:
		return HttpResponseRedirect('/majors/')
	else:
		return HttpResponseRedirect(request.session['next'])

def success(request):
	return render_to_response('accounts/success.html',context_instance=RequestContext(request))

# def _add_profile_pic(user,img_url):
# 	img = None
# 	img_ext = urlparse.urlparse(img_url).path.split('/')[-1].split('.')[1]
# 	img_filename = user.profile.std_name() + "." + img_ext
# 	try:
# 		img = urllib2.urlopen(img_url)
# 	except urllib2.HTTPError, e:
# 		self.stdout.write(str(e.code))
# 	if img:
# 		pic = Picture()
# 		pic.person = user.profile
# 		pic.source = 'linkedin'
# 		pic.description = 'linkedin profile pic'
# 		pic.save()
# 		with open('tmp_img','wb') as f:
# 			f.write(img.read())
# 		with open('tmp_img','r') as f:
# 			img_file = File(f)
# 			pic.pic.save(img_filename,img_file,True)
# 		os.remove('tmp_img')
	

def random_profile(request):

	while(1):
		profile_max = Profile.objects.count()
		profile_num = random.randint(1, profile_max)
		if (Position.objects.filter(person__id=profile_num).count() > 0):
			break;

	return profile(request, profile_num)



#########################
### JSON/AJAX Methods ###
#########################

def save_position(request):
	response = {}

	# Error checking
	if not request.POST or not request.is_ajax():
		response.update({"errors":["incorrect request type"], "result":"failure"})
		return HttpResponse(json.dumps(response))

	# Grab values for the Position
	position_id = int(request.POST.get("id"))
	position_type = request.POST.get("type")
	if position_type == "education":
		field = request.POST.get("field")
		degree = request.POST.get("degree")
		title = "Student"
	else:
		title = request.POST.get("title")
		field = None
		degree = None

	# Get or create entity
	entity_name = request.POST.get("entity")
	entity = _get_company_name_only(entity_name)
	if entity is None:
		entity = Entity(name=entity_name, status="stub") ## TODO: expand this
		entity.save()

	# Format dates
	start_date = _convert_string_to_datetime(request.POST.get("start_date"))
	end_date = _convert_string_to_datetime(request.POST.get("end_date"))

	try:
		# (if, new position)
		if position_id == -1:
			# create new position
			pos = Position(person=request.user, title=title, field=field, degree=degree, entity=entity, start_date=start_date, end_date=end_date, type=position_type, status="manual")
			pos.save()
			# map careers + ideals
			careers = careerlib.match_careers_to_position(pos)
			careerlib.match_position_to_ideals(pos)
			for c_id in careers:
				c = Career.objects.get(pk=c_id)
				pos.careers.add(c)
			pos.save()

		# (else, edit existing position)
		else:
			pos = Position.objects.get(id=position_id) # TODO: change this, right now bulk overwrite
			pos.entity = entity
			pos.type = position_type
			pos.field = field
			pos.degree = degree
			pos.title = title
			pos.start_date = start_date
			pos.end_date = end_date
			pos.save()

		response.update({"result":"success", "pos_id": pos.id})
	except:
		response.update({"result":"failure", "errors":["Error writing to DB."]})


	return HttpResponse(json.dumps(response))


def validate_position(request):
	# initialize response
	response = {}
	# return error if not ajax or post
	if not request.is_ajax or not request.POST:
		response['result'] = 'failure'
		response['errors'] = 'invalid request type'
		return HttpResponse(json.dumps(response))

	if request.POST:
		from careers.forms import AddProgressDetailsForm
		# bind form
		form = AddProgressDetailsForm(request.POST)
		# validate form
		if form.is_valid():
			# init carerlib
			mapper = careerlib.EdMapper()

			# Education
			if form.cleaned_data['type'] == "education":
				# set up initial data
				response['data'] = {
					'grad_year':form.cleaned_data['end_date'].year	
				}
				# see if we can map degree
				idealdegree = mapper.match_degree(form.cleaned_data['degree'] + form.cleaned_data['field'])
				if idealdegree:
					# there is a match, add ideal id to path generation
					response['result'] = 'success'
					response['data']['degree'] = idealdegree.title
					response['data']['field'] = None
					response['data']['ideal_id'] = idealdegree.id
					
				else:
					# no match, still return data but don't update 
					response['result'] = 'success'
					response['errors'] = 'missing ideal id'
					response['data']['degree'] = form.cleaned_data['degree']
					response['data']['field'] = form.cleaned_data['field']
				
				# see if we can match entity
				entity = Entity.objects.filter(name__icontains=form.cleaned_data['entity'],subtype="ed-institution").annotate(pop=Count("positions__id")).order_by("-pop")
				if entity.exists():
					# there is a match
					response['data']['entity'] = entity[0].name
					response['data']['entity_id'] = entity[0].id
				else:
					# no match, return same text string as entered
					response['data']['entity'] = form.cleaned_data['entity']
				# return JSON response
				return HttpResponse(json.dumps(response))

			# Position
			elif form.cleaned_data['type'] == "org" or form.cleaned_data["type"] == "internship":
				# set up initial data
				response['data'] = {
					'start_date':form.cleaned_data['start_date'].year,
					'end_date':form.cleaned_data['end_date'].year
				}
				# see if we can map position
				pos = Position() ## THOMAS -- this was "Object()"... I changed it b/c it wouldn't work
				pos.title = form.cleaned_data['title']
				pos.type = "position"
				# pos.entity = None
				idealpos = mapper.return_ideal_from_position(pos)
				if idealpos:
					response['result'] = "success"
					response['data']['title'] = idealpos.title
					response['data']['ideal_id'] = idealpos.id
				else:
					response['result'] = 'success'
					response['errors'] = 'missing ideal id'
					response['data']['title'] = form.cleaned_data['title']
				# see if we can find entity
				entity = Entity.objects.filter(name__icontains=form.cleaned_data['entity']).annotate(pop=Count("positions__id")).order_by("-pop")
				if entity.exists():
					# there is a match
					response['data']['entity'] = entity[0].name
					response['data']['entity_id'] = entity[0].id
				else:
					# no match, return same text string as entered
					response['data']['entity'] = form.cleaned_data['entity']
				return HttpResponse(json.dumps(response))
		else:
			# return error
			response['result'] = "failure"
			response['errors'] = form.errors
			return HttpResponse(json.dumps(response))


def upload_profile_pic(request):
	response = {}


	if not request.POST or not request.is_ajax:
		response.update({"errors":["Incorrect request type."], "result":"failure"})
		return HttpResponse(json.dumps(response))

	print request.POST
	## THOMAS: there should be a file object in here that is the the file uploaded on the client

	response.update({"result":"success"})

	return HttpResponse(json.dumps(response))


# Adds a connection between the requesting user and the profile
#	currently being viewed
def connect(request):
	u1 = request.user
	u2 = User.objects.get(id=request.POST.get('id'))
	response = {}

	try:
		cxn1 = Connection()
		cxn1.person1 = u1.profile
		cxn1.person2 = u2.profile
		cxn1.service = "linkedin"
		cxn1.status = "added"
		cxn1.save()

		cxn2 = Connection()
		cxn2.person1 = u1.profile
		cxn2.person2 = u2.profile
		cxn2.service = "linkedin"
		cxn2.status = "added"
		cxn2.save()

		response["result"] = "success"
	except:
		response["result"] = "failure"
		response["errors"] = "Error creating connections @ DB"

	return HttpResponse(simplejson.dumps(response))




@login_required
def personalize(request):
	'''
	asks users for more information about their goals and whatnot
	'''
	# check to see if tasks information is in session
	tasks = False
	profile_task_id = 99
	connections_task_id = 'null'
	if "tasks" in request.session:
		tasks = True
		profile_task_id = request.session['tasks']['profile']
		connections_task_id = request.session['tasks']['connections']

	data = {
		'tasks':tasks,
		'profile_task_id':profile_task_id,
		'connections_task_id':connections_task_id,
		'educations':Position.objects.filter(person=request.user,type="education").values("id","degree","field","entity__name","end_date"),
		'positions':Position.objects.filter(person=request.user).exclude(type="education").values("id","title","entity__name","start_date","end_date"),
		'geographies':Region.objects.filter(people=request.user).values("name","id"),
		'goals':GoalPosition.objects.filter(owner=request.user).values("position__title","id")
	}

	return render_to_response('careers/personalize.html',data,context_instance=RequestContext(request))

@login_required
def add_to_profile(request):
	# check for form submission
	if request.POST:
		from accounts.forms import AddEducationForm, AddExperienceForm, AddGeographyForm, AddGoalForm, AddProfilePicForm
		from django.core.files import File
		import accounts.tasks as tasks
		if request.POST['type'] == "profile_pic":
			# bind form
			form = AddProfilePicForm(request.POST,request.FILES)
			# validate form
			if form.is_valid():
				# create picture object
				img_filename = request.user.profile.std_name() + ".jpg"
				pic = Picture()
				pic.person = request.user.profile
				pic.source = 'user'
				pic.save()
				with open('tmp_img','wb') as f:
					f.write(request.FILES['pic'].read())
				with open('tmp_img','r') as f:
					img_file = File(f)
					pic.pic.save(img_filename,img_file,True)
				os.remove('tmp_img')
				response = {
					'result':'success',
					'pic':pic.pic.url
				}
			else:
				response = {
					'result':'failure',
					'position':form.errors
				}
			return HttpResponse(json.dumps(response))
		if request.POST['type'] == "education":
			# bind form
			form = AddEducationForm(request.POST)
			# validate form
			if form.is_valid():
				try:
					school = Entity.objects.get(name=form.cleaned_data['school'])
				except MultipleObjectsReturned:
					school = Entity.objects.filter(name=form.cleaned_data['school'])[0]
				except ObjectDoesNotExist:
					school = Entity(name=form.cleaned_data['school'])
					school.save()

				ed = Position(type="education",entity=school,end_date=form.cleaned_data['end_date'],degree=form.cleaned_data['degree'],field=form.cleaned_data['field'],person=request.user)
				ed.save()
				# kick off task to process for career matches
				tasks.match_position(ed)
				position_data = {
					'degree':ed.degree,
					'pos_id':ed.id,
					'field':ed.field,
					'entity':ed.entity.name
				}
				response = {
					'result':'success',
					'position':position_data
				}
			else:
				response = {
					'result':'failure',
					'errors':form.errors
				}
			return HttpResponse(json.dumps(response))
		if request.POST['type'] == "experience":
			# bind form
			form = AddExperienceForm(request.POST)
			# validate form
			if form.is_valid():
				try:
					entity = Entity.objects.get(name=form.cleaned_data['entity'])
				except MultipleObjectsReturned:
					entity = Entity.objects.filter(name=form.cleaned_data['entity'])[0]
				except ObjectDoesNotExist:
					entity = Entity(name=form.cleaned_data['entity'])
					entity.save()

				pos = Position(
					type="professional",
					entity=entity,
					person=request.user,
					start_date=form.cleaned_data['start_date'],
					end_date=form.cleaned_data['end_date'],
					title=form.cleaned_data['title']
					)
				pos.save()
				# kick off task to process career matches
				tasks.match_position(pos)
				# return json response
				position_data = {
					'title':pos.title,
					'pos_id':pos.id,
					'entity':pos.entity.name
				}
				response = {
					'result':'success',
					'position':position_data
				}
				
			else:
				response = {
					'result':'failure',
					'errors':form.errors
				}
			return HttpResponse(json.dumps(response))
		if request.POST['type'] == "geography":
			# bind form
			form = AddGeographyForm(request.POST)
			# validate form
			if form.is_valid():
				try:
					reg = Region.objects.get(name=form.cleaned_data['region'])
				except MultipleObjectsReturned:
					reg = Region.objects.filter(name=form.cleaned_data['region'])[0]
				reg.people.add(request.user)
				response = {
					'result':'success',
					'geo':reg.name
				}
			else:
				response = {
					'result':'failure',
					'errors':form.errors
				}
			return HttpResponse(json.dumps(response))
		if request.POST['type'] == "goal":
			# bind form
			form = AddGoalForm(request.POST)
			# validate form
			if form.is_valid():
				try:
					ideal = IdealPosition.objects.get(title=form.cleaned_data['goal'])
				except MultipleObjectsReturned:
					ideal = IdealPosition.objects.filter(title=form.cleaned_data['goal'])[0]
				g = GoalPosition(position=ideal,owner=request.user)
				g.save()
				response = {
					'result':'success',
					'goal':g.position.title,
					'id':g.id
				}
			else:
				response = {
					'result':'failure',
					'errors':form.errors
				}
			return HttpResponse(json.dumps(response))


def remove_from_profile(request):

	if request.POST:
		from accounts.forms import AddEducationForm, AddExperienceForm, AddGeographyForm, AddGoalForm, AddProfilePicForm
		from django.core.files import File
		import accounts.tasks as tasks
		if request.POST['type'] == "profile_pic":
			pass
		if request.POST['type'] == "education":
			# retrieve education
			ed = Position.object.get(id=request.POST.get("id"))
			if ed:
				ed.delete()
				response = {
					'result':'success'
				}
			else:
				response = {
					'result':'failure',
					'errors': 'Couldn\'t find the education'
				}
		if request.POST['type'] == "experience":
			# retrieve position
			pos = Position.objects.get(id=request.POST["id"])
			if pos:
				pos.delete()
				response = {
					'result':'success'
				}
			else:
				response = {
					'result':'failure',
					'errors': 'Couldn\'t find the position'
				}
		if request.POST['type'] == "geo":
			# retrieve region
			reg = Region.objects.get(id=request.POST['id'])
			if reg:
				user = User.objects.get(id=request.POST['user_id'])
				reg.people.remove(user)
				response = {
					'result':'success'
				}
			else:
				response = {
					'result':'failure',
					'errors': 'Something went wrong. Please try again.'
				}
			
		if request.POST['type'] == "goal":
			# retreive goal
			goal = GoalPosition.objects.get(id=request.POST['id'])
			if goal:
				goal.delete()
				response = {
					'result': 'success'
				}
			else:
				response = {
					'result': 'failure',
					'errors': 'Something went wrong'
				}
		return HttpResponse(json.dumps(response))
	else:
		response = {
			'result': 'failure',
			'errors': 'Something went wrong. Please try again.'
		}
		return HttpResponse(json.dumps(response))


###############
##  Helpers  ##
###############
# taken from lilib
def _get_company_name_only(name):
	cos = Entity.objects.filter(name=name)
	# use Filter for safety
	if len(cos) > 0:
		# check if one has li_univ_name and li_uniq_id
		for c in cos:
			if c.li_univ_name is not None and c.li_uniq_id is not None:
				return c
		# else just return first result
		return cos[0]
	else:
		return None


# From SO, returns dict of diff fields between models
def _diff_models(model1, model2, excludes = []):
    changes = {}
    for field in model1._meta.fields:
        if not (isinstance(field, (fields.AutoField, fields.related.RelatedField)) 
                or field.name in excludes):
            if field.value_from_object(model1) != field.value_from_object(model2):
                changes[field.verbose_name] = (field.value_from_object(model1),
                                                   field.value_from_object(model2))
    return changes

def _convert_string_to_datetime(string):
	# TODO: validate input string "MM/YY"

	time_struct = time.strptime(string, "%m/%y")
	dt = datetime.fromtimestamp(time.mktime(time_struct))
	return dt


## 8/8 STILL IN USE ##
# Takes a queryset of user's positions and returns 
#	information needed for timeline creation
def _prepare_positions_for_timeline(positions):

	if len(positions) == 0:
		return [], None, None, None, None

	formatted_positions = []

	# Process each position
	for pos in positions:
		formatted_pos = {}

		if pos.start_date and pos.title: # ignore no start_date

			formatted_pos['duration'] = pos.duration_in_months + 1 ## so 6/11 - 6/11 != 0
			formatted_pos['id'] = pos.id
			
			# Assumption: no end date = current
			if not pos.end_date:
				formatted_pos['end_date'] = "Current"
			else:
				formatted_pos['end_date'] = helpers._format_date(pos.end_date)
			formatted_pos['start_date'] = helpers._format_date(pos.start_date)
			# formatted_pos['description'] = pos.description

			# pos.pic = pos.entity.default_logo()
			formatted_pos['co_name'] = pos.entity.name


			# Internships
			if 'ntern' in pos.title and 'nternational' not in pos.title or "Summer" in pos.title:
				formatted_pos['type'] = 'internship'
				formatted_pos['title'] = pos.title

			# Educations
			elif pos.type == 'education' or pos.title == 'Student':
				formatted_pos['type'] = 'education'
				if pos.degree is not None:
					formatted_pos['degree'] = pos.degree
				if pos.field is not None:
					formatted_pos['field'] = pos.field
				formatted_pos['school'] = pos.entity.name

				if pos.degree is not None and pos.field is not None:
					formatted_pos['title'] = pos.degree + ", " + pos.field
				elif pos.degree is not None:
					formatted_pos['title'] = pos.degree
				elif pos.field is not None:
					formatted_pos['title'] = pos.field
				else:
					formatted_pos['title'] = 'Student' ## Let's just guess 

			# Jobs
			else:
				formatted_pos['title'] = pos.title
				formatted_pos['type'] = 'org'

			formatted_positions.append(formatted_pos)
	
	# Sort by start date
	formatted_positions.sort(key=lambda	 p:(p['start_date'][3:] + p['start_date'][:2]))
	start_date = formatted_positions[0]['start_date']
	formatted_positions.reverse()
	total_time = helpers._months_from_now_json(start_date)
	end_date = helpers._format_date(datetime.now())

	return formatted_positions, start_date, end_date, total_time


def _uniqify(list):
    tmp = set()
    solution = []
    for element in list:
        # Hack city
        if element.title == None:
            element.title = ""
        current = element.title + ', ' + element.co_name

        if current in tmp:
            continue
        tmp.add(current)
        solution.append(element)

    return solution
