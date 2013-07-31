# Python
import datetime
from datetime import timedelta
import json
import logging

# Django
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.utils import simplejson
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import Count, Q


# Prosperime
from entities.models import Entity, Industry, Region
from careers.models import SavedPath, SavedPosition, Position, Career, GoalPosition, SavedCareer, IdealPosition, CareerDecision, SavedIndustry
from accounts.models import Profile
from social.models import Comment

import careers.careerlib as careerlib
from careers.seedlib import SeedBase
from social.feedlib import FeedBase
import social.feedlib as feedlib

import utilities.helpers as helpers

logger = logging.getLogger(__name__)

def chrome_api(request):

	print request.GET.get("foo")


	print "\n\n"

	request.GET.getlist("data[]")

	print "\n\n"


	response = {"foo":"bar"}
	return HttpResponse(json.dumps(response))

def internships_simple(request):

	data = {"foo":"bar"}
	return render_to_response("careers/internships_simple.html", data, context_instance = RequestContext(request))

# Clayton - DEV
def internships(request):

	## WHAT TO SHOW IF NOT LOGGED IN?
	# Figure out which school to get
	# users_school = request.user.positions.filter(type="education")
	# if users_school:
	# 	school_id = 2368
	# 	# school_id = users_school[0].id
	# else:
	# 	## TODO... what to do here?
	# 	school_id = 2116 # "University of Pennsylvania"
	# 	# 2368 = "Stanford University" (one of them)


	# data = cache.get("feed_me_some_terns_"+str(school_id))
	# if data is not None:
	# 	data["cache"] = "hit"
	# 	data["school_id"] = school_id
	# 	return render_to_response("careers/d3.html", data, context_instance=RequestContext(request))
	# else:
	# 	return render_to_response("careers/d3.html", {"cache":"miss", "school_id":school_id}, context_instance=RequestContext(request))

	## IDEA 3: MAP TOP SCHOOLS -> COMMON MAJORS -> ENTITIES
	

	data = {"foo":"bar"}
	return render_to_response("careers/internships.html", data, context_instance=RequestContext(request))


def get_internship_data(request):

	### GET n-MOST COMMON INTERNSHIP ENTITIES FOR GIVEN SCHOOL ###

## Housekeeping ##
	# TODO: get the alternate ID and positions for each school
	school_id = request.GET.get("school_id")

	# Get params, create cache suffix (for cache storage/lookup)
	if request.GET.get("entity_id"):
		entity_id = request.GET.get("entity_id")
		cache_suffix = str(school_id) + "_" + str(entity_id)
	else:
		entity_id = None
		cache_suffix = str(school_id)

	# Look in the cache... may not be the best idea for this
	response = cache.get("feed_me_some_terns_" + cache_suffix)
	if response is not None:
		return HttpResponse(json.dumps(response))


## Base Data Pulls ##

	# Get all internship positions
	all_internships = Position.objects.filter(Q(title__icontains="intern") | Q(title__icontains="summer")).select_related("person", "entity")
	# Get all Users who held them
	all_interns = [p.person for p in all_internships]
	# Get all college student Users from given school
	college_students = [p.person for p in Position.objects.filter(type="education", entity__id=school_id).exclude(ideal_position__major=None).select_related("person")]
	
	if entity_id:
		# get interns from entity + school
		people_who_worked_at_entity = [i.person for i in all_internships.filter(entity__id=entity_id, person__in=college_students)]
		# get majors
		majors = Position.objects.filter(person__in=people_who_worked_at_entity, type="education").exclude(field=None).exclude(ideal_position=None).exclude(ideal_position__major=None)
		# get frequences
		frequencies = {}
		for m in majors:
			if m.ideal_position.major in frequencies:
				frequencies[m.ideal_position.major] += 1
			else:
				frequencies[m.ideal_position.major] = 1
		# get majors proportions from frequences for pie chart
		majors_proportions = []
		total_num_majors = len(majors)
		rest = total_num_majors
		counter = 1
		for m in frequencies:
			majors_proportions.append({
				"key":m,
				"prop":(float(frequencies[m]) / total_num_majors),
				"id":counter
			})
			rest -= frequencies[m]
			counter += 1

		# Add the remainder (if there is one)
		if rest > 1:
			majors_proportions.append({"key":"Rest", "prop":float(rest) / total_num_majors, "index":counter})

		from pprint import pprint
		pprint(majors_proportions)

		response = {
			"majors":majors_proportions,
			"school_id":school_id,
			"entity_id":entity_id,
			"intern_titles":[t.title for t in all_internships.filter(person__in=college_students, entity__id=entity_id)]
		}



	else:
		# majors = Position.objects.filter(type="education", person__in=college_students).exclude(ideal_position__major=None).select_related("ideal_position")
		# # Map most common
		# majors_map = {}
		# for m in majors:
		# 	if m.ideal_position.major in majors_map:
		# 		majors_map[m.ideal_position.major] += 1
		# 	else:
		# 		majors_map[m.ideal_position.major] = 1

		# # Get 8 most common majors
		# from heapq import nlargest; from operator import itemgetter;
		# most_common_majors = nlargest(8, majors_map.iteritems(), itemgetter(1))

		# Get most common entities
		intersection = set(all_interns).intersection(set(college_students))
		print "Drawing from pool of: " + str(len(intersection))
		# Maps {entity_name: frequency}
		frequencies = {}
		# Maps {entity_name: entity_id}
		entities_map = {} # Sorry... this is ugly but I'm rushing
		internship_counter = 0
		for user in intersection:
			# Exclude internships at the college itself
			internships = all_internships.filter(person=user).exclude(entity__id=school_id)
			for i in internships:
				internship_counter += 1
				if i.entity.name is not None:
					if i.entity.name in frequencies:
						frequencies[i.entity.name] += 1
					else:
						frequencies[i.entity.name] = 1
						entities_map[i.entity.name] = i.entity.id
		
		from pprint import pprint
		pprint(frequencies)


		# Sort using heap queue (it's fast)
		from heapq import nlargest; from operator import itemgetter; 
		most_common_entities = nlargest(8, frequencies.iteritems(), itemgetter(1))

		entities_proportions = []
		total_num_entities = internship_counter # just for code legibility
		rest = total_num_entities

		for e in most_common_entities:
			entities_proportions.append({
				"key":str(e[0]),
				"prop":(float(e[1]) / total_num_entities),
				"id":entities_map[e[0]]
			})
			rest -= e[1]

		if rest > 1:
			entities_proportions.append({"key":"Other", "prop":(float(rest) / total_num_entities), "id":-1})


		response = {
			"school_id":school_id,
			"entities":entities_proportions,
			"school_name":Entity.objects.get(id=school_id).name
		}


	cache.set("feed_me_some_terns_" + cache_suffix, response, 1000)


	return HttpResponse(json.dumps(response))


######################################################
################## CORE VIEWS ########################
######################################################

# @login_required
def old_majors(request):


	# try to get from cache
	# data = cache.get("majors_viz_"+str(request.user.id))
	data = cache.get("majors_viz")

	# test if cache worked
	if data is not None:
		data["cache"] = "hit"
		return render_to_response("careers/d3.html",data,context_instance=RequestContext(request))
	else:
		data = {"cache":"miss"}

	return render_to_response("careers/d3.html",data,context_instance=RequestContext(request))

def majors_v4(request):
	# check for meta
	if request.META and 'HTTP_USER_AGENT' in request.META:

		import re
		
		res = re.search("MSIE 8.0",request.META["HTTP_USER_AGENT"])
		if res:
			return render_to_response("no_ie8.html",context_instance=RequestContext(request))
	data = {}
	import accounts.tasks as tasks
	data['majors'] = cache.get("majors_viz_v3")
	if data['majors'] is not None:
		data["cache"] = "hit"


	if "tasks" in request.session:
		logger.info("tasks in session")
		profile_task = tasks.process_li_profile.AsyncResult(request.session['tasks']['profile'])
		connections_task = tasks.process_li_connections.AsyncResult(request.session['tasks']['connections'])
		if profile_task.status != 'SUCCESS' or connections_task.status != 'SUCCESS':
			data['tasks'] = True
		if profile_task.status != 'SUCCESS':
			data['profile_task_id'] = request.session['tasks']['profile']
		else:
			data['profile_task_id'] = None
		if connections_task.status != 'SUCCESS':
			data['connections_task_id'] = request.session['tasks']['connections']
		else:
			data['connections_task_id'] = None
	else:
		logger.info('no tasks in session')
		data['tasks'] = False
		data['profile_task_id'] = None
		data['connections_task_id'] = None

	# test if cache worked
	if data["majors"]:
		return render_to_response("careers/majors_v4.html",data,context_instance=RequestContext(request))
	else:
		data["cache"] = "miss"

		return render_to_response("careers/majors_v4.html",data,context_instance=RequestContext(request))

def majors_v3(request):
	# check for meta
	if request.META and 'HTTP_USER_AGENT' in request.META:

		import re
		
		res = re.search("MSIE 8.0",request.META["HTTP_USER_AGENT"])
		if res:
			return render_to_response("no_ie8.html",context_instance=RequestContext(request))
	data = {}
	import accounts.tasks as tasks
	data['majors'] = cache.get("majors_viz_v3")
	if data['majors'] is not None:
		data["cache"] = "hit"


	if "tasks" in request.session:
		logger.info("tasks in session")
		profile_task = tasks.process_li_profile.AsyncResult(request.session['tasks']['profile'])
		connections_task = tasks.process_li_connections.AsyncResult(request.session['tasks']['connections'])
		if profile_task.status != 'SUCCESS' or connections_task.status != 'SUCCESS':
			data['tasks'] = True
		if profile_task.status != 'SUCCESS':
			data['profile_task_id'] = request.session['tasks']['profile']
		else:
			data['profile_task_id'] = None
		if connections_task.status != 'SUCCESS':
			data['connections_task_id'] = request.session['tasks']['connections']
		else:
			data['connections_task_id'] = None
	else:
		logger.info('no tasks in session')
		data['tasks'] = False
		data['profile_task_id'] = None
		data['connections_task_id'] = None

	# test if cache worked
	if data["majors"]:
		return render_to_response("careers/majors_v3.html",data,context_instance=RequestContext(request))
	else:
		data["cache"] = "miss"

		return render_to_response("careers/majors_v3.html",data,context_instance=RequestContext(request))

@login_required
def test_majors_v3(request):

	path = careerlib.CareerPathBase()
	data = path.get_majors_data_v3()

	return render_to_response("careers/test_majors.html",data,context_instance=RequestContext(request))

def majors(request):
	# try to get from cache
	# data = cache.get("majors_viz_"`+str(request.user.id))
	data = {}
	import accounts.tasks as tasks
	data['majors'] = cache.get("majors_viz")
	if data['majors'] is not None:
		data["cache"] = "hit"


	if "tasks" in request.session:
		logger.info("tasks in session")
		profile_task = tasks.process_li_profile.AsyncResult(request.session['tasks']['profile'])
		connections_task = tasks.process_li_connections.AsyncResult(request.session['tasks']['connections'])
		if profile_task.status != 'SUCCESS' or connections_task.status != 'SUCCESS':
			data['tasks'] = True
		if profile_task.status != 'SUCCESS':
			data['profile_task_id'] = request.session['tasks']['profile']
		else:
			data['profile_task_id'] = None
		if connections_task.status != 'SUCCESS':
			data['connections_task_id'] = request.session['tasks']['connections']
		else:
			data['connections_task_id'] = None
	else:
		logger.info('no tasks in session')
		data['tasks'] = False
		data['profile_task_id'] = None
		data['connections_task_id'] = None

	# test if cache worked
	if data["majors"]:

		return render_to_response("careers/majors.html",data,context_instance=RequestContext(request))
	else:
		data = {"cache":"miss"}


	return render_to_response("careers/majors.html",data,context_instance=RequestContext(request))


