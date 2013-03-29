# from Python
import oauth2 as oauth
import cgi
from datetime import datetime, timedelta
import urlparse
import math

# import datetime

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
from accounts.forms import FinishAuthForm, AuthForm
from django.contrib import messages
from lilib import LIProfile
from accounts.tasks import process_li_profile, process_li_connections

# Prosperime
from accounts.models import Account, Profile, Picture
from careers.models import SavedPath, CareerDecision, Position, SavedPosition, SavedCareer
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
	profile = user.profile
	profile_pic = user.profile.default_profile_pic()
	
	own_profile = False
	queue = None
	viewer_saved_paths = []
	goal_careers = None
	career_decision_position = []

	# career_map = profile.all_careers
	#top_careers = profile.top_careers
	career_map = None
	top_careers = None

	# Convert positions to timeline info
	positions = Position.objects.filter(person=user).select_related('careerDecision')
	positions, start_date, end_date, total_time, current = _prepare_positions_for_timeline(positions)

	# If Own Profile, get extra information
	if int(user_id) == int(request.user.id):
		own_profile = True

		# Your Saved Paths
		saved_path_queryset = SavedPath.objects.filter(owner=request.user).exclude(title='queue')
		viewer_saved_paths = []
		for path in saved_path_queryset:
			viewer_saved_paths.append(_saved_path_to_json(path))

		# Your Goal Careers
		goal_careers_queryset = SavedCareer.objects.filter(owner=request.user).select_related("career")
		goal_careers = []
		for career in goal_careers_queryset:
			goal_careers.append(_saved_career_to_json(career.career))

		# Positions of Interest ('Queue')
		try:
			queue = SavedPath.objects.filter(owner=request.user, title='queue').prefetch_related()
			queue = _saved_path_to_json(queue[0])
		except:
			queue = None

		# Career Decision Prompt
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



	response = {
		'profile':profile,
		'viewer_saved_paths':viewer_saved_paths,
		'profile_pic':profile_pic,
		'positions':positions,
		'current':current,
		'start_date':start_date,
		'end_date':end_date,
		'total_time':total_time,
		# 'career_map':career_map,
		# 'top_careers':top_careers,
		'career_decision_prompt':career_decision_position,
		'own_profile':own_profile,
		'queue':queue,
		'goal_careers':simplejson.dumps(goal_careers),
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
			'entity_name':p.position.entity.name,
			'type':p.position.type,
		})
	formatted_path['positions'] = positions
	return formatted_path

## Takes a career object and returns dict
def _saved_career_to_json(career):

	formatted_career = {
		'title':career.long_name,
		'id':career.id,
	}

	return formatted_career


# Takes a queryset of user's positions and returns 
#	information needed for timeline creation
def _prepare_positions_for_timeline(positions):

	formatted_positions = []
	current = None

	if len(positions)  == 0:
		start_date = None
		total_time = None

	# Process each position
	for pos in positions:

		if pos.start_date: # ignore no start_date

			pos.duration = pos.duration_in_months()

			if pos.title is not None:
				if 'ntern' in pos.title and 'nternational' not in pos.title:
					pos.type = 'internship'

			# Assumption: no end date = current
			if not pos.end_date:
				pos.end_date = "Current"

			# domains = pos.entity.domains.all()
			# if domains:
			# 	pos.domain = domains[0].name
			# else:
			# 	pos.domain = None

			pos.co_name = pos.entity.name
			# pos.pic = pos.entity.default_logo()

			# Educations
			if pos.type == 'education' or pos.title == 'Student':
				if pos.degree is not None and pos.field is not None:
					pos.title = pos.degree + ", " + pos.field
				elif pos.degree is not None:
					pos.title = pos.degree
				elif pos.field is not None:
					pos.title = pos.field
				else:
					pos.title = 'Student' ## Let's just guess 

			# Jobs/Internships
			else:
				if pos.current:
					current = pos

			formatted_positions.append(pos)
	
	
	# Sort by start date
	formatted_positions.sort(key=lambda	 p:p.start_date)
	start_date = formatted_positions[0].start_date
	formatted_positions.reverse()
	total_time = helpers._months_from_now(start_date)
	end_date = datetime.now()

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

def _get_profile_pic(profile):
	pics = Picture.objects.filter(person=profile,status="active").order_by("created")
	if pics.exists():
		return pics[0].pic.__unicode__()
	return None


