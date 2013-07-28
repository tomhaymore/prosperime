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

# from django.contrib.auth.decorators import  _required
from django.contrib.auth import authenticate, logout as auth_logout, login as auth_login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import simplejson

from django.contrib import messages
from lilib import LIProfile

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

# Prosperime
from accounts.models import Account, Profile, Picture, Connection
from careers.models import SavedPath, CareerDecision, Position, SavedPosition, SavedCareer, GoalPosition, IdealPosition
from entities.models import Entity, Region
from accounts.tasks import process_li_profile, process_li_connections, send_welcome_email
from accounts.forms import FinishAuthForm, AuthForm, RegisterForm
import utilities.helpers as helpers

logger = logging.getLogger(__name__)
critical_logger = logging.getLogger("benchmarks")


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
			return HttpResponseRedirect('/majors/')
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
				return HttpResponseRedirect('/majors/')
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


# View for invidiual profiles
@login_required
def profile(request, user_id):

	user = User.objects.get(id=user_id)
	if user.profile.status == "dormant":
		HttpResponseRedirect("/home/")

	profile = user.profile
	profile_pic = user.profile.default_profile_pic()
	
	own_profile = False
	own_profile_javascript = "false"
	queue = None
	viewer_saved_paths = []
	saved_path_ids = None
	goal_careers = None
	career_decision_position = "false"
	goal_positions = None

	# career_map = profile.all_careers
	top_careers = profile.get_all_careers(3)
	career_map = None
	# top_careers = None

	# Convert positions to timeline info
	positions = Position.objects.filter(person=user).select_related('careerDecision')
	formatted_positions, start_date, end_date, total_time, current = _prepare_positions_for_timeline(positions)

	# If Own Profile, get extra information
	if int(user_id) == int(request.user.id):
		own_profile = True
		own_profile_javascript = "true"

		# Your Saved Paths
		saved_path_queryset = SavedPath.objects.filter(owner=request.user).exclude(title='queue')
		viewer_saved_paths = []
		saved_path_ids = []
		for path in saved_path_queryset:
			viewer_saved_paths.append(_saved_path_to_json(path))
			saved_path_ids.append([path.id, path.title])

		# Your Goal Careers
		goal_careers_queryset = SavedCareer.objects.filter(owner=request.user).select_related("career")
		goal_careers = []
		for career in goal_careers_queryset:
			formatted_career = _saved_career_to_json(career.career)
			formatted_career["saved_career_id"] = career.id
			goal_careers.append(formatted_career)

		# Your Goal Positions
		goal_positions_queryset = GoalPosition.objects.filter(owner=request.user).select_related("position")
		goal_positions = []
		for pos in goal_positions_queryset:
			formatted_position = _ideal_position_to_json(pos.position)
			formatted_position["goal_id"] = pos.id
			goal_positions.append(formatted_position)

		# Positions of Interest ('Queue')
		try:
			queue = SavedPath.objects.filter(owner=request.user, title='queue').prefetch_related()
			queue = _saved_path_to_json(queue[0])
		except:
			queue = []

		# Career Decision Prompt
		# career_decision = _get_career_decision_prompt_position(top_careers, positions, profile)
		# if career_decision is None:
		# 	career_decision_position = None;
		# else:
		# 	career_decision_position = {
		# 		'id':career_decision.id,
		# 		'title':career_decision.title,
		# 		'co_name':career_decision.entity.name,
		# 		'type':career_decision.type,
		# 	}
		career_decision_position = "false"


	if not own_profile:
		# see if connected
		viewer = request.user.profile
		if profile in viewer.connections.all():
			is_connected = True
		else:
			is_connected = False


		# Users Saved Paths
		saved_path_queryset = SavedPath.objects.filter(owner__id=user_id).exclude(title='queue')
		viewer_saved_paths = []
		saved_path_ids = []
		for path in saved_path_queryset:
			viewer_saved_paths.append(_saved_path_to_json(path))
			saved_path_ids.append([path.id, path.title])

	else:
		is_connected = True


	response = {
		'user':user,
		'profile':profile,
		'viewer_saved_paths':simplejson.dumps(viewer_saved_paths),
		'saved_path_ids':saved_path_ids,
		'profile_pic':profile_pic,
		'positions':simplejson.dumps(formatted_positions),
		'current':current,
		'start_date':start_date,
		'end_date':end_date,
		'total_time':total_time,
		# 'career_map':career_map,
		'top_careers':top_careers,
		'career_decision_prompt':career_decision_position,
		'own_profile':own_profile,
		'own_profile_javascript':own_profile_javascript, # b/c js has true/false, not True/False
		'queue':simplejson.dumps(queue),
		'goal_careers':simplejson.dumps(goal_careers),
		'goal_positions':simplejson.dumps(goal_positions),
		'is_connected':is_connected,
	}

	return render_to_response('accounts/profile.html', response, context_instance=RequestContext(request))