def home(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/welcome/')
	else:
		return HttpResponseRedirect('/majors/')
	# data = {}
	# user = request.user

	# # data['user_careers'] = Career.objects.filter(positions__person__id=user.id)
	# # data['saved_paths'] = SavedPath.objects.filter(owner=user)
	# data['saved_careers'] = request.user.saved_careers.all()
	# data['saved_jobs'] = GoalPosition.objects.filter(owner=user)
	# data['career_decisions'] = CareerDecision.objects.all()

	# fetch data 
	# educations = Position.objects.filter(person=request.user,type="education").order_by("start_date")
	# positions = Position.objects.filter(person=request.user).exclude(type="education").order_by("-start_date")
	# locations = Region.objects.filter(people=request.user)
	# goals = GoalPosition.objects.filter(owner=request.user)
	# user = request.user

	# data = {
	# 	'educations' : educations,
	# 	'positions' : positions,
	# 	'locations': locations,
	# 	'goals' : goals,
	# 	'user' : request.user,
	# 	'latest_ed' : educations[0].ideal_position.title[:5],
	# 	'duration': careerlib.get_prof_longevity(user)
	# }


	# if "tasks" in request.session:
	# 	data['tasks'] = True
	# 	data['profile_task_id'] = request.session['tasks']['profile']
	# 	data['connections_task_id'] = request.session['tasks']['connections']
	# else:
	# 	data['tasks'] = False
	# 	data['profile_task_id'] = None
	# 	data['connections_task_id'] = None

	return render_to_response('home_v5.html',context_instance=RequestContext(request))


# @login_required

def major(request,major_id):
	"""
	view for detailed information on a particular major
	"""
	
	# get degree
	major = IdealPosition.objects.get(pk=major_id)
	# instantiate career lib class
	C = careerlib.CareerPathBase()

	# check if user is authenticated
	if not request.user.is_authenticated():
		data = {
			'major':major,
			'major_data':C.get_major_data(major)
		}
		return render_to_response('careers/major_profile_v3.html',data,context_instance=RequestContext(request)) 
	
	# get major data
	major_data = C.get_major_data(major,request.user)
	
	# get connections and schools
	# connections = [c.id for c in request.user.profile.connections.all()]
	# schools = Entity.objects.filter(Q(li_type="school")|Q(li_type="educational")).filter(positions__person=request.user).annotate(number=Count("positions"))

	# # expand universities array
	# for s in schools:
	# 	s.starting = C.get_starting_jobs_from_school(major=major,user=request.user) 
	# 	s.current = C.get_current_jobs_from_school(major=major,user=request.user)
	# 	s.number = len(IdealPosition.objects.filter(Q(position__person__id__in=connections)|Q(position__entity__in=schools)).annotate(num=Count("position__person")))

	# init array
	# paths  = []

	# users = User.objects.filter(Q(id__in=connections)|Q(positions__entity__id=schools)).filter(positions__ideal_position=major).distinct()
	# for u in users:

	# 	first_and_last_positions = u.profile.first_and_last_positions() 
	# 	if first_and_last_positions is not None:
	# 		paths.append({"id":u.id, "full_name":u.profile.full_name(), "profile_pic":u.profile.default_profile_pic(), "first":first_and_last_positions[0].title + " at " + first_and_last_positions[0].entity.name, "latest":first_and_last_positions[1].title + " at " + first_and_last_positions[1].entity.name})

	data = {
		"paths": major_data['people'],
		"major": major,
		"schools": major_data['schools'],
		"number": len(major_data['people'])
		# "starting": major_data['first_jobs'][0],
		# "current": major_data['current_jobs'][0]
	}
	if major_data['first_jobs']:
		data['starting'] = major_data['first_jobs'][0]
	else:
		data['starting'] = None

	if major_data['current_jobs']:
		data['current'] = major_data['current_jobs'][0]
	else:
		data['current'] = None

	if "tasks" in request.session:
		data['tasks'] = True
		data['profile_task_id'] = request.session['tasks']['profile']
		data['connections_task_id'] = request.session['tasks']['connections']
	else:
		data['tasks'] = False
		data['profile_task_id'] = None
		data['connections_task_id'] = None

	return render_to_response('careers/major_profile_v3.html',data,context_instance=RequestContext(request))

def get_school_fragment(request,school_id=None):
	c = careerlib.CareerPathBase()
	f = feedlib.FeedBase()
	# grab list of all schools affiliated with user
	schools = [e for e in Entity.objects.filter(positions__person=request.user,positions__type="education").distinct()]
	# if particular school selected, get details for just that school
	if school_id:
		school = Entity.object.get(pk=school_id)
		degrees = [{'id':p.id,'title':p.title,'long_title':p.long_title,'description':p.description} for p in IdealPosition.objects.filter(cat="ed",position__entity=school).annotate(pop=Count("position__id")).distinct().order_by("-pop")[:5]]
		# degrees = [p.degree for p in Position.objects.filter(entity=school,type="education").exclude(degree=None).distinct()]
		# careers = c.get_careers_in_schools([school])
		jobs = c.get_first_jobs_from_schools([school]),
		paths = c.get_paths_from_schools([school])
	else:
		school = None
		degrees = [{'id':p.id,'title':p.title,'long_title':p.long_title,'description':p.description} for p in IdealPosition.objects.filter(cat="ed",position__entity__in=schools).annotate(pop=Count("position__id")).distinct().order_by("-pop")[:5]]
		# degrees = [p.degree for p in Position.objects.filter(entity__in=schools,type="education").exclude(degree=None).distinct()]
		# careers = c.get_careers_in_schools(schools)
		# jobs = c.get_first_jobs_from_schools(schools),
		paths = c.get_paths_from_schools(schools)

	# get updates for degrees
	for d in degrees:
		d['updates'] = f.get_ideal_updates(request.user,d['id'])

	data = {
		'school':school,
		'schools':schools,
		'degrees':degrees,
		# 'careers':careers
		# 'jobs':jobs,
		'paths':paths
	}
	print 'hello'
	return render_to_response("careers/home_school_fragment.html",data,context_instance=RequestContext(request))

def get_feed_fragment(request):
	feeder = FeedBase() 
	feed = feeder.get_univ_feed(request.user)

	data = {
		'feed':feed
	}

	return render_to_response("social/home_feed_fragment.html",data,context_instance=RequestContext(request))

def schools(request):
	return render_to_response("schools.html", context_instance=RequestContext(request))

def test_ideal_paths(request):

	# verify GET has right parameters
	if request.GET.getlist('ideal_id'):

		ideal_pos_id = request.GET.getlist('ideal_id')[0]

		# from careers.positionlib import IdealPositionBase
		# ideal_pos_lib = IdealPositionBase()

		# check cache for path information
		paths = cache.get('get_ideal_paths'+'_'+str(ideal_pos_id))
		if paths is None:
			# cache expired, retrieve anew
			from careers.positionlib import IdealPositionBase
			ideal_pos_lib = IdealPositionBase()

			paths = ideal_pos_lib.get_ideal_paths(ideal_pos_id)

		return render_to_response('careers/test_ideal_paths.html',{'paths':paths},context_instance=RequestContext(request))



def progress(request):

# <<<<<<< HEAD
# 	applicable_positions = IdealPosition.objects.filter(level=4).annotate(pop=Count('position__id')).order_by("-pop")
# =======
	# ghetto way of finding positions that we can give info on
	# applicable_positions = Position.objects.filter(ideal_position__level=4)
	applicable_positions = IdealPosition.objects.annotate(pop=Count('position__id')).filter(level=4,pop__gte=3).order_by("-pop")[:10]
	# ideal_positions = []
	# for a in applicable_positions:
	# 	if a.ideal_position not in ideal_positions:
	# 		ideal_positions.append(a.ideal_position)

	options = [{'title':i.title,'ideal_id':i.id} for i in applicable_positions]

	# If we know user, get existing pos
	if request.user.is_authenticated():
		formatted_positions = [{'title':p.title, 'id':p.id, 'entity_name':p.entity.name, 'ideal_id':p.ideal_position.id} for p in Position.objects.filter(person=request.user).exclude(ideal_position=None).select_related("entity")]
	# Else, no existing pos
	else:
		formatted_positions = []


	owner_positions = self.user.positions.all().order_by('-start_date').exclude(type="education")
	if owner_positions.exists():
		owner_current_position = {"title":owner_positions[0].title, "entity_id":owner_positions[0].id, "entity_logo":owner_positions[0].default_logo()}

	else:
		owner_current_position = None

	data = {
		"authenticated":request.user.is_authenticated(),
		"options":options,
		"positions":json.dumps(formatted_positions)
	}

	return render_to_response("careers/on_track.html", data, context_instance=RequestContext(request))

# DEPRECATED: new code in Accounts.views
def add_progress_detail(request):
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
			elif form.cleaned_data['type'] == "position":
				# set up initial data
				response['data'] = {
					'start_date':form.cleaned_data['start_date'].year,
					'end_date':form.cleaned_data['end_date'].year
				}
				# see if we can map position
				pos = Object()
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

@login_required
def build(request):

	path_title = "Untitled" ## this should default if no title
	
	# V3 EDIT - only latest pos and ed
	current_positions = []
	latest_position = request.user.profile.latest_position_with_ideal()
	educations = request.user.profile.educations()
	
	if latest_position is not None:
		current_positions.append({"pos_id":latest_position.id, "ideal_id": latest_position.ideal_position.id, 'title':latest_position.title, 'entity_name':latest_position.entity.name})
	if educations is not None:
		for ed in educations:
			if ed.ideal_position is not None:
				current_positions.append({"pos_id":ed.id, "ideal_id": ed.ideal_position.id, 'title':ed.title, 'entity_name':ed.entity.name})
	

	# all_positions = Position.objects.filter(person=request.user).values("id", "ideal_position__id", "title", "entity__name")
	# for p in all_positions:
	# 	current_positions.append({"pos_id": p["id"], "ideal_id": p["ideal_position__id"], "title":p["title"], "entity_name":p["entity__name"]})

	# for e in educations:
	# 	current_positions.append({'pos_id':e.id,'ideal_id':e.ideal_position_id,'title':e.title,'entity_name':e.entity.name})
	
	# eligible_alternates = Position.objects.filter().exclude(Q(type="education") | Q(ideal_position=None)).order_by("title").select_related("entity", "ideal_position")
	# alternate_starting_points = []
	# for e in eligible_alternates:
	# 	alternate_starting_points.append({"pos_id":e.id, "ideal_id":e.ideal_position.id, "title":e.title, 'entity_name':e.entity.name})

	alternate_starting_points = [{"pos_id":e.id, "ideal_id":e.ideal_position.id, "title":e.title, 'entity_name':e.entity.name} for e in Position.objects.filter().exclude(Q(type="education") | Q(ideal_position=None)).order_by("title").select_related("entity", "ideal_position")]

	data = {
		'title':path_title,
		'current_positions':current_positions,
		'current_positions_json':json.dumps(current_positions),
		'path_id':-1,
		'path_steps':json.dumps(None),
		'viewer_is_owner':"true",
		'alternate_starting_points':alternate_starting_points,
	}

	return render_to_response("careers/build3.html", data, context_instance=RequestContext(request))

@login_required
def build_v2(request):

	path_title = "Untitled" ## this should default if no title

	# latest_position = request.user.profile.latest_position()
	educations = request.user.profile.educations()

	current_positions = []
	all_positions = Position.objects.filter(person=request.user).values("id", "ideal_position__id", "title", "entity__name")
	for p in all_positions:
		current_positions.append({"pos_id": p["id"], "ideal_id": p["ideal_position__id"], "title":p["title"], "entity_name":p["entity__name"]})
	# current_positions.append({'pos_id':latest_position.id,'ideal_id':latest_position.ideal_position_id,'title':str(latest_position.title),'entity_name':str(latest_position.entity.name)})

	# for e in educations:
	# 	current_positions.append({'pos_id':e.id,'ideal_id':e.ideal_position_id,'title':e.title,'entity_name':e.entity.name})
	

	data = {
		'title':path_title,
		'current_positions':current_positions,
		'current_positions_json':json.dumps(current_positions),
		'path_id':-1,
		'path_steps':None,
		'viewer_is_owner':"true",
	}

	return render_to_response("careers/build_v2.html", data, context_instance=RequestContext(request))


@login_required
def modify_saved_path(request,id):

	# get path object
	path = SavedPath.objects.get(pk=id)

	# initiate array for steps in saved path
	path_steps = []
	
	# loop through saved steps in path, add as dicts to array
	for p in path.positions.all():
		path_steps.append({'pos_id':p.id,'ideal_id':p.ideal_position_id,'title':p.title,'entity_name':p.entity.name})

	# get latest position and educations
	latest_position = request.user.profile.latest_position()
	educations = request.user.profile.educations()

	# add to current positions
	current_positions = []
	current_positions.append({'pos_id':latest_position.id,'ideal_id':latest_position.ideal_position_id,'title':str(latest_position.title),'entity_name':str(latest_position.entity.name)})

	for e in educations:
		current_positions.append({'pos_id':e.id,'ideal_id':e.ideal_position_id,'title':str(e.title),'entity_name':str(e.entity.name)})
	
	# get all comments on path
	comments = [{'body':c.body, 'profile_pic':c.owner.profile.default_profile_pic(), 'date_created':helpers._formatted_date(c.created), 'user_name':c.owner.profile.full_name(), 'user_id':c.owner.id} for c in Comment.objects.filter(path=path)]


	# for select new position dropdown	
	eligible_alternates = Position.objects.filter().exclude(type="education").exclude(ideal_position=None).order_by("title").select_related("entity", "ideal_position")
	alternate_starting_points = []
	for e in eligible_alternates:
		alternate_starting_points.append({"pos_id":e.id, "ideal_id":e.ideal_position.id, "title":e.title, 'entity_name':e.entity.name})


	# collect data for template
	data = {
		'path_steps':json.dumps(path_steps),
		'current_positions':current_positions,
		'current_positions_json':json.dumps(current_positions),
		'path_id':path.id,
		'title':path.title,
		'comments':comments,
		'alternate_starting_points':alternate_starting_points,
	}


	# If not your path, redirect to path view (rather than build)
	if request.user.id != path.owner.id:
		data['user_name'] = path.owner.profile.full_name()
		data['user_id'] = path.owner.id 
		return render_to_response("careers/path.html",data ,context_instance=RequestContext(request))



	return render_to_response("careers/build3.html", data, context_instance=RequestContext(request))


@login_required
def viewPath(request,path_id):

	path = SavedPath.objects.get(id=path_id)
	path_steps = []
	for p in path.positions.all():
		path_steps.append({'pos_id':p.id,'ideal_id':p.ideal_position_id,'title':p.title,'entity_name':p.entity.name})

	data = {
		'user_name':path.owner.profile.full_name(),
		'user_id':path.owner.id,
		'path_id':path_id,
		'title':path.title,
		'comments':[{'body':c.body, 'profile_pic':c.owner.profile.default_profile_pic(), 'date_created':helpers._formatted_date(c.created), 'user_name':c.owner.profile.full_name(), 'user_id':c.owner.id} for c in Comment.objects.filter(path=path)],
		'path_steps':json.dumps(path_steps),
	}

	return render_to_response("careers/path.html", data, context_instance=RequestContext(request))


@login_required
def plan(request,id=None):
	# check to see if viewing a specific position
	from careers.positionlib import IdealPositionBase
	if request.GET.getlist('ideal'):
		id = IdealPosition.objects.filter(title=request.GET['ideal'])[0].id
	if id:
		ideal_pos = IdealPosition.objects.get(pk=id)

		ideal_pos_lib = IdealPositionBase()
		paths = ideal_pos_lib.get_paths_to_ideal_position(ideal_pos.id)
		matching_users = ideal_pos_lib.get_users_matching_ideal_path([ideal_pos.id])
		data = {
			'ideal_pos': ideal_pos,
			'paths': paths,
			'goal_positions': None
		}

	else:

		goal_positions = request.user.goal_position.all()

		data = {
			'ideal_pos':None,
			'paths':None,
			'goal_positions':goal_positions
		}
	return render_to_response("careers/plan.html", data, context_instance=RequestContext(request))

@login_required
def feed(request):
	data = {}

	profile = request.user.profile

	feedBase= FeedBase()
	feed = feedBase.get_univ_feed(request.user)

	for f in feed:
		f["stub"] = json.dumps(f["stub"])
		f["body"] = json.dumps(f["body"])
		f["date"] = helpers._formatted_date(f["date"])
		
	# seedbase returns filenames for relevant people
	seed_base = SeedBase()
	filenames = seed_base.get_seeds(request.user)

	# load json files and send to template
	seed_data = []
	print filenames
	for f in filenames:
		try:
			json_person = open(f)
		except IOError, e:
			print str(e)
		except e:
			print e
		data = json.load(json_person)
		seed_data.append(data)
		json_person.close()

	data["seeds"] = json.dumps(seed_data)
	data["user_profile_pic"] = profile.default_profile_pic()
	data["user_id"] = request.user.id
	data["feed"] = feed
	return render_to_response("careers/feed.html", data, context_instance=RequestContext(request))


@login_required
def next(request):
	data = {}

	# Get params
	if request.GET.getlist('i1'):
		ind_1 = request.GET.getlist('i1')[0]
		if request.GET.getlist('i2'):
			ind_2 = request.GET.getlist('i2')[0]
		else:
			ind_2 = None
	else:
		ind_1 = None

	## Move from One Industry to Another ##
	if ind_1 and ind_2:

		# Cache
		data = cache.get('next_industry_data_'+str(request.user.id)+'_'+str(ind_1))
		if data is None:
			print 'lvl2: missed cache'
		else:
			print 'lvl2: hit cache'

		# Get the specific entry related to this move
		industry_data = data['transitions'][int(ind_2)]
		new_data = {
			'lvl':2,
			'start_name':data['start_name'],
			'start_id':data['start_id'],
			'end_name':industry_data[0],
			'end_id':ind_2,
			'total_people':industry_data[1],
			'people':industry_data[2],
			'related_industries':data['related_industries'],
		}

		print 'Double Query: ' + str(ind_1) + ' --> ' + str(ind_2)
		return HttpResponse(simplejson.dumps(new_data))


	## Single Industry ##
	# All info about a single industry
	elif ind_1:

		# Check cache
		data = cache.get('next_industry_data_'+str(request.user.id)+'_'+str(ind_1))
		if data is None:
			cache.set('next_industry_data_'+str(request.user.id)+'_'+str(ind_1),_get_industry_data(ind_1, request),600)
			data = cache.get('next_industry_data_'+str(request.user.id)+'_'+str(ind_1))
	
		## Turn off Cache for dev
		# data = _get_industry_data(ind_1, request)

		print 'Single Query: ' + str(ind_1)
		return HttpResponse(simplejson.dumps(data))

	## Plain Page ##
	else:
		# Landing Page
		formatted_industries = []
		seen_before = set() ## to avoid duplicates... needed?
		industries = request.user.profile._industries()
		for i in industries:
			if i.id in seen_before:
				print "@/next/ and duplicate industry found. user id:" + str(request.user.id)
			else:
				formatted_industries.append({'id':i.id, 'name':i.name})
				seen_before.add(i.id)
		saved_industries = SavedIndustry.objects.filter(owner=request.user).select_related("industry")
		for i in saved_industries:
			if i.industry.id in seen_before:
				print "@/next/ and duplicate industry found. user id:" + str(request.user.id)
			else:
				formatted_industries.append({'id':i.industry.id, 'name':i.industry.name})
				seen_before.add(i.industry.id)

		# Do something like... top industries in network?
		all_industries = Industry.objects.all().values("name", "id").order_by("name")
		formatted_all_industries = []

		for i in all_industries:
			formatted_all_industries.append({'id':i['id'], 'name':str(i['name'])})

		data["all_industries"] = json.dumps(formatted_all_industries)
		data["industries"] = json.dumps(formatted_industries)
		return render_to_response('careers/next_v2.html',data,context_instance=RequestContext(request))


# constructs the return data structure for a single industry view
## NOTE: this is a beast, and stores all the dsts needed for the 
## industry --> industry sub-views. 

### FINAL NOTE: eventually, we might want to be able to segment this by 
### 'my network' & 'prosperime community'. I do nothing about this now


def _get_industry_data(ind_id, request):

		## NOTE ##
		# You cannot store anything meaningful in the key of the dict
		# b/c sorting the items later kills the keys. as such, I use
		# the industry id as a key to construct the dst, but also include
		# the industry id in the value so that it can be accessed later

		# DST Schema
		# transitions = {
		# 	ind_id: [ind_name, num_people, people, ind_id]
		# }

		# people = {
		# 	person_id: [person_name, move]
		# }

		# move = {
		# 	start_title
		# 	start_entity_name
		# 	end_title
		# 	end_entity_name
		# }


	industry = Industry.objects.get(pk=ind_id)
	related_positions = Position.objects.filter(entity__domains=industry).select_related('person')
	people_set = set()
	transitions = {}

	## Get other industries related to this person's page
	interested_industries = Profile.objects.get(user=request.user)._industries()
	formatted_industries = []
	for i in interested_industries:
		ind = [i.id, i.name]
		formatted_industries.append(ind)

	## Also, get saved industries
	saved_industries = SavedIndustry.objects.filter(owner=request.user).select_related("industry")
	for i in saved_industries:
		ind = [i.industry.id, i.industry.name]
		formatted_industries.append(ind)

	## Iterate through all positions from given industry
	for p in related_positions:
		person = Profile.objects.get(user=p.person)

		## Use set to count the # people related to each industry
		if p.id not in people_set:
			people_set.add(p)

		## My ghetto logic where I assume that the next position
		## in the db is the next pos in someone's timeline
		next_pk = p.pk - 1
		try:
			next = Position.objects.get(pk=next_pk)
		except:
			next.person == person.user

		# If the next position belongs to the same person
		if next.person == person.user: 
			ind = next.entity.domains.all()

			# If it has industries
			if len(ind) > 0:

				ind_id = ind[0].id

				# We've seen this industry before, update dst
				if ind_id in transitions:
					# Increment #people counter
					transitions[ind_id][1] += 1

					# Create a 'move'
					people = transitions[ind_id][2]
					# Don't add multiple moves for the same person
					if person.id not in people:
						move = {
							'start_title':p.title,
							'start_entity_name':p.entity.name,
							'end_title':next.title,
							'end_entity_name':next.entity.name,
						}

						people[person.id] = [person.full_name(), move]

				else:
					# Haven't seen this transition before
					move = {
						'start_title':p.title,
						'start_entity_name':p.entity.name,
						'end_title':next.title,
						'end_entity_name':next.entity.name,
					}

					# Create People dst
					people = {person.id: [person.full_name(), move]}

					# add to greater dst
					transitions[ind_id] = [ind[0].name, 1, people, ind_id]

	total_people = len(people_set)
	data = {
			'lvl':1,
			'start_id':industry.id, 
			'start_name':industry.name,
			'total_people': total_people,
			'related_industries': formatted_industries,
			'transitions':transitions,
		}

	return data

@login_required
def viewCareerDecisions(request):
	data = {}

	return render_to_response('careers/career_decisions.html',data,context_instance=RequestContext(request))


@login_required
def discover(request):

	# initiate CareerSimBase
	career_path = careerlib.CareerPathBase()
	career_sim = careerlib.CareerSimBase()

	# data array for passing to template
	data = {}
	# print request.user.id
	if 'tasks' in request.session:
		data = {
			'profile_task_id':request.session['tasks']['profile'],
			'connections_task_id':request.session['tasks']['connections'],
		}

	# Check/Set Cache
	careers_network = cache.get('discover_careers_network_data_'+str(request.user.id))
	if careers_network is None:
		cache.set('discover_careers_network_data_'+str(request.user.id),career_path.get_careers_brief_in_network(request.user),600)
		careers_network = cache.get('discover_careers_network_data_'+str(request.user.id))

	careers_similar = cache.get('discover_careers_similar_data_'+str(request.user.id))
	if careers_similar is None:
		cache.set('discover_careers_similar_data_'+str(request.user.id),career_sim.get_careers_brief_similar(request.user),600)
		careers_similar = cache.get('discover_careers_similar_data'+str(request.user.id))

	# # Dev, don't cache
	# careers_network = _get_careers_brief_in_network(request.user)
	# careers_similar = _get_careers_brief_similar(request.user.id)

	careers = {}

	careers['network'] = careers_network
	careers['similar'] = careers_similar

	return render_to_response('entities/discover.html',{'data':data,'careers':careers},context_instance=RequestContext(request))

@login_required
def career_profile(request,career_id):
	# get career object
	career = Career.objects.get(pk=career_id)
	connections = request.user.profile.connections.all()
	# users = User.objects.select_related('profile','positions','pictures').values('id','profile__headline','profile__first_name','profile__last_name','profile__pictures__pic','positions__entity__id','positions__entity__name').filter(positions__careers=career).annotate(no_of_pos=Count('positions__id')).order_by('-no_of_pos')

	# init careerlib
	career_path = careerlib.CareerPathBase()

	# get ed overview
	# ed_overview = None
	ed_overview = cache.get('career_profile_ed_overview_'+str(request.user.id)+"_"+str(career_id))
	# # check to see if cache was empty
	if ed_overview is None:
		print "missed cache @ ed.overview"
		cache.set('career_profile_ed_overview_'+str(request.user.id)+"_"+str(career_id),career_path.get_ed_overview(request.user,career),10)
		ed_overview = cache.get('career_profile_ed_overview_'+str(request.user.id)+"_"+str(career_id))
	# 	# ed_overview = career_path.get_ed_overview(request.user,career)
	
	# get paths overview
	paths = cache.get('paths_in_career_'+str(request.user.id)+"_"+str(career_id))
	# check to see if cache is empty
	if paths is None:
		cache.set('paths_in_career_'+str(request.user.id)+"_"+str(career_id),career_path.get_paths_in_career(request.user,career),10)
		paths = cache.get('paths_in_career_'+str(request.user.id)+"_"+str(career_id))

	# break down paths and overview to make it easier to parses
	paths_in_career = {}
	paths_in_career['network'] = paths['network']
	paths_in_career['all'] = paths['all']

	overview = {}
	overview['network'] = paths['overview']['network']
	overview['all'] = paths['overview']['all']

	# get duration overview
	duration = cache.get('career_stats_duration_'+str(request.user.id)+"_"+str(career_id))
	# check to see if cache is empty
	if duration is None:
		cache.set('career_stats_duration_'+str(request.user.id)+"_"+str(career_id),career_path.get_avg_duration(request.user,career))
		duration = cache.get('career_stats_duration_'+str(request.user.id)+"_"+str(career_id))

	stats = {}
	
	stats['duration'] = {
		'network': duration['network'],
		'all': duration['all']
		} 

	positions = cache.get('career_stats_positions_'+str(request.user.id)+"_"+str(career_id))
	if positions is None:
	# if entry_positions is None or senior_positions is None:
		cache.set('career_stats_positions_'+str(request.user.id)+"_"+str(career_id),career_path.entry_positions_stats(request.user,career))
		positions = cache.get('career_stats_positions_'+str(request.user.id)+"_"+str(career_id))
	
	stats['positions'] = {
		'entry': positions[0],
		'senior': positions[1]
	}

	positions_network = Position.objects.filter(person__profile__in=connections,careers=career)
	positions_all = Position.objects.filter(careers=career)

	positions = {
		'network': positions_network,
		'all': positions_all
	}

	orgs_network = Entity.objects.filter(positions__person__in=connections,positions__careers=career)
	orgs_all = Entity.objects.filter(positions__careers=career)

	orgs = {
		'network': orgs_network,
		'all': orgs_all
	}

	# todo
	# restructure ed overview and paths to cycle through users once, combine logic
	# restructure duration, positions to cycle through positions (maybe combine into one loop)

	return render_to_response('careers/career_profile.html',{'positions':positions,'orgs':orgs,'stats':stats,'career':career,'ed_overview':ed_overview,'paths':paths_in_career,'overview':overview},context_instance=RequestContext(request))

@login_required
def discover_career(request,career_id):

	# initiate CareerSimBase
	# career_path = careerlib.CareerPathBase()

	# get career object
	career = Career.objects.get(pk=career_id)
	
	paths_in_career = {}
	overview = {}

	# Cache
	paths = cache.get('paths_in_career_'+str(request.user.id)+"_"+str(career_id))
	if paths is None:
		print 'discover.people missed cache'
		# cache.set('paths_in_career_'+str(request.user.id)+"_"+str(career_id),career_path.get_paths_in_career(request.user,career),10)
		cache.set('paths_in_career_'+str(request.user.id)+"_"+str(career_id),careerlib.get_paths_in_career(request.user,career),600)
		paths = cache.get('paths_in_career_'+str(request.user.id)+"_"+str(career_id))
	else:
		print 'discover.people hit cache'

	## Don't Cache, for dev
	# paths = _get_paths_in_career_alt(request.user, career)

	paths_in_career['network'] = paths['network']
	paths_in_career['all'] = paths['all']

	overview['network'] = paths['overview']['network']
	overview['all'] = paths['overview']['all']

	request_type = 'people'

	return render_to_response('entities/discover_career.html',{'career':career,'people':paths_in_career,'overview':overview, 'request_type':request_type},context_instance=RequestContext(request))


@login_required
def discover_career_orgs(request, career_id):

	# initiate CareerSimBase
	career_path = careerlib.CareerPathBase()

	career = Career.objects.get(pk=career_id)
	entities_in_career = {}
	overview = {}

	# Cache
	paths = cache.get('paths_in_career_'+str(request.user.id)+"_"+str(career_id))
	if paths is None:
		print 'discover.career.orgs missed cache'
		cache.set('paths_in_career_'+str(request.user.id)+"_"+str(career_id),career_path.get_paths_in_career(request.user,career),600)
		paths = cache.get('paths_in_career_'+str(request.user.id)+"_"+str(career_id))

	else:
		print 'discover.career.orgs hit cache'

	## Don't Cache, for development
	# paths = _get_paths_in_career_alt(request.user, career)

	# entities_in_career['network'] = paths['networkCompanies']
	# entities_in_career['all'] = paths['allCompanies']

	overview['network'] = paths['overview']['network']
	overview['all'] = paths['overview']['all']

	request_type = 'orgs'

	return render_to_response('entities/discover_career.html', {'career': career, 'entities':entities_in_career, 'overview':overview, 'request_type':request_type, 'career_id':career_id}, context_instance=RequestContext(request))

@login_required
def discover_career_positions(request, career_id):

	# initiate CareerSimBase
	career_path = careerlib.CareerPathBase()

	career = Career.objects.get(pk=career_id)
	positions_in_career = {}
	overview = {}

	# # Cache
	paths = cache.get('paths_in_career_'+str(request.user.id)+"_"+str(career_id))
	if paths is None:
		print 'discover.career.pos missed cache'
		cache.set('paths_in_career_'+str(request.user.id)+"_"+str(career_id),career_path.get_paths_in_career(request.user,career),600)
		paths = cache.get('paths_in_career_'+str(request.user.id)+"_"+str(career_id))
	else:
		print 'discover.people hit cache'

	## Don't Cache, for dev
	# paths = _get_paths_in_career_alt(request.user, career)

	paths_in_career['network'] = paths['networkPeople']
	paths_in_career['all'] = paths['allPeople']

	## Don't use cache, for dev
	# paths = _get_paths_in_career_alt(request.user, career)


	positions_in_career['network'] = paths['networkPositions']
	positions_in_career['all'] = paths['allPositions']

	overview['network'] = paths['overview']['network']
	overview['all'] = paths['overview']['all']

	request_type = 'positions'

	return render_to_response('entities/discover_career.html', {'career': career, 'positions':positions_in_career, 'overview':overview, 'request_type':request_type, 'career_id':career_id}, context_instance=RequestContext(request))

@login_required
def position_profile(request,pos_id):

	# initiate position class
	import careers.positionlib as positionlib
	career_pos = positionlib.PositionBase()

	# get position
	position = IdealPosition.objects.get(pk=pos_id)
	
	# ed_overview = None
	ed_overview = cache.get('position_profile_ed_overview_'+str(request.user.id)+"_"+str(pos_id))
	# # check to see if cache was empty
	if ed_overview is None:
		print "missed cache position_profile - @ ed.overview"
		cache.set('position_profile_ed_overview_'+str(request.user.id)+"_"+str(pos_id),career_pos.get_ed_overview(request.user,position),10)
		ed_overview = cache.get('position_profile_ed_overview_'+str(request.user.id)+"_"+str(pos_id))

	# get duration overview
	duration = cache.get('position_stats_duration_'+str(request.user.id)+"_"+str(pos_id))
	# check to see if cache is empty
	if duration is None:
		cache.set('position_stats_duration_'+str(request.user.id)+"_"+str(pos_id),career_pos.get_avg_duration_to_position(request.user,position))
		duration = cache.get('position_stats_duration_'+str(request.user.id)+"_"+str(pos_id))

	stats = {}
	
	stats['duration'] = {
		'network': duration['network'],
		'all': duration['all']
		} 

	return render_to_response('careers/position_profile.html',{'stats':stats,'ed_overview':ed_overview,'position':position},context_instance=RequestContext(request))

@login_required
def position_paths(request,pos_id):
	from django.core import serializers
	# get search filters
	orgsSelected = request.GET.getlist('org')
	locationsSelected = request.GET.getlist('location')
	sectorsSelected = request.GET.getlist('sector')

	# compile filters into one string for cache id
	full_filters_string = "_".join(orgsSelected + sectorsSelected + locationsSelected)

	# check cache
	paths = cache.get("search_position_paths_" + full_filters_string+"_"+pos_id)
	if paths is None:

		# fetch all users for paths, filtered by position
		users = User.objects.prefetch_related('positions').select_related('positions','profile').filter(positions__ideal_position_id=pos_id).annotate(no_of_pos=Count('positions__pk')).exclude(pk=request.user.id).order_by('-no_of_pos')	

		# filter user queryset
		if locationsSelected:
			users = users.filter(positions__entity__office__city__in=locationsSelected)
		if sectorsSelected:
			users = users.filter(positions__entity__domains__name__in=sectorsSelected)
		if orgsSelected:
			users = users.filter(positions__entity__name__in=orgsSelected)

		paths = []

		for u in users[:20]:
			positions = [{'title':p.title,'org':p.entity.name,'org_id':p.entity.id, 'start_date':_date_to_int(p.start_date)} for p in u.positions.all()]
			path = {
				'id':u.id,
				'full_name':u.profile.full_name(),
				'profile_pic':str(u.profile.default_profile_pic()),
				'positions': positions,
				'careers':None
			}
			paths.append(path)

		cache.set("search_position_paths_" + full_filters_string,paths)

	# paths = serializers.serialize('json',paths)
	return HttpResponse(json.dumps(paths))

@login_required
def position_paths_filters(request,pos_id):
	""" serves up JSON object of params for position_path searches """

	# initialize array for all filters
	filters = []

	# get search filters
	locationsSelected = request.GET.getlist('location')
	sectorsSelected = request.GET.getlist('sector')
	orgsSelected = request.GET.getlist('org')

	# set base filters

	# set organization filters
	orgsBase = User.objects.filter(positions__ideal_position_id=pos_id).values("positions__entity__name").annotate(freq=Count('pk')).order_by('-freq').distinct()
	orgsFiltered = orgsBase

	if locationsSelected:
		orgsFiltered = orgsFiltered.filter(positions__entity__office__city__in=locationsSelected)

	if sectorsSelected:
		orgsFiltered = orgsFiltered.filter(positions__entity__domains__name__in=sectorsSelected)

	orgsBase = orgsBase[:10]
	
	orgsFilteredDict = {}
	for o in orgsFiltered:
		orgsFilteredDict[o['positions__entity__name']] = o['freq']

	for o in orgsBase:
		# make sure it doesn't have a null value
		if o['positions__entity__name']:
			# get count from filtered dict
			if o['positions__entity__name'] in orgsFilteredDict:
				freq = orgsFilteredDict[o['positions__entity__name']]
			else:
				freq = 0
			# check to see if the value should be selected
			if o['positions__entity__name'] in orgsSelected:
				filters.append({'name':o['positions__entity__name'],'value':o['positions__entity__name'],'category':'Organizations','count':freq,'selected':True})
			else:
				filters.append({'name':o['positions__entity__name'],'value':o['positions__entity__name'],'category':'Organizations','count':freq,'selected':None})

	# set location filters
	locationsBase = User.objects.filter(positions__ideal_position_id=pos_id).values("positions__entity__office__city").annotate(freq=Count('pk')).order_by('-freq').distinct()
	locationsFiltered = locationsBase
	
	if sectorsSelected:
		locationsFiltered = locationsFiltered.filter(positions__entity__domains__name__in=sectorsSelected)

	if orgsSelected:
		locationsFiltered = locationsFiltered.filter(positions__entity__name__in=orgsSelected)

	locationsBase = locationsBase[:10]

	locationsFilteredDict = {}
	for l in locationsFiltered:
		locationsFilteredDict[l['positions__entity__office__city']] = l['freq']

	for l in locationsBase:
		# make sure it doesn't have a null value
		if l['positions__entity__office__city']:
			# get count from locationsFilteredDict
			if l['positions__entity__office__city'] in locationsFilteredDict:
				freq = locationsFilteredDict[l['positions__entity__office__city']]
			else:
				freq = 0
			# check to see if the value should be selected
			if l['positions__entity__office__city'] in locationsSelected:
				filters.append({'name':l['positions__entity__office__city'],'value':l['positions__entity__office__city'],'category':'Location','count':freq,'selected':True})
			else:
				filters.append({'name':l['positions__entity__office__city'],'value':l['positions__entity__office__city'],'category':'Location','count':freq,'selected':None})

	# get sector filters
	sectorsBase = User.objects.filter(positions__ideal_position_id=pos_id).values('positions__entity__domains__name').annotate(freq=Count('pk')).distinct()
	sectorsFiltered = sectorsBase[:10]

	if locationsSelected:
		sectorsFiltered = sectorsFiltered.filter(positions__entity__office__city__in=locationsSelected)

	if orgsSelected:
		locationsFiltered = locationsFiltered.filter(positions__entity__name__in=orgsSelected)

	sectorsFilteredDict = {}
	for s in sectorsFiltered:
		sectorsFilteredDict[s['positions__entity__domains__name']] = s['freq']

	for s in sectorsBase:
		# make sure it doesn't have a null value
		if s['positions__entity__domains__name']:
			# get count from sectorsFilteredDict
			if s['positions__entity__domains__name'] in sectorsFilteredDict:
				freq = sectorsFilteredDict[s['positions__entity__domains__name']]
			else:
				freq = 0
			name = " ".join(word.capitalize() for word in s['positions__entity__domains__name'].replace("_"," ").split())
			# check to see if the value should be selected
			if s['positions__entity__domains__name'] in sectorsSelected:
				filters.append({'name':name,'value':s['positions__entity__domains__name'],'category':'Sector','count':freq,'selected':True})
			else:
				filters.append({'name':name,'value':s['positions__entity__domains__name'],'category':'Sector','count':freq,'selected':None})
	
	# render response
	return HttpResponse(simplejson.dumps(filters), mimetype="application/json")


def viewCareerDecisions(request):
	data = {}

	return render_to_response('careers/career_decisions.html',data,context_instance=RequestContext(request))


##########################
###### AJAX Methods ######
##########################

def get_majors_filters(request):
	# make sure it's a get request
	from operator import itemgetter
	if request.GET:

		params = request.GET['term']

		majors = [{'label_short':m['major'] + " ("+m['title'].split(" ")[0]+")",'label':m['major'] +  " ("+m['title'].split(" ")[0]+")",'value':m['id'],'type':'majors'} for m in IdealPosition.objects.filter(cat="ed",major__icontains=params).values('major','id','title').distinct()]
		schools = [{'label_short':s['name'],'label':s['name'] + " (school)",'value':s['id'],'type':'schools'} for s in Entity.objects.filter(Q(li_type="school")|Q(type="school")|Q(li_type="educational")).filter(name__icontains=params).exclude(li_uniq_id=None,li_univ_name=None).values('name','id')]
		# jobs = [{'label_short':p['title'],'label':p['title'] + " (job)",'value':p['id'],'type':'jobs'} for p in IdealPosition.objects.filter(title__icontains=params).values('title','id')]

		results = majors + schools

		results = sorted(results, key=itemgetter('label_short'))

		return HttpResponse(json.dumps(results))

def get_internship_filters(request):
	# make sure it's a get request
	from operator import itemgetter
	if request.GET:

		params = request.GET['term']

		# TODO: limit to schools that actually have internship data on 
		# applicable_schools = cache.get("schools_of_repute")
		# if applicable_schools is None:
		# 	applicable_schools = 

		majors = []
		# majors = [{'label_short':m['major'] + " ("+m['title'].split(" ")[0]+")",'label':m['major'] +  " ("+m['title'].split(" ")[0]+")",'value':m['id'],'type':'majors'} for m in IdealPosition.objects.filter(cat="ed",major__icontains=params).values('major','id','title').distinct()]
		schools = [{'label_short':s['name'],'label':s['name'] + " (school)",'value':s['id'],'type':'schools'} for s in Entity.objects.filter(Q(li_type="school")|Q(type="school")|Q(li_type="educational")).filter(name__icontains=params).exclude(li_uniq_id=None,li_univ_name=None).values('name','id')]
		# jobs = [{'label_short':p['title'],'label':p['title'] + " (job)",'value':p['id'],'type':'jobs'} for p in IdealPosition.objects.filter(title__icontains=params).values('title','id')]

		results = majors + schools

		results = sorted(results, key=itemgetter('label_short'))

		return HttpResponse(json.dumps(results))




## returns JSON-ready array of saved careers
def getSavedCareers(request):

	formatted_careers = []
	saved_careers = SavedCareer.objects.filter(owner=request.user).select_related("career")
	for sc in saved_careers:
		formatted_careers.append({
			'title':sc.career.long_name,
			'id':sc.career.id,
		})


	return HttpResponse(simplejson.dumps(response))


## returns JSON-ready array of goal positions
def getGoalPositions(request):

	formatted_positions = []
	goal_positions = GoalPosition.objects.filter(owner=request.user).select_related("position")
	for gp in goal_positions:
		formatted_positions.append({
			'title':gp.position.title,
			'id':gp.position.id,
		})

	return HttpResponse(simplejson.dumps(response))


## Adds a career to user's savedCareers
def addSavedCareer(request):
	response = {}

	if not request.is_ajax or not request.POST:
		response['result'] = 'failure'
		response['errors'] = 'invalid request type'
		return HttpResponse(simplejson.dumps(response))

	user = request.user
	career = Career.objects.get(id=request.POST.get('id'))

	try:
		saved_career = SavedCareer()
		saved_career.career = career
		saved_career.owner = user
		saved_career.title = career.long_name
		saved_career.status = "added"
		saved_career.save()
		response['result'] = 'success'

	except:
		response['result'] = 'failure'
		response['errors'] = 'error saving to DB'


	return HttpResponse(simplejson.dumps(response))

## Adds an idealPosition to user's goalPositions
def addGoalPosition(request):
	response = {}

	if not request.is_ajax or not request.POST:
		response['result'] = 'failure'
		response['errors'] = 'invalid request type'
		return HttpResponse(simplejson.dumps(response))

	user = request.user
	ideal_position = IdealPosition.objects.get(id=request.POST.get('id'))
	
	try:
		goal_position = GoalPosition()
		goal_position.position = ideal_position
		goal_position.owner = user
		goal_position.status = "added"
		goal_position.save()
		response['result'] = 'success'

	except:
		response['result'] = 'failure'
		response['errors'] = 'error saving to DB'


	return HttpResponse(simplejson.dumps(response))


def addIndustry(request):

	response = {}

	if not request.is_ajax or not request.POST:
		response['result'] = 'failure'
		response['errors'] = 'invalid request type'
		return HttpResponse(simplejson.dumps(response))

	user = request.user
	industry = Industry.objects.get(id=request.POST.get('id'))
	print str(industry)
	print user.profile.full_name() + " requests to save industry " + str(request.POST.get('id'))

	try:
		saved_industry = SavedIndustry()
		saved_industry.title = industry.name
		saved_industry.industry = industry
		saved_industry.status = "added"
		saved_industry.owner = user
		saved_industry.save()
		response['result'] = 'success'

	except:
		response['result'] = 'failure'
		response['errors'] = 'error saving to DB'


	return HttpResponse(simplejson.dumps(response))


def addDecision(request):
	response = {}

	if not request.is_ajax or not request.POST:
		response['success'] = 'incorrect request type'
		return HttpResponse(simplejson.dumps(response))

	position = Position.objects.get(id=request.POST.get('pos_id'))

	decision = CareerDecision()
	decision.owner = request.user
	decision.position = position
	decision.winner = decision.position.entity

	if position.type == 'education':
		decision.type = 'college'
	elif 'ntern' in position.title:
		decision.type = 'internshp'
	elif position.current:
		decision.type = 'currentJob'
	else:
		decision.type = None

	privacy = request.POST.get('privacy')
	if privacy:
		decision.privacy = privacy


	decision.reason = request.POST.get('reason')
	decision.comments = request.POST.get('comments')
	decision.mentorship = int(request.POST.get('mentorship'))
	decision.social = int(request.POST.get('social'))
	decision.skills = int(request.POST.get('skills'))
	decision.overall = int(request.POST.get('overall'))

	decision.save()
	response['sucess'] = 'true'

	alternates = request.POST.get('alternates')
	alternates =  alternates.split(', ')
	for alternate in alternates:
		# get entity
		entity = Entity.objects.filter(name=alternate)
		entity=entity[0]
		decision.alternates.add(entity)

	decision.save()
	response['alternates'] = 'completed'

	return HttpResponse(simplejson.dumps(response))


def getDecisions(request):

	if request.GET.getlist('term'):
		search_term = request.GET.getlist('term')[0]
	else:
		search_term = None

	if search_term is None:
		# empty - return 10 most recent
		decisions = CareerDecision.objects.all().order_by('date_created')[:10]
	
	elif search_term == 'relevantCareers':
		decisions = CareerDecision.objects.all().order_by('date_created')[:10]

	elif search_term == 'positionsOfInterest':
		print 'here'
		queue = SavedPath.objects.get(owner=request.user, title='queue')
		poi = SavedPosition.objects.filter(path=queue).select_related('position')
		titles = []
		for p in poi:
			titles.append(p.position.title)
			print p.position.title
		decisions = CareerDecision.objects.filter(position__title__in=titles)

	elif search_term == 'highestRated':
		decisions = CareerDecision.objects.all().order_by('date_created')[:10]

	else: # == 'byCompany'
		decisions = CareerDecision.objects.all().order_by('date_created')[:10]

	response = {
		'decisions':_decisions_to_json(decisions)
	}

	return HttpResponse(simplejson.dumps(response))


## Autocomplete for positions
def positionAutocomplete(request):

	query = request.GET.getlist('query')[0]
	positions = Position.objects.filter(Q(title__istartswith=query) | Q(entity__name__istartswith=query)).values("id", "entity__name", "title", "ideal_position__id")

	suggestions = []
	for p in positions:
		string = str(p['title']) + ' at ' + str(p['entity__name'])
		item = {
			'value':string,
			'pos_id':p['id'],
			'title':p['title'],
			'entity_name':p['entity__name'],
			'ideal_id':p['ideal_position__id'],
		}
		suggestions.append(item)

	response = {
		'query': query,
		'suggestions': suggestions,
	}

	return HttpResponse(simplejson.dumps(response))


## Autocomplete for multiple entities, used in CareerDecision prompt
def entityAutocomplete(request):

	query = request.GET.getlist('query')[0]
	entities = Entity.objects.filter(name__istartswith=query).values('name')

	suggestions = []
	for e in entities:
		suggestions.append(str(e['name']))

	# suggestions = simplejson.dumps(suggestions)
	print suggestions
	response = {
		'query': query,
		'suggestions': suggestions,
	}
	return HttpResponse(simplejson.dumps(response))

## Autocomplete for careers, used in Profile
def careerAutocomplete(request):

	query = request.GET.getlist('query')[0]
	careers = Career.objects.filter(long_name__istartswith=query).values('long_name', 'id')

	suggestions = []
	for c in careers:
		item = {
			'value':c['long_name'],
			'data':c['id'],
		}
		suggestions.append(item)	

	response = {
		'query':query,
		'suggestions':suggestions,
	}

	return HttpResponse(simplejson.dumps(response))

def idealPositionAutocomplete(request):

	query = request.GET.getlist('query')[0]
	positions = IdealPosition.objects.filter(title__istartswith=query).values('title', 'id')

	suggestions = []
	for p in positions:
		item = {
			'value':p['title'],
			'data':p['id'],
		}
		suggestions.append(item)	

	response = {
		'query':query,
		'suggestions':suggestions,
	}

	return HttpResponse(json.dumps(response))


## Autocomplete for industries, used in What Next?
def industryAutocomplete(request):

	query = request.GET.getlist('query')[0]

	print 'query: ' + query
	industries = Industry.objects.filter(name__istartswith=query).values('name', 'id')

	suggestions = []
	seen_before = set()
	for i in industries:
		if (i['name']) not in seen_before:
			item = {
				'value':i['name'],
				'data':i['id'],
			}
			suggestions.append(item)
			seen_before.add(i['name'])

	response = {
		'query':query,
		'suggestions':suggestions,
	}	
	
	return HttpResponse(simplejson.dumps(response))


def home_proto(request):

	user_jobs = [
		{"title":"Product Management Intern", "entity":"Wordnik", "position_id":7, "entity_id":8},
		{"title":"Marketing & Banking Intern", "entity":"Montgomery & Co.", "position_id":7, "entity_id":8},
		{"title":"Intern", "entity":"Bankinter", "position_id":7, "entity_id":8},
		{"title":"Co-Founder", "entity":"ProsperMe", "position_id":7, "entity_id":8},
	]

	popular_tags = [
		{"title":"Great Hours", "id":7, "type":"Good"},
		{"title":"What Perks", "id":7, "type":"Bad"},
		{"title":"Crazy Hours", "id":7, "type":"Bad"},
		{"title":"Strict Culture", "id":7, "type":"Eh"},
		{"title":"Great Pay", "id":7, "type":"Good"},
		{"title":"Great Cause", "id":7, "type":"Good"},
		{"title":"Just a Paycheck", "id":7, "type":"Bad"},
	]

	related_reviews = [
		{"position":"Product Manager", "entity":"Wordnik", "id":10},
		{"position":"Web Developer", "entity":"Greystripe", "id":10},
		{"position":"Editor", "entity":"Penguin Books", "id":10},
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

	suggested = [
		{"title":"Google" , "type":"entity" ,"id":7},
		{"title":"Facebook" , "type":"entity" ,"id":7},
		{"title":"Apple" , "type":"entity" ,"id":7},
		{"title":"Product Manager" , "type":"position" ,"id":7},
		{"title":"Web Developer" , "type":"position" ,"id":7},
		{"title":"Full-Stack Ruby Developer" , "type":"position" ,"id":7},
	]


	data = {
		"user_jobs":user_jobs,
		"popular_tags":popular_tags,
		"related_reviews":related_reviews,
		"suggested":suggested,
		"reviews":reviews,
	}



	return render_to_response("proto.html", data, context_instance=RequestContext(request))



@login_required
def personalize_careers_jobs(request):
	'''
	presents initial set of careers and jobs to user during onboarding for them to selected
	'''
	# initiate careerlib
	career_path = careerlib.CareerPathBase()
	career_sim = careerlib.CareerSimBase()

	# data array for passing to template
	data = {}

	# check to see if tasks are pending
	# if 'tasks' in request.session:
	# 	data['tasks'] = {}
	# 	if 'profile' in request.session['tasks']:
	# 		data['tasks']['profile'] = request.session['tasks']['profile']
	# 		if request.session['tasks']['profile']['status'] == True:
	# 			del request.session['tasks']['profile']
	# 	if 'connections' in request.session['tasks']:
	# 		data['tasks']['connections'] = request.session['tasks']['connections']
	# 		if request.session['tasks']['connections']['status'] == True:
	# 			del request.session['tasks']['connections']
	# 	if len(request.session['tasks']) == 0:
	# 		del request.session['tasks']

	# get career information
	careers_network = career_path.get_careers_brief_in_network(request.user)
	careers_similar = career_sim.get_careers_brief_similar(request.user)

	# get list of ids of similar careers to avoid duplication in network
	careers_similar_ids = []

	for c in careers_similar:
		careers_similar_ids.append(c.id)

	careers = {}

	careers['network'] = careers_network
	careers['similar'] = careers_similar

	return render_to_response('careers/personalize.html',{'data':data,'careers':careers},context_instance=RequestContext(request))

@login_required
def personalize_careers(request):
	'''
	presents initial set of careers  to user during onboarding for them to selected
	'''
	# initiate careerlib
	career_path = careerlib.CareerPathBase()
	career_sim = careerlib.CareerSimBase()

	# data array for passing to template
	data = {}

	# check to see if tasks are pending
	# if 'tasks' in request.session:
	# 	data['tasks'] = {}
	# 	if 'profile' in request.session['tasks']:
	# 		data['tasks']['profile'] = request.session['tasks']['profile']
	# 		if request.session['tasks']['profile']['status'] == True:
	# 			del request.session['tasks']['profile']
	# 	if 'connections' in request.session['tasks']:
	# 		data['tasks']['connections'] = request.session['tasks']['connections']
	# 		if request.session['tasks']['connections']['status'] == True:
	# 			del request.session['tasks']['connections']
	# 	if len(request.session['tasks']) == 0:
	# 		del request.session['tasks']

	# get career information
	careers_network = career_path.get_careers_brief_in_network(request.user)
	careers_similar = career_sim.get_careers_brief_similar(request.user)

	# get list of ids of similar careers to avoid duplication in network
	careers_similar_ids = [c.id for c in careers_similar]

	careers = {
		'network': careers_network,
		'similar': careers_similar
	}

	# careers = {}

	# careers['network'] = careers_network
	# careers['similar'] = careers_similar

	return render_to_response('careers/personalize_careers.html',{'data':data,'careers':careers,'careers_similar_ids':careers_similar_ids},context_instance=RequestContext(request))

@login_required
def personalize_jobs(request):

	return render_to_response('careers/personalize_jobs.html',context_instance=RequestContext(request))

@login_required
def add_personalization(request):
	# check to make sure POST data came through
	if request.POST:
		print request.POST
		if 'selected_careers[]' in request.POST:
			print request.POST.getlist('selected_careers[]')
			for career_id in set(request.POST.getlist('selected_careers[]')):
				career = Career.objects.get(pk=career_id)
				if career not in request.user.saved_careers.all():
					saved_career = SavedCareer(career=career,owner=request.user)
					saved_career.save()
		if 'selected_jobs[]' in request.POST:
			for job_name in set(request.POST.getlist('selected_jobs[]')):
				# get or create the ideal position
				try:
					ideal_pos = IdealPosition.objects.get(title=job_name)
				except:
					ideal_pos = IdealPosition(title=job_name)
					ideal_pos.save()
				# make sure user hasn't already saved this one
				try:
					goal_pos = GoalPosition.objects.get(owner=request.user,position=ideal_pos)
				except:
					goal_pos = GoalPosition(owner=request.user,position=ideal_pos)
					goal_pos.save()

		## Get current industry to show for 'what's next' page -- 
		data = {}
		industries = request.user.profile._industries()
		if industries:
			data['industries'] = industries[0].id
		else:
			data['industries'] = None
		data['success'] = True
		return HttpResponse(simplejson.dumps(data))
		#return render_to_response('api_success.html', data)
	else:
		return render_to_response('api_fail.html')

@login_required
def list_jobs(request):
	if request.GET:
		params = request.GET['q']
		# print params
		jobs = IdealPosition.objects.values('title','id').filter(title__icontains=params)
	else:
		jobs = IdealPosition.objects.values('title','id').all()

	jobs_list = []

	for j in jobs:
		jobs_list.append({'value':j['title'],'id':j['id']})

	# jobs = json.dumps(list(jobs))
	jobs = json.dumps(jobs_list)
	return HttpResponse(jobs, mimetype="application/json")

@login_required
def list_careers(request):
	if request.GET:
		params = request.GET['q']
		# print params
		careers = Career.objects.values('short_name','id').filter(Q(short_name__icontains=params) | Q(long_name__icontains=params))
	else:
		careers = Career.objects.values('short_name','id').all()

	careers_list = [{'value':c['short_name'],'id':c['id']} for c in careers]

	# jobs = json.dumps(list(jobs))
	careers = json.dumps(careers_list)
	return HttpResponse(careers, mimetype="application/json")

# VIEW: display ALL user's paths
def show_paths(request):

	# paths = SavedPath.objects.filter(owner=request.user)

	# data = {
	# 	'saved_paths': paths,
	# }

	# return render_to_response('careers/saved_paths.html', data,
	# 	context_instance=RequestContext(request))

	### TEMPORARILY, A JSON DUMPER
	paths = SavedPath.objects.filter(owner=request.user).prefetch_related()
	formatted_paths = []
	for p in paths:
		current = {
			'owner':p.owner.profile.full_name(),
			'title':p.title,
			'last_index':p.last_index
		}
		saved_positions = SavedPosition.objects.filter(path=p)
		positions = []
		for pos in saved_positions:
			positions.append({
				'pos_id':pos.position.id,
				'title':pos.position.title,
				'entity':pos.position.entity.name,
				'owner':pos.position.person.profile.full_name(),
			})

		current['positions'] = positions
		formatted_paths.append(current)	

	return HttpResponse(simplejson.dumps(formatted_paths))

def test_build_paths(request):

	# verify GET has right parameters
	if request.GET.getlist('ideal_id'):

		start_ideal_id = request.GET.getlist('ideal_id')[0]
		start_pos_id = request.GET.getlist('pos_id')[0]

		# check cache for path information
		paths = cache.get("get_next_build_step_ideal_"+str(start_ideal_id)+"_"+str(start_pos_id))
		if paths is None:
			# initialize class
			build = careerlib.CareerBuild()
			paths = build.get_next_build_step_ideal(start_ideal_id,start_pos_id)
			cache.set('get_next_build_step_ideal_'+str(start_ideal_id)+'_'+str(start_pos_id),paths,10)

		return render_to_response('careers/test_build_paths.html',{'paths':paths},context_instance=RequestContext(request))

# AJAX for getting build steps
def get_next_build_step(request):
	# check if GET parameters were sent
	if request.GET.getlist('id'):
		# initialize class
		career_path = careerlib.CareerBuild()

		# initiate next and finished flag
		next = []
		finished = []
		# initiate array for next positions
		pos = []
		# reduce GET to variable
		
		start_ideal_id = request.GET.getlist('id')[0]
		start_pos_id = request.GET.getlist('pos_id')[0]

		print 'ideal_id: ' + str(start_ideal_id)
		print 'pos_id: ' + str(start_pos_id)

		# try to retreive positions from cache
		positions = cache.get("get_next_build_step_ideal_"+str(start_ideal_id)+"_"+str(start_pos_id))
		if positions is None:
			# initialize class
			build = careerlib.CareerBuild()
			positions = build.get_next_build_step_ideal(start_ideal_id,start_pos_id)

		# ideal_pos = career_path.get_next_build_step_ideal(start_ideal_id,start_pos_id)
		# print ideal_pos
		
		## GET FAKE TOP PEOPLE
		# p = Profile.objects.get(id=880)
		# people = []
		# latest = p.latest_position()
		# people.append({'id':880, 'name':p.full_name(), 'title':latest.title, 'entity_name':latest.entity.name, 'profile_pic':p.default_profile_pic()})
		# p = Profile.objects.get(id=841)
		# latest = p.latest_position()
		# people.append({'id':841, 'name':p.full_name(), 'title':latest.title, 'entity_name':latest.entity.name, 'profile_pic':p.default_profile_pic()})
		# p = Profile.objects.get(id=908)
		# latest = p.latest_position()
		# people.append({'id':908, 'name':p.full_name(), 'title':latest.title, 'entity_name':latest.entity.name, 'profile_pic':p.default_profile_pic()})



		for ideal in ideal_pos:
			ideal["people"] = people
			ideal["duration"] = "12 months"
			entities = []
			for e in ideal["orgs"]:
				ent = Entity.objects.get(id=e["id"])
				entities.append({'name':e['name'], 'description':ent.description})
			ideal["entities"] = entities
			ideal["title"] = ideal["ideal_title"]
			ideal["level"] = ideal["positions"][0]["level"]

		print "Num Options Returned: " + str(len(positions))

		return HttpResponse(json.dumps(positions))

# AJAX for getting build steps
def get_next_build_step_ideal(request):
	# check if GET parameters were sent
	if request.GET.getlist('id'):
		# initialize class
		build = careerlib.CareerBuild()

		# initiate next and finished flag
		next = []
		finished = []
		# initiate array for next positions
		pos = []
		# reduce GET to variable
		
		start_ideal_id = request.GET.getlist('id')[0]
	
		start_pos_id = request.GET.getlist('pos_id')[0]

		# try to retreive positions from cache
		positions = cache.get("get_next_build_step_ideal_"+str(start_ideal_id)+"_"+str(start_pos_id))
		if positions is None:
			# initialize class
			build = careerlib.CareerBuild()
			positions = build.get_next_build_step_ideal(start_ideal_id,start_pos_id)

		print "Num Options Returned: " + str(len(positions))

		return HttpResponse(json.dumps(positions))
	
# AJAX for returning a JSON of ideal position paths
def get_ideal_paths(request):
	
	# verify GET has right parameters
	if request.GET.getlist('ideal_id'):

		ideal_pos_id = request.GET.getlist('ideal_id')[0]

		# from careers.positionlib import IdealPositionBase
		# ideal_pos_lib = IdealPositionBase()

		# check cache for path information
		paths = cache.get('get_ideal_paths'+'_'+str(ideal_pos_id))
		if paths is None:
			# cache expired, retrieve anew
			from careers.positionlib import IdealPositionBase
			ideal_pos_lib = IdealPositionBase()

			paths = ideal_pos_lib.get_ideal_paths(ideal_pos_id)

		

		return HttpResponse(json.dumps(paths))

def get_ideal_pos_paths(request):
	print request
	# verify GET has right parameters
	if request.GET.getlist('ideal_id'):

		# reduce GET param to regular variable
		ideal_pos_id = request.GET.getlist('ideal_id')[0]

		# instantiate positionlib class
		from careers.positionlib import IdealPositionBase
		ideal_pos_lib = IdealPositionBase()
		
		
		full_paths = {}
		# check for initial path
		initial_path_id = request.GET.getlist('initial')
		print initial_path_id
		if initial_path_id:
			initial_path_id = initial_path_id[0]
			# fetch paths
			paths = ideal_pos_lib.get_paths_to_ideal_position(ideal_pos_id,initial_path_id)
		else:
			# fetch paths
			paths = ideal_pos_lib.get_paths_to_ideal_position(ideal_pos_id)

		# return paths as json
		full_paths['paths'] = paths
		return HttpResponse(json.dumps(full_paths))

# AJAX method for retreiving users who match an ideal path
def get_ideal_match_users(request):
	# verify GET has right parameters
	
	if request.GET.getlist('path[]'):

		# reduce GET to list
		path = request.GET.getlist('path')
		print path
		# instantiate positionlib class
		from careers.positionlib import IdealPositionBase
		ideal_pos_lib = IdealPositionBase()

		matches = ideal_pos_lib.get_users_matching_ideal_path(path)

		return HttpResponse(json.dumps(matches))

def save_build_path(request):

	response = {}
	if not request.is_ajax or not request.POST:
		response["result"] = "failure"
		response["errors"] = "Incorrect request type"
		return HttpResponse(json.dumps(response))

	title = request.POST.get("title")
	position_ids = request.POST.getlist("position_ids[]")
	path_id = int(request.POST.get("path_id"))

	if path_id == -1:
		# new path
		try:
			path = SavedPath()
			path.title = title
			path.owner = request.user
			path.save()

			counter = 0
			for p_id in position_ids:
				pos = SavedPosition()
				pos.path = path
				pos.index = counter
				pos.position = Position.objects.get(id=int(p_id))
				pos.save()
				counter += 1

			path.last_index = counter
			path.save()

			response["result"] = "success"
			response["path_id"] = path.id


		except:
			response["result"] = "failure"
			response["errors"] = "Error creating path in careers.views"

	else:
		path = SavedPath.objects.get(id=path_id)

		try:
			# probably a faster way to do than batch delete/save
			for saved_pos in SavedPosition.objects.filter(path=path):
				saved_pos.delete()

			path.title = title
			counter = 0
			for p_id in position_ids:
				pos = SavedPosition()
				pos.path = path
				pos.index = counter
				pos.position = Position.objects.get(id=int(p_id))
				pos.save()
				counter += 1

			path.last_index = counter
			path.save()
			response["result"] = "success"
			response["path_id"] = path.id

		except:
			response["result"] = "failure"
			response["errors"] = "Error saving existing path in careers.views"


	return HttpResponse(json.dumps(response))

# for single major d3 viz -- AJAX
def get_major_data(request,major_id):
	
	data = cache.get("major_viz_"+str(request.user.id)+"_"+str(major_id))
	if not data:
		path = careerlib.CareerPathBase()
		data = path.get_major_data(major_id)
		cache.set("major_viz_"+str(request.user.id)+"_"+str(major_id),data,2400)

	return HttpResponse(json.dumps(data))

def get_majors_data_v3(request):
	params = {}
	# print request.GET
	if request.GET.getlist('majors[]'):
		params['majors'] = [int(m) for m in request.GET.getlist('majors[]')]
		# print params['majors']
		# print request.GET.getlist('majors[]')
	if request.GET.getlist('schools[]'):
		params['schools'] = request.GET.getlist('schools[]')
	# if request.GET.getlist('jobs[]'):
	# 	params['jobs'] = request.GET.getlist('jobs[]')
	if request.GET.getlist('user'):
		params['user'] = request.GET.getlist('user')[0]

	path = careerlib.CareerPathBase()


	# If there are no params, look back at the cache 
	if not params:
		data = cache.get("majors_viz_v3_full")
		if data is None:
			data = path.get_majors_data_v3(**params)
			cache.set("majors_viz_v3_full",data,300)
	else:
		from urllib import urlencode
		cache_stub = urlencode(params)
		data = cache.get("majors_viz_v3_"+cache_stub)
		if data is None:
			data = path.get_majors_data_v3(**params)
			cache.set("majors_viz_v3_"+cache_stub,data,300)

	return HttpResponse(json.dumps(data))

# For Majors D3 viz -- AJAX
def get_majors_data(request):

	# logger.info("getting majors data")
	params = {}
	# print request.GET
	if request.GET.getlist('majors[]'):
		params['majors'] = [int(m) for m in request.GET.getlist('majors[]')]
		# print params['majors']
		# print request.GET.getlist('majors[]')
	if request.GET.getlist('schools[]'):
		params['schools'] = request.GET.getlist('schools[]')
	if request.GET.getlist('jobs[]'):
		params['jobs'] = request.GET.getlist('jobs[]')
	
	path = careerlib.CareerPathBase()

	# If there are no params, look back at the cache 
	if not params:
		data = cache.get("majors_viz")
		if data is None:
			data = path.get_majors_data(**params)
			cache.set("majors_viz",data,2400)
	else:
		data = path.get_majors_data(**params)

	return HttpResponse(json.dumps(data))

	# people = []
	# positions = []
	# majors = {}

	# majors_set = set()
	# people_set = set()
	# positions_set = set()

	# counter = 0

	# # get schools from user
	# schools = Entity.objects.filter(li_type="school",positions__person=request.user,positions__type="education").distinct()

	# acceptable_majors = ["Science, Technology, and Society", "English", "Psychology", "Management Science & Engineering", "Computer Science", "International Relations", "Political Science", "Economics", "Human Biology", "Product Design", "History", "Civil Engineering", "Electrical Engineering", "Physics", "Symbolic Systems", "Mechanical Engineering", "Spanish", "Public Policy", "Materials Science & Engineering", "Biomechanical Engineering", "Mathematics", "Classics", "Feminist Studies", "Mathematical and Computational Sciences", "Atmosphere and Energy Engineering", "Urban Studies", "Chemistry", "Chemical Engineering", "Religious Studies", "Earth Systems"]
	# # base_positions = Position.objects.filter(type="education", field__in=acceptable_majors).exclude(ideal_position=None).select_related("person")
	
	# # assemble all the positions
	# # base_positions = Position.objects.filter(type="education",entity__in=schools).exclude(ideal_position=None).select_related("person")
	# base_positions = Position.objects.filter(type="education",ideal_position__level=1).exclude(ideal_position=None,person__profile__status="crunchbase").select_related("person")

	# for p in base_positions:
	# 	# first_ideal = p.person.profile.first_ideal()
	# 	first_ideal = p.person.profile.first_ideal_job()

	# 	# Majors
	# 	if first_ideal:
	# 		if p.ideal_position.major is None:
	# 			continue
	# 			print p.title, p.degree, p.field
	# 			print p.ideal_position, p.ideal_position.id
	# 		if p.ideal_position.major not in majors_set:
	# 			majors_set.add(p.ideal_position.major)
	# 			majors[p.ideal_position.major] = {"id":[p.ideal_position.id],"people":[p.person.id], "positions":[first_ideal['ideal_position__id']], "index":len(majors_set)}
	# 		# if p.field not in majors_set:
	# 		# 	majors_set.add(p.field)
	# 		# 	majors[p.field] = {"people":[p.person.id], "positions":[first_ideal.id], "index":len(majors_set)}
	# 		else:
	# 			# majors[p.field]["people"].append(p.person.id)
	# 			# majors[p.field]["positions"].append(first_ideal.id)
	# 			majors[p.ideal_position.major]["people"].append(p.person.id)
	# 			majors[p.ideal_position.major]["positions"].append(first_ideal['ideal_position__id'])

	# 		# People
	# 		if p.person.id not in people_set:

	# 			people_set.add(p.person.id)
	# 			people.append({'name':p.person.profile.full_name(), 'id':p.person.id, "major_index":majors[p.ideal_position.major]["index"], "major":p.ideal_position.major})

	# 			counter += 1	
	# 			if counter == 72:
	# 				break;


	# 		if first_ideal['ideal_position__id'] not in positions_set:
	# 			positions_set.add(first_ideal['ideal_position__id'])
	# 			positions.append({'title':first_ideal['ideal_position__title'], 'id':first_ideal['ideal_position__id'], "major_index":majors[p.ideal_position.major]["index"], "major":p.ideal_position.major})


	
	# 	# ideal_positions_set = set()
	# 	# majors_dict = {}

	# 	# all_people = Profile.objects.all()
	# 	# for p in all_people:
	# 	# 	first_ideal = p.first_ideal()

	# 	# 	# Make sure they have a first position
	# 	# 	if first_ideal:
	# 	# 		# Add to people list
	# 	# 		people.append({'name':p.full_name(), 'id':p.id})
	# 	# 		# Add to position list
	# 	# 		if first_ideal.id not in ideal_positions_set:
	# 	# 			ideal_positions_set.add(first_ideal)
	# 	# 			positions.append({'title':first_ideal.title, 'id':first_ideal.id})

	# 	# majored_positions = Position.objects.filter(type="education").exclude(field=None)
	# 	# for m in majored_positions:
	# 	# 	if m.field not in majors_dict:
	# 	# 		majors_dict[m.field] = 1
	# 	# 		majors.append({'major':m.field, 'id':m.id})
	# 	# 	else:
	# 	# 		majors_dict[m.field] = majors_dict[m.field] + 1

	# 	# print majors
	# 	# print "###################"
	# 	# print people
	# 	# print "###################"
	# 	# print positions

	# 	# majors["Human Basket-weaving and other Anthropological Endeavors"] = {"id":1,"people":[],"positions":[],"index":len(majors_set)}
	# 	data = {
	# 		"majors":json.dumps(majors),
	# 		"positions":json.dumps(positions),
	# 		"people":json.dumps(people),
	# 		"result":"success"
	# 	}
	if not params:

		cache.set("majors_viz_"+str(request.user.id),data,2400)
		cache.set("majors_viz",data,2400)


	return HttpResponse(json.dumps(data))


# Deletes all saved positions and saved path of given path id
def delete_path(request):
	response = {}

	if not request.is_ajax or not request.POST:
		response['result'] = "failure"
		response['errors'] = "Incorrect request type"
		return HttpResponse(json.dumps(response))

	path_id = request.POST.get('id')
	print "Delete saved_path: " + str(path_id)

	try:
		saved_positions = SavedPosition.objects.filter(path__id=path_id)
		for s in saved_positions:
			s.delete()

		saved_path = SavedPath.objects.get(id=path_id)
		saved_path.delete()

		response["result"] = "success"
	except:
		response["result"] = "failure"
		response["result"] = "Error deleting path from DB in careers.views"

	return HttpResponse(json.dumps(response))


# JSON dumper
def get_paths(request):
	paths = []

	# Check if get parameters or not
	# If so, show a single path
	if request.GET.getlist('id'):
		path_requested = request.GET.getlist('id')[0]
		path = SavedPath.objects.get(id=path_requested)
		path_owner = path.owner

		saved_positions = SavedPosition.objects.filter(path=path)
		positions = _get_positions_for_path(saved_positions, True)
		count = 0
		paths.append({'title': path.title, 'positions': positions, 'count': count, 'id': path.id, 'type':'single'})

	# If not, show all path_requested
	else:
		all_paths = SavedPath.objects.filter(owner=request.user)

		if all_paths is not None:
			# then add to data
			for path in all_paths:

				# delegate position formatting to helper
				# TODO: don't need path objects here! 
				# saved_positions = Saved_Position.objects.filter(path=path)
				# positions = _get_positions_for_path(saved_positions, False)	
				positions = []
				count = SavedPosition.objects.filter(path=path).count()
				paths.append({'title': path.title, 'positions': positions, 'id': path.id, 'count':count, 'type':'all'})


		# else do nothing

	return HttpResponse(simplejson.dumps(paths), mimetype="application/json")
	

# AJAX POST requests only
def remove(request):
	response = {}
	if not request.is_ajax or not request.POST:
		print 'Error @ saved_paths.remove'
		response.update({'success':False})
		return HttpResponse(simplejson.dumps(response))

	if request.POST.get('type') == 'path':
		# then delete a path
		path_id = request.POST.get('path_id')

		# Error Checking
		if not path_id:
			print 'Error @ saved_paths.remove'
			response.update({'success':False})
			return HttpResponse(simplejson.dumps(response))

		path = SavedPath.objects.get(id=path_id)
		path.delete()
		response.update({'success':True})

	else:

		# delete a position from a path
		path_id = request.POST.get('path_id', False)
		pos_id = request.POST.get('pos_id', False)

		# Error checking...
		if not path_id or not pos_id:
			print 'Error @ saved_paths.remove'
			response.update({'success':False})
			return HttpResponse(simplejson.dumps(response))
	
		try:
			path = SavedPath.objects.get(id=path_id)
			position = Position.objects.get(id=pos_id)

			saved_position = SavedPosition.objects.get(path=path, position=position)
			deleted_pos_index = int(saved_position.index)
			saved_position.delete()
			response.update({'success': True})

		except:
			response.update({'success': False})


		# now, must cascade index changes and update path.last_index
		path.last_index = int(path.last_index) - 1
		path.save()

		positions_in_path = SavedPosition.objects.filter(path=path)
		for pos in positions_in_path:
			if int(pos.index) > deleted_pos_index:
				pos.index = int(pos.index) - 1
				pos.save()

	return HttpResponse(simplejson.dumps(response))


# VIEW: responds to ajax POST request only 
def save(request):

	# Error checking
	if not request.is_ajax:
		print 'Error @ saved.paths.save - non ajax requested'
		return render_to_response('/search/', context_instance=RequestContext(request))

	if not request.POST:
		print 'Error @ saved_paths.save - get request'
		return render_to_response('/search/', context_instance=RequestContext(request))

	title = request.POST.get('title', False)
	pos_id = request.POST.get('pos_id', False)

	response = {}

	if title and pos_id:
		response.update({'success':True})
	else:
		response.update({'errors':['Either title or pos_id missing']})

	path = SavedPath.objects.get(title=title, owner=request.user)
	if not path:
		response.update({'errors':['path could not be found']})
	else:
		position = Position.objects.get(id=pos_id)

		saved_position = SavedPosition()
		saved_position.position = position
		saved_position.path = path
		saved_position.index = path.get_next_index()
		saved_position.save()	

		# path.positions.add(position)

	return HttpResponse(simplejson.dumps(response))

def get_queue(request):
	print 'in careers.get_queue'
	try:
		queue = SavedPath.objects.get(owner=request.user, title='queue')
		queue = _saved_path_to_json(queue)
	except:
		queue = None

	return HttpResponse(simplejson.dumps(queue))

# FOR DEV ONLY 


def add_to_queue(request):
	response = {}
	pos_id = request.POST.get('pos_id', False)

	if not request.is_ajax:
		response['success'] = 'not ajax request'
	if not request.POST:
		response['success'] = 'not POST'
	if not pos_id:
		response['success'] = 'no pos_id'

	try:
		existing_queue = SavedPath.objects.get(owner=request.user, title='queue')
	except:
		# Create a new one
		existing_queue = SavedPath()
		existing_queue.title = 'queue'
		existing_queue.owner = request.user
		existing_queue.last_index = 1
		existing_queue.save()
		print existing_queue.owner

	try:
		position = Position.objects.get(id=pos_id)
		new_pos = SavedPosition()
		new_pos.position = position
		new_pos.path = existing_queue
		new_pos.index = 0
		new_pos.save()
	except:
		response['success'] = 'failed in back-end'

	return HttpResponse(simplejson.dumps(response))


# VIEW: creates a path, responds to POST request via AJAX
def create(request):
	title = request.POST.get('title', False)

	# Error checking... what to do with them??
	if not request.is_ajax:
		print 'Error @ saved_paths.create - non ajax requested'
	if not request.POST:
		print 'Error @ saved_paths.create - get request!'
	if not title:
		print 'Error @ saved_paths.create - no title'

	response = {}

	try:
		new_path = SavedPath()
		new_path.title = title
		new_path.owner = request.user
		new_path.last_index = 1

		# automatically add current position to any new cp
		currentPos = Position.objects.filter(person=request.user, current=True).exclude(type='education')
		if currentPos:
			# need to test this
			new_path.save()
			first_position = SavedPosition()
			first_position.position = currentPos[0]
			first_position.path = new_path
			first_position.index = 0
			first_position.save()
		else:
			# this means we DON'T have a current position for them...
			# think about this one
			# add a "funemployment" position!
			new_path.last_index = 0
			new_path.save()

		response.update({'success': True, 'id':new_path.id})

	except:
		response.update({'success': False})

	return HttpResponse(simplejson.dumps(response))

# AJAX POST only, changes the indexing of saved_positions
def rearrange(request):

	response = {}
	pos_id = int(request.POST.get('pos_id'))
	diff = int(request.POST.get('difference'))
	pos_index = int(request.POST.get('pos_index'))
	path_id = int(request.POST.get('path_id'))
	
	positions = SavedPosition.objects.filter(path=SavedPath.objects.get(id=path_id))
	
	# Position being moved 'up'
	if diff > 0:
		for p in positions:
			if p.position.id == pos_id:
				p.index = int(p.index) + diff
				p.save()
			elif int(p.index) > pos_index and int(p.index) <= (pos_index + diff):
				p.index = int(p.index) - 1
				p.save()

	# Position being moved 'down'
	else: 
		for p in positions:
			if p.position.id == pos_id:
				p.index = int(p.index) + diff
				p.save()
			elif int(p.index) < pos_index and int(p.index) >= (pos_index + diff):
				p.index = int(p.index) + 1
				p.save()

	response.update({'success':True})
	return HttpResponse(simplejson.dumps(response))



######################################################
##################    HELPERS   ######################
######################################################



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


# Takes an array of CareerDecision objects and returns array of 
	# JSON-able items
def _decisions_to_json(decisions):
	formatted_decisions = []

	for d in decisions:

		avg = _average_decision_score(d)

		decision = {
			'id':d.id,
			'owner':d.owner.profile.full_name(),
			'owner_id':d.id,
			'privacy':d.privacy,
			'position_title':d.position.title,
			'position_id':d.position.id,
			'position_entity_name':d.winner.name,
			'position_entity_id':d.winner.id,
			'reason':d.reason,
			'comments':d.comments,
			'avg':avg,
			'social':d.social,
			'skills':d.skills,
			'mentorship':d.mentorship,
			'overall':d.overall,
		}

		alternates = []
		for a in d.alternates.all():
			alternates.append({
				'entity_name':a.name,
				'entity_id':a.id,
			})
		decision['alternates'] = alternates

		formatted_decisions.append(decision)

	print 'returning formatted decisions: ' + str(len(formatted_decisions))
	return formatted_decisions


def _average_decision_score(decision):
	denominator = 4
	numerator = 0

	if decision.social != 0:
		numerator += decision.social
	else:
		denominator -= 1

	if decision.skills != 0:
		numerator += decision.skills
	else: 
		denominator -= 1

	if decision.mentorship != 0:
		numerator += decision.mentorship
	else:
		denominator -= 1

	if decision.overall != 0:
		numerator += decision.overall
	else:
		denominator -= 1

	if denominator == 0:
		return None
	else:
		return numerator / denominator



def _ready_profiles_for_json(profiles):
	formatted_profiles = []

	for p in profiles:
		attribs = {
			'first_name': p.first_name,
			'last_name:': p.last_name,
		}
		formatted_profiles.append(attribs)

	return formatted_profiles



def _split_and_jsonify(all_positions):

	intern_total = 0; big_total = 0; bigs = []; interns = []; intern_counter = 0; big_counter = 0;

	for pos in all_positions:
		if "intern" in pos.title or "Intern" in pos.title:
			interns.append({'title':pos.title, 'entity_name':pos.entity.name, 'person':pos.person.profile.full_name()})
			if pos.start_date and pos.end_date:
				duration = pos.end_date - pos.start_date
				intern_total += duration.days
				intern_counter += 1

		else:
			bigs.append({'title':pos.title, 'entity_name':pos.entity.name, 'person':pos.person.profile.full_name()})
			if pos.start_date and pos.end_date:
				duration = pos.end_date - pos.start_date
				big_total += duration.days
				big_counter += 1

	data = {
		'interns':interns,
		'job_holders':bigs,
		# 'intern_avg_duration':intern_total/intern_counter,
		# 'job_avg_duration':big_total/big_counter,
	}

	return data



# code taken w/ few modifications from entities.views
# Note: 'saved_positions' = saved_position objects
def _get_positions_for_path(saved_positions, extra_info):
	"""
	Returns JSON format of all user positions, with possible anonymity
	"""

	positions = []
	index_list = []
	for saved_pos in saved_positions:
		positions.append(saved_pos.position)
		index_list.append(saved_pos.index)

	if positions:
		formatted_positions = []
		i = 0
		for p in positions:

			domains = p.entity.domains.all()
			if domains:
				domain = domains[0].name
			else:
				domain = None
			
			# Education
			if p.type == "education":
				if p.degree is not None and p.field is not None:
					title = p.degree + ", " + p.field
				elif p.degree is not None:
					title = p.degree
				elif p.field is not None:
					title = p.field
				else:
					title = None
				attribs = {
					'domain':domain,
					'duration':p.duration(),
					'title':title,
					'type':'education'
				}
			# Organization
			else:
				attribs = {
					'type':'org',
					'domain': domain,
					'duration':p.duration(),
					'title':p.title,
				}

			# Clay: addition of description if avail
			if (p.description):
				attribs['description'] = p.description
			else:
				attribs['description'] = None

			# Clay: also need the uniq id for saving
			attribs['id'] = p.id

			
			if p.start_date is not None:
				attribs['start_date'] = p.start_date.strftime("%m/%Y")
			if p.end_date is not None:
				attribs['end_date'] = p.end_date.strftime("%m/%Y")
			
			# Clay: extra line fixes case in which domain==None
			if domain:
				attribs['co_name'] = domain + " company"
			else:
				attribs['co_name'] = p.entity.name

			attribs['index'] = index_list[i]

			# now, get interesting pos information
			metadata = []
			# other jobs at this company:
			other_jobs = Position.objects.filter(entity__name=p.entity.name).exclude(person=p.person)
			for job in other_jobs:
				person = Profile.objects.get(user=job.person)
				job_info = {
					'person_name':person.first_name + ' ' + person.last_name,
					'person_id':job.person.id,
					'job_title':job.title,
				}
				metadata.append(job_info)

			
			attribs['metadata'] = metadata

			formatted_positions.append(attribs)
			i += 1

		return formatted_positions
	# if no positions, return None
	return None


# Note, this uses the old school Position object, not Saved_Position
def _ready_position_for_proto(p):
		
	array = []
	if not p.title:
		return None

	if p.type == 'education':
		return None

	attribs = {
		'title':p.title,
		'id':p.id,
	}

	array.append(attribs)
	return array


def _get_paths_in_career_alt(user, career):

	paths = {}
	overview = {}

	# Need: positions related to query
	career_singleton_array = [career] #needed to make this query work
	positions_in_career = Position.objects.filter(careers__in=career_singleton_array).select_related('entity', 'person', 'person__profile')

	# Check this fxn to see how it works
	users_list, user_ids = _get_users_in_network(user)

	## ** DST's ** ##

	# Used to get length of sets
	all_user_set = set()
	all_co_set = set()
	network_user_set = set()
	network_pos_counter = 0
	network_co_set = set()

	# Return DST's for 'Network'
	network_people = []
	network_cos = []
	network_pos = []

	# Return DST's for 'Prosperime Community'
	all_people = []
	all_cos = []
	all_pos = []

	# Used for Big Players
	network_entities_dict = {}
	all_entities_dict = {}

	for pos in positions_in_career:

		pos_data = {
			'id':pos.id,
			'title':pos.title,
			'co_name':pos.entity.name,
			'owner':pos.person.profile.full_name(),
			'owner_id':pos.person.id,
			'logo_path':pos.entity.default_logo(),
			# 'logo_path':pos.entity.logo,
		}

		co_data = {
			# count logo id people name
			'name':pos.entity.name,
			'id':pos.entity.id,
			'logo_path':pos.entity.default_logo(),
			# 'logo_path':pos.entity.logo,
			'people':None,
		}

		# Format End Dates for person_data object
		if pos.start_date is not None:
			start_date = pos.start_date.strftime("%m/%Y")
		else:
			start_date = None

		if pos.end_date is not None:
			end_date = pos.end_date.strftime("%m/%Y")
		else:
			end_date = "Current"

		person_data = {
			'name':pos.person.profile.full_name(),
			'id':pos.person.id,
			#'latest_position':pos.person.profile.latest_position(),
			'pos_title':pos.title,
			'pos_co_name':pos.entity.name,
			'pos_id':pos.id,
			'pos_start_date':start_date,
			'pos_end_date':end_date,
			'profile_pic':pos.person.profile.default_profile_pic(),
			# 'profile_pic':pos.person.profile.profile_pic,
		}

		# Network & All
		if pos.person.id in user_ids:
			
			# Positions
			network_pos_counter += 1
			network_pos.append(pos_data)
			all_pos.append(pos_data)

			# People
			network_user_set.add(pos.person.id) 
			all_user_set.add(pos.person.id)
			network_people.append(person_data)
			all_people.append(person_data)

			# Companies
			
			# No Duplicates
			if pos.entity.name not in network_co_set:
				network_cos.append(co_data)
			if pos.entity.name not in all_co_set:
				all_cos.append(co_data)
			
			# network_co_set.add(pos.entity.id) # should be id, but crappy db data
			#all_co_set.add(pos.entity.id) # should be id, but crappy db data
			network_co_set.add(pos.entity.name)
			all_co_set.add(pos.entity.name)

			# Entities Dict for BigPlayers
			## Could rearrange this loop structure for minor boost
			if pos.entity.id in network_entities_dict:
				network_entities_dict[pos.entity.id]['count'] += 1
			else:
				network_entities_dict[pos.entity.id] = {
					'count':1,
					'name':pos.entity.name,
					'id':pos.entity.id,
				}

			if pos.entity.id in all_entities_dict:
				all_entities_dict[pos.entity.id]['count'] += 1
			else:
				all_entities_dict[pos.entity.id] = {
					'count':1,
					'name':pos.entity.name,
					'id':pos.entity.id,
				}

		# Only All
		else:

			# Positions
			all_pos.append(pos_data)

			# People
			all_user_set.add(pos.person.id)
			all_people.append(person_data)

			# Companies
			if pos.entity.name not in all_co_set:
				all_cos.append(co_data)

			# all_co_set.add(pos.entity.id) # should be id, but crappy db data
			all_co_set.add(pos.entity.name)

			# Entities Dict for BigPlayers
			if pos.entity.id in all_entities_dict:
				all_entities_dict[pos.entity.id]['count'] += 1
			else:
				all_entities_dict[pos.entity.id] = {
					'count':1,
				}

	# People
	paths['network'] = network_people
	paths['all'] = all_people

	# Positions
	paths['networkPositions'] = network_pos
	paths['allPositions'] = all_pos
 
	# Companies
	paths['networkCompanies'] = network_cos
	paths['allCompanies'] = all_cos	

	## Overview
	overview['network'] = {
		'num_people': len(network_user_set),
		'num_pos': network_pos_counter,
		'num_cos': len(network_co_set),
	}

	overview['all'] = {
		'num_people':len(all_user_set),
		'num_pos':len(positions_in_career),
		'num_cos':len(all_co_set),
	}

	# Big Players
	network_entities_dict = sorted(network_entities_dict.iteritems(), key=lambda x: x[1]['count'], reverse=True)
	overview['network']['bigplayers'] = network_entities_dict[:3]

	all_entities_dict = sorted(all_entities_dict.iteritems(), key=lambda x: x[1]['count'], reverse=True)
	overview['all']['bigplayers'] = all_entities_dict[:3]

	# Add Overview to Paths
	paths['overview'] = {
		'network' : overview['network'],
		'all': overview['all'],
	}

	return paths

def _get_users_in_network(user,**filters):

	# get schools from user
	schools = Entity.objects.filter(li_type="school",positions__person=user,positions__type="education").distinct()
	
	# get all connected users and those from the same schools
	
	users = User.objects.select_related('profile','pictures').values('pk','positions__careers','profile__first_name','profile__last_name','profile__pictures__pic').filter(Q(profile__in=user.profile.connections.all()) | (Q(positions__entity__in=schools))).distinct()
	# if filters['positions']:
	# 	users = users.filter(positions__title__in=filters['positions'])
	# if filters['locations']:
	# 	users = users.filter(positions__entity__office__city__in=filters['locations'])
	
	users_list = [{'id':u['pk'],'first_name':u['profile__first_name'],'last_name':u['profile__last_name'],'profile_pic':u['profile__pictures__pic'],'careers':u['positions__careers']} for u in users]	
	user_ids = [u['id'] for u in users_list]

	user_ids = set(user_ids)
	return (users_list, user_ids)

def _date_to_int(date):

	if date is None:
		return None

	year = str(date.year)[2:]
	month = str(date.month)

	if len(month) == 1:
		return year + '0' + month
	else:
		return year + month



#######################
###### Dev Only #######
#######################

def getIndustriesForUser(user_id):
	user = User.objects.get(pk=user_id)
	positions = Position.objects.filter(person=user).prefetch_related().select_related('entity') # check this

	industries = []
	seen_before = set()
	for p in positions:
		p_entity = p.entity
		p_industries = p_entity.domains.all()
		print p_industries
		for i in p_industries:
			if i.id not in seen_before:
				seen_before.add(i.id)
				industries.append(i)

	print 'Industry Report for: ' + user.profile.full_name()
	print '####################'
	print 'Positions: '
	for p in positions:
		if p.title is not None:
			print p.title + ' - ' + p.entity.name
		else:
			print 'n/a - ' + p.entity.name 
	print '####################'
	print 'Industries:'
	for i in industries:
		print i.name


def manual_save(user_id, path_id, pos_id):

	path = SavedPath.objects.get(id=path_id)
	position = Position.objects.get(id=pos_id)

	saved_position = SavedPosition()
	saved_position.position = position
	saved_position.path = path
	saved_position.index = path.get_next_index()
	saved_position.save()	

	return 'Success'

class Object(object):
	pass
