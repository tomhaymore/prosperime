# from Python
import oauth2 as oauth
import cgi
from datetime import datetime, timedelta
import urlparse
import math
# import datetime

# from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout as auth_logout, login as auth_login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import simplejson
from accounts.forms import FinishAuthForm, AuthForm
from django.contrib import messages
from lilib import LIProfile
from accounts.tasks import process_li_profile, process_li_connections

# Prosperime
from accounts.models import Account, Profile, Picture
from careers.models import SavedPath, Career, Position
from entities.models import Entity

def login(request):
	
	# print request.session['_auth_user_backend']
	if request.user.is_authenticated():
		return HttpResponseRedirect('/')
	if request.method == "POST":
		# make sure using proper authentication backend
		request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
		form = AuthForm(request.POST)

		if form.is_valid():
			user = authenticate(username=form.cleaned_data['username'],password=form.cleaned_data['password'])
			if user is not None:
				auth_login(request,user)
				messages.success(request, 'You have successfully logged in.')
				return HttpResponseRedirect('/')
			
	else:
		form = AuthForm()

	return render_to_response('accounts/login.html',{'form':form},context_instance=RequestContext(request))

@login_required
def logout(request):
	auth_logout(request)
	return HttpResponseRedirect('/')

def linkedin_authorize(request):
		
	liparser = LIProfile()
	redirect_url, request_token = liparser.authorize()

	request.session['request_token'] = request_token

	return HttpResponseRedirect(redirect_url)
  
# @login_required
def linkedin_authenticate(request):  
	
	liparser = LIProfile()

	access_token, linkedin_user_info = liparser.authenticate(request.session['request_token'],request.GET['oauth_verifier'])
	
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


def finish_login(request):
	# TODO: redirect if not not authenticated through LinkedIn already
	
	if request.POST:

		# form submitted
		linkedin_user_info = request.session['linkedin_user_info']
		access_token = request.session['access_token']

		form = FinishAuthForm(request.POST)
		
		if form.is_valid():
			username = form.cleaned_data['username']
			email = form.cleaned_data['email']
			password = form.cleaned_data['password']

			# check to see if dormant user already exists
			try: 
				user = User.objects.get(status="dormant",account__uniq_id=linkedin_user_info['id'])
				existing = True
			except:
				# create user
				user = User.objects.create_user(username,email,password)
				user.save()
				existing = False

			# make sure using right backend
			request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
			# log user in
			user = authenticate(username=username,password=password)
			# make sure authentication worked
			if user is not None:
				auth_login(request,user)
			else:
				# somehow authentication failed, redirect with error message
				messages.error(request, 'Something went wrong. Please try again.')
				return render_to_response('accounts/finish_login.html',{'form':form,'error_message':error_message},context_instance=RequestContext(request))


			# update user profile
			# user.profile.full_name = request.session['linkedin_user_info']['firstName'] + " " + request.session['linkedin_user_info']['lastName']		
			user.profile.first_name = linkedin_user_info['firstName']
			user.profile.last_name = linkedin_user_info['lastName']
			user.profile.headline = linkedin_user_info['headline']
			user.profile.save()

			# add pofile picture
			if 'pictureUrl' in linkedin_user_info:
				# _add_profile_pic(user,linkedin_user_info['pictureUrl'])
				li_parser = LIProfile()
				li_parser.add_profile_pic(user,linkedin_user_info['pictureUrl'])

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
			# return HttpResponseRedirect('/search')
			return HttpResponseRedirect('/discover')
	else:
		form = FinishAuthForm()

	return render_to_response('accounts/finish_login.html',{'form':form},context_instance=RequestContext(request))


def finish_link(request):
	# get info for creating an account
	linkedin_user_info = request.session['linkedin_user_info']
	access_token = request.session['access_token']

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

	messages.success(request, 'Your LinkedIn account has been successfully linked. Please refresh the page to see changes.')

	return HttpResponseRedirect('/home')

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
	
