# from Python
import oauth2 as oauth
import cgi
from datetime import datetime, timedelta
import urlparse
import math

# import datetime

import random

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
from careers.models import SavedPath, CareerDecision, Position
from entities.models import Entity

import utilities.helpers as helpers


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

def terms(request):

	return render_to_response('terms.html',context_instance=RequestContext(request))

def privacy(request):

	return render_to_response('privacy.html',context_instance=RequestContext(request))

def copyright(request):

	return render_to_response('copyright.html',context_instance=RequestContext(request))

@login_required
def logout(request):
	auth_logout(request)
	return HttpResponseRedirect('/welcome')

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
			# grab cleaned values from form
			username = form.cleaned_data['username']
			email = form.cleaned_data['email']
			location = form.cleaned_data['location']
			headline = form.cleaned_data['headline']
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
			user.profile.location = location
			# check to see if user provided a headline
			if headline:
				user.profile.headline = headline
			else:
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
			return HttpResponseRedirect('/personalize/careers/')
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
		'profile': {
			'status':profile_task.ready(),
			'id':profile_task.id
			},
		'connections': {
			'status':connections_task.ready(),
			'id':connections_task.id
			}
	}

	messages.success(request, 'Your LinkedIn account has been successfully linked. Please refresh the page to see changes.')

	return HttpResponseRedirect('/personalize/careers/')

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
	# profile = Profile.objects.get(user=user)
	profile = user.profile
	# get careers
	career_dict = {}
	for p in user.positions.all():
		for c in p.careers.all():
			if c in career_dict:
				career_dict[c] += 1
			else:
				career_dict[c] = 1

	saved_paths = SavedPath.objects.filter(owner=user)
	# saved_paths = user.saved_path.all()
	# profile_pic = _get_profile_pic(profile)
	profile_pic = user.profile.default_profile_pic()
	viewer_saved_paths = SavedPath.objects.filter(owner=request.user)

	# Do position processing here!

	# CHECK THAT THIS WORKS
	positions = Position.objects.filter(person=user).select_related('careerDecision')

	ed_list = []
	org_list = []

	# declare vars before in case no positions
	current = None

	for pos in positions:
		pos.duration = pos.duration_in_months()

		if pos.title is not None:
			if 'ntern' in pos.title and 'nternational' not in pos.title:
				pos.type = 'internship'

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
		pos.pic = pos.entity.default_logo()
		# Process education positions
		if pos.type == 'education' or pos.title == 'Student':
			if pos.degree is not None and pos.field is not None:
				pos.title = pos.degree + ", " + pos.field
			elif pos.degree is not None:
				pos.title = pos.degree
			elif pos.field is not None:
				pos.title = pos.field
			else:
				pos.title = 'Student' ## Let's just guess 
			if pos.start_date:
				ed_list.insert(0, pos)
		else:

			# Assumption: ignore if no start-date, crappy data
			if pos.start_date:
				org_list.insert(0, pos)
			if pos.current:
				current = pos




	# will do so O(n2) but hey, these are small 
	ed_list = _uniqify(ed_list)
	org_list = _uniqify(org_list)

	# we have this data... but what to do with it?
	#career_map = profile.all_careers
	#top_careers = profile.top_careers
	career_map = None
	top_careers = None

	# Check for CareerDecision
	if user.id == request.user.id:
		career_decision = _get_career_decision_prompt_position(top_careers, positions, profile)
		if career_decision is None:
			career_decision_position = None;
		else:
			career_decision_position = {
				'id':career_decision.id,
				'title':career_decision.title,
				'co_name':career_decision.entity.name,
				'type':career_decision.type,
			}
	else:
		career_decision_position = None;

	positions = ed_list + org_list

	if len(positions)  == 0:
		start_date = None
		total_time = None
	else:

		for p in positions:
			if p.start_date is None:
				positions.remove(p)

		# Sort by start date
		positions.sort(key=lambda	 p:p.start_date)
		start_date = positions[0].start_date
		positions.reverse()
		total_time = helpers._months_from_now(start_date)

		end_date = datetime.now()

		if total_time > 200: 
		# 200 is an arbitrary constant that seems to fit my laptop screen well
			total_time = int(math.ceil(total_time/2))
			for pos in org_list:
				pos.duration = int(math.ceil(pos.duration/2))
			compress = True
		else:
			compress = False


	end_date = datetime.now()
	compress = None

	return render_to_response('accounts/profile.html', {'profile':profile,'careers':career_dict,'saved_paths': saved_paths, 'viewer_saved_paths':viewer_saved_paths, 'profile_pic': profile_pic, 'orgs':org_list, 'ed':ed_list, 'current':current, 'start_date':start_date, 'end_date':end_date, 'total_time': total_time, 'compress': compress, 'career_map': career_map, 'top_careers':top_careers, 'career_decision_prompt':career_decision_position, 'positions':positions}, context_instance=RequestContext(request))
	
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

def _get_profile_pic(profile):
	pics = Picture.objects.filter(person=profile,status="active").order_by("created")
	if pics.exists():
		return pics[0].pic.__unicode__()
	return None