@login_required
def profile_org(request, org_id):

	# saved_paths... always need this... better way?
	saved_paths = SavedPath.objects.filter(owner=request.user)

	# nothing related to entities, so don't know if we can batch here
	entity = Entity.objects.get(pk=org_id)

	# Basic Entity Data
	response = {
		'id':org_id,
		'name':entity.name,
		'size':entity.size_range,
		'description':entity.description,
		'logo_path':entity.default_logo(),
	}

	# Related Jobs
	# Should use entity object, but duplicates!
	## jobs = Position.objects.filter(entity=entity).select_related('person__profile')
	jobs = Position.objects.filter(entity__name=entity.name).select_related('person__profile')

	related_jobs = []
	for j in jobs:
		jobs_data = {
			'id':j.id,
			'title':j.title,
			'description':j.description,
			'owner_name':j.person.profile.full_name(),
			'owner_id':j.person.id,
		}
		related_jobs.append(jobs_data)


	response['jobs'] = related_jobs
	response['saved_paths'] = saved_paths

	#return render_to_response('accounts/profile_org.html', response, context_instance=RequestContext(request))

	return render_to_response('accounts/profile.html', {'profile':profile, 'saved_paths': saved_paths, 'profile_pic': profile_pic, 'orgs':org_list, 'ed':ed_list, 'current':current, 'start_date':start_date, 'end_date':end_date, 'total_time': total_time, 'compress': compress, 'career_map': career_map}, context_instance=RequestContext(request))


#########################
### JSON/AJAX Methods ###
#########################


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



# Deletes a goal positions, saved careers, or interested position 
def deleteItem(request):

	response = {}

	item_type = request.POST.get('type')
	item_id = request.POST.get('id')

	print "Delete: " + str(item_type) + ' ' + str(item_id)

	if not item_type:
		response["result"] = "Failure"
		response["errors"] = "no query found"
		return HttpResponse(simplejson.dumps(response))

	if item_type == "goal-position":
		gp = GoalPosition.objects.get(id=item_id)
		gp.delete()
		response["result"] = "Success"

	elif item_type == "saved-career":
		sc = SavedCareer.objects.get(id=item_id)
		sc.delete()
		response["result"] = "Success"

	elif item_type == "queue-position":
		poi = SavedPosition.objects.get(position__id=item_id, path__title="queue", path__owner=request.user)
		poi.delete()
		response["result"] = "Success"

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
					'goal':g.position.title
				}
			else:
				response = {
					'result':'failure',
					'errors':form.errors
				}
			return HttpResponse(json.dumps(response))


# Called after a goal position, saved career is added to a profile, allowing
#	backbone to refresh the template
def updateProfile(request):

	response = {}
	query = request.GET.getlist('query')

	if query:

		if query[0] == "goalPositions":

			goal_positions_queryset = GoalPosition.objects.filter(owner=request.user).select_related("position")
			goal_positions = []
			for pos in goal_positions_queryset:
				goal_positions.append(_ideal_position_to_json(pos.position))

			response["data"] = goal_positions

		elif query[0] == "savedCareers":

			goal_careers_queryset = SavedCareer.objects.filter(owner=request.user).select_related("career")
			goal_careers = []
			for career in goal_careers_queryset:
				goal_careers.append(_saved_career_to_json(career.career))

			response["data"] = goal_careers

		else:
			response["data"] = None

		response["result"] = "success"
		return HttpResponse(simplejson.dumps(response))

	response["result"] = 'failure'
	return HttpResponse(simplejson.dumps(response))


###############
##  Helpers  ##
###############

def _test_career_prompt():


	# get random profile
	profile_max = Profile.objects.count()
	profile_num = random.randint(1, profile_max)

	profile = Profile.objects.get(pk=profile_num)
	positions = Position.objects.filter(person=profile.user)

	top_careers = profile.top_careers

	values = _get_career_decision_prompt_position(top_careers, positions, profile)
	
	if values is None:
		print 'Person: ' + str(profile.user.id) + profile.full_name() + ' has no positinos?'
	else:
		for value in values:
			print 'Person: ' +str(profile.user.id) + profile.full_name()
			if value.title is not None:
				print 'Return Value: ' + value.title + ' ' + value.entity.name
			else:
				print 'Return Value: nameless ' + value.entity.name

	return values