def fetch_profile(request):

	linkedin_key = '8yb72i9g4zhm'
	linkedin_secret = 'rp6ac7dUxsvJjQpS'

	# ME
	access_token = {
		'oauth_token_secret': "67cbcc33-30bf-423d-b677-92bc3f775559", 
		'oauth_token': '0a0d3a27-5713-439e-a57e-c2f35798b4a5'
	}

	acct_id = "MmD6vhOwE-"
	# set fields to fetch from API
	fields = "(id,public-profile-url)";
	
	# construct url
	api_url = "http://api.linkedin.com/v1/people/id=%s:%s?format=json" % (acct_id,fields,)
	 

	consumer = oauth.Consumer(linkedin_key, linkedin_secret)
	 
	token = oauth.Token(
		key=access_token['oauth_token'], 
		secret=access_token['oauth_token_secret'])

	client = oauth.Client(consumer, token)

	resp, content = client.request(api_url)
	content = content.lstrip('"')
	content = content.rstrip('"')
	print content
	return HttpResponse(simplejson.dumps(content))


def process_public_page(self,user,url):
		# fetch html and soup it
		
		# html = self.get_public_page(url)
		try:
			html = urllib2.urlopen(url)
		except:
			return None
		soup = BeautifulSoup(html)

		# get all profile container divs
		divs = soup.find_all("div","section",id=re.compile("^profile"))

		# loop throuh each div
		for d in divs:
			# identify type
			if d['id'] == 'profile-experience':
				# extract position data
				positions = self.extract_pos_from_public_page(d)
				for p in positions:
					# check to see if a co uniq was returned
					if p['co_uniq_name'] is not None:
						# check to see if new company
						co = self.get_company(name=p['co_uniq_name'])
						if co is None:
							# add new company
							co = self.add_company(name=p['co_uniq_name'])
							# if it's a new company, position must be new as well
							if co is not None:
								self.add_position(user,co,p)
						else:
							pos = self.get_position(user,co,p)
							if pos is None:
								self.add_position(user,co,p)
							
			# handle Education
			elif d['id'] == 'profile-education':
				ed_positions = self.extract_ed_pos_from_public_page(d)
				for p in ed_positions:
					# check to see if new company
					inst = self.get_institution(name=p['inst_name'])
					if inst is None:
						# add new company
						inst = self.add_institution(p)
						# if it's a new company, position must be new as well
						# if inst is not None:
						self.add_ed_position(user,inst,p)
					else:
						# TODO update company
						pos = self.get_position(user,inst,p,type="ed")
						if pos is None:
							self.add_ed_position(user,inst,p)

def extract_pos_from_public_page(self,data):
	# initialize positions array
	positions = []
	# get all position divs
	raw_positions = data.find_all("div","position")
	# loop through each position
	for p in raw_positions:
		# get title of position
		title = p.find("div","postitle").span.contents[0]
		# get unique name of company
		co_uniq_name = p.find("a","company-profile-public")
		if co_uniq_name:
			co_uniq_name = co_uniq_name.get('href')
			m = re.search("(?<=\/company\/)([\w-]*)",co_uniq_name)
			co_uniq_name = m.group(0).strip()
			# print co_uniq_name
			# get start and end dates
			start_date = p.find("abbr","dtstart")
			if start_date is not None:
				start_date = start_date.get('title')
			try:
				end_date = p.find('abbr','dtstamp').get('title')
				current = True
			except:
				current = False

			try:
				end_date = p.find("abbr","dtend").get("title")
			except:
				end_date = None
			# get descriptions
			try:
				descr = p.find("p","description").contents[0]
			except:
				descr = None
			# append to main positions array
			positions.append({'title':title,'co_uniq_name':co_uniq_name,'startDate':start_date,'endDate':end_date,'summary':descr,'isCurrent':current})
	return positions

def extract_ed_pos_from_public_page(self,data):
	# initialize positions array
	positions = []
	# get all position divs
	raw_positions = data.find_all("div","position")
	# loop through each position
	for p in raw_positions:
		inst_uniq_id = p.get('id')
		inst_name = p.h3.contents[0].strip()
		
		try:
			degree = p.find("span","degree").contents[0].strip()
		except:
			degree = None
		try:
			major = p.find("span","major").contents[0].strip()
		except:
			major = None

		try:
			dates = p.find('p','period')
			dates = dates.find_all('abbr')
			start_date = dates[0].get('title')
			if not start_date:
				start_date = None
			end_date = dates[1].get('title')
			if not end_date:
				end_date = None
		except:
			start_date = None
			end_date = None

		positions.append({
			'inst_uniq_id':inst_uniq_id,
			'inst_name':inst_name,
			'degree':degree,
			'fieldOfStudy':major,
			'start_date':start_date,
			'end_date':end_date,
		})
	return positions