# View for invidiual profiles
@login_required
def profile(request, user_id):

	user = User.objects.get(id=user_id)
	profile = Profile.objects.get(user=user)
	saved_paths = SavedPath.objects.filter(owner=user)
	profile_pic = _get_profile_pic(profile)
	viewer_saved_paths = SavedPath.objects.filter(owner=request.user)

	# Do position processing here!
	positions = Position.objects.filter(person=user)
	ed_list = []
	org_list = []

	# declare vars before in case no positions
	current = None

	for pos in positions:
		pos.duration = pos.duration_in_months()

	
		# Assumption: no end date = current
		if not pos.end_date:
			pos.end_date = "Current"

		# Process domains
		## NO DOMAINS RIGHT NOW -- UNUSED
		# domains = pos.entity.domains.all()
		# if domains:
		# 	domain = domains[0].name
		# 	pos.co_name = domain + " company"
		# else:
		# 	domain = None
		# 	pos.co_name = pos.entity.name

		pos.co_name = pos.entity.name
		pos.domain=None

		# Process education positions
		if pos.type == 'education' or pos.title == 'Student':
			if pos.degree is not None and pos.field is not None:
				pos.title = pos.degree + ", " + pos.field
			elif pos.degree is not None:
				pos.title = pos.degree
			elif pos.field is not None:
				pos.title = pos.field
			else:
				pos.title = None
			ed_list.insert(0, pos)
		else:

			if pos.title:
				print pos.title + ', ' + pos.co_name

			# Assumption: ignore if no start-date, crappy data
			if pos.start_date:
				org_list.insert(0, pos)
			if pos.current:
				current = pos
			# else:
			# 	print 'ignoring: ' + pos.type

	# Still need to uniqify this data!
	# will do so O(n2) but hey, these are small datasets
	ed_list = _uniqify(ed_list)
	org_list = _uniqify(org_list)

	# Now, prepare for timeline
	# First, sort by start_date
	## ?? org_list.sort(key=lambda x: (int(x.start_date)[:3] + int(x.start_date)[0:2]))

	if len(org_list) == 0:
		# then we have problem
		start_date = total_time = end_date = compress = None
	else:	
		start_date = org_list[len(org_list)-1].start_date
		total_time = _months_from_now(start_date)
		end_date = datetime.datetime.now()

		if total_time > 200: 
		# 200 is an arbitrary constant that seems to fit my laptop screen well
			total_time = int(math.ceil(total_time/2))
			for pos in org_list:
				pos.duration = int(math.ceil(pos.duration/2))
			compress = True
		else:
			compress = False

	# we have this data... but what to do with it?
	career_map = profile.all_careers

	return render_to_response('accounts/profile.html', {'profile':profile, 'saved_paths': saved_paths, 'viewer_saved_paths':viewer_saved_paths, 'profile_pic': profile_pic, 'orgs':org_list, 'ed':ed_list, 'current':current, 'start_date':start_date, 'end_date':end_date, 'total_time': total_time, 'compress': compress, 'career_map': career_map}, context_instance=RequestContext(request))
	
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

	return render_to_response('accounts/profile_org.html', response, context_instance=RequestContext(request))

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

# Returns # months difference between start_date and now
def _months_from_now(start_date):
	now = datetime.datetime.now()
	return (12 * (now.year - start_date.year)) + (now.month - start_date.month)

# taken straight from viz.js
def _months_difference(start_mo, start_yr, end_mo, end_yr, compress, round):
	diff = 12 * (end_yr - start_yr)
	diff += end_mo - start_mo

	if compress:
		diff /= 2
		if round == 'upper':
			diff = math.ceil(diff)
		if round == 'lower':
			diff = math.floor(diff)

	return diff

def _get_profile_pic(profile):
	pics = Picture.objects.filter(person=profile,status="active").order_by("created")
	if pics.exists():
		return pics[0].pic.__unicode__()
	return None