def _get_career_decision_prompt_position(top_careers, positions, profile):
	eligible_candidates = []
	unique_set = set()

	# Convert QuerySet to List & Uniqify
	for pos in positions:
		if pos.title is None:
			pos.title = ""

		if pos.title+pos.entity.name not in unique_set:
			eligible_candidates.append(pos)
			unique_set.add(pos.title + pos.entity.name)

	if len(positions) == 0:
		return None
	else: 
		already_asked = CareerDecision.objects.filter(position__in=positions)
		print "already asked:"
		print already_asked

		# ignore positions that we've already asked about
		for decision in already_asked:
			eligible_candidates.remove(decision.position)

		# need a copy so that removing from list doesn't short the loop...
		# 	annoying python implementation quirk
		candidates_copy = eligible_candidates[:]
		for candidate in candidates_copy:
			# ignore singleton entries, in which we have only one position
			#	for that entity
			print 'testing: ' +str(candidate.id)

			# Test for Singleton Entity
			# if Position.objects.filter(entity__name=candidate.entity.name).count() <= 1:
			# 	eligible_candidates.remove(candidate)
			# 	print 'remove: '+str(candidate.id) + ' singleton entity'

			# Test for Singleton Position
			if Position.objects.filter(title=candidate.title).count() <=1:
				eligible_candidates.remove(candidate)
				print 'remove: '+str(candidate.id)+ ' singleton pos'

			# Test for no title (ok for ed)
			elif candidate.title is "" and candidate.type is not 'education':
				eligible_candidates.remove(candidate)
				print 'remove: '+str(candidate.id) + ' no title non ed'

			## nagging issues - jobs @ universities... cut them?
			## CEO, Board Member...
			## what if all eliminated??

			## idea for better: filter by # entity, position matches

	for e in eligible_candidates:
		print str(e.id)

	# for now, just return top hit
	if len(eligible_candidates) >= 1:
		return eligible_candidates[0]
	else:
		return None

## Takes Saved Path object and returns dict
def _saved_path_to_json(path):

	formatted_path = {
		'title':path.title,
		'last_index':path.last_index,
		'id':path.id,
	}
	all_pos = SavedPosition.objects.filter(path=path).select_related('position')
	positions = []
	for p in all_pos:
		positions.append({
			'title':p.position.title,
			'pos_id':p.position.id,
			'owner':p.position.person.profile.full_name(),
			'owner_id':p.position.person.id,
			'org':p.position.entity.name,
			'type':p.position.type,
		})
	formatted_path['positions'] = positions
	return formatted_path

## Takes a career object and returns dict
def _saved_career_to_json(career):

	formatted_career = {
		'title':career.long_name,
		'career_id':career.id,
	}

	return formatted_career

## Takes Ideal Position object and returns dict
def _ideal_position_to_json(position):

	formatted_position = {
		'title':position.title,
		'description':position.description,
		'ideal_id':position.id,
	}

	return formatted_position


# Takes a queryset of user's positions and returns 
#	information needed for timeline creation
def _prepare_positions_for_timeline(positions):

	if len(positions) == 0:
		return [], None, None, None, None

	formatted_positions = []
	current = None

	if len(positions)  == 0:
		start_date = None
		total_time = None

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
			formatted_pos['description'] = pos.description

			# domains = pos.entity.domains.all()
			# if domains:
			# 	pos.domain = domains[0].name
			# else:
			# 	pos.domain = None

			formatted_pos['co_name'] = pos.entity.name
			# pos.pic = pos.entity.default_logo()



			# Internships
			if 'ntern' in pos.title and 'nternational' not in pos.title or "Summer" in pos.title:
				formatted_pos['type'] = 'internship'
				formatted_pos['title'] = pos.title

			# Educations
			elif pos.type == 'education' or pos.title == 'Student':
				formatted_pos['type'] = 'education'
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
				if pos.current:
					current = pos

			formatted_positions.append(formatted_pos)
	
	
	# Sort by start date
	formatted_positions.sort(key=lambda	 p:(p['start_date'][3:] + p['start_date'][:2]))
	start_date = formatted_positions[0]['start_date']
	formatted_positions.reverse()
	total_time = helpers._months_from_now_json(start_date)
	end_date = helpers._format_date(datetime.now())

	return formatted_positions, start_date, end_date, total_time, current


#################
#### HELPERS ####
#################
# Helper from StackOverflow to remove duplicates from list whilst preserving order

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
