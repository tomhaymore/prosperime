# from Python
import datetime
import math

# from Django
# from django.contrib.auth import authenticate, login as auth_login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import simplejson
from django.contrib import messages
from django.core.cache import cache


# Prosperime
from entities.models import Entity, Office, Financing, Industry
from accounts.models import Picture, Profile
from careers.models import SavedPath, CareerDecision, Position, Career
#from entities.careerlib import CareerSimBase
import careers.careerlib as careerlib

### DEPRECATED ###
# @login_required
def home(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('welcome')
	data = {}
	user = request.user

	data['user_careers'] = Career.objects.filter(positions__person__id=user.id)
	data['saved_paths'] = SavedPath.objects.filter(owner=user)
	data['top_careers'] = []
	data['career_decisions'] = CareerDecision.objects.all()


	return render_to_response('home.html',data,context_instance=RequestContext(request))

def contact(request):

	data = {}

	return render_to_response('contact.html', data, context_instance=RequestContext(request))



def welcome(request):
	if request.user.is_authenticated():
		# user is logged in, display personalized information
		return HttpResponseRedirect('/home')
	return render_to_response('welcome.html',context_instance=RequestContext(request))

# view for org profiles
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


def _get_paths_in_career(user,career):

	# initialize overview array
	overview = {}
	paths = {}

	# get users in network
	users_list, user_ids = _get_users_in_network(user)

	network_people = User.objects.prefetch_related().select_related('positions','entities','accounts').filter(id__in=user_ids,positions__careers=career).annotate(no_of_pos=Count('positions__pk')).order_by('-no_of_pos').distinct()
	# CAUTION--values() can return multiple records when requesting M2M values; make sure to reduce
	# network_people = User.objects.values('id','profile__headline','profile__first_name','profile__last_name','profile__pictures__pic','positions__entity__id','positions__entity__name').annotate(no_of_pos=Count('positions__id')).order_by('-no_of_pos')

	# Clayton -- need to uniqify this list, b/c lots of wasted time
	#	parsing duplicate people ... EDIT: not the problem, problem is
	#	duplicate positions!
	# network_people = _order_preserving_uniquify(network_people)

	network_people_dict = {}
	num_pos = 0
	# entities = []
	entities = set()
	entities_dict = {}
	num_cos = 0
	network_positions = []
	counter = 0

	## Network
	for p in network_people:
		# num_pos += len(p.positions.all())
		people_seen = set()
		positions_seen = set()

		for pos in p.positions.all():
			num_pos += 1
			# entities.append(pos.entity.id)
			entities.add(pos.entity.id)

			# if pos in career, add to positions
			# 	additionally, impose 30 position cap
			
			if career in pos.careers.all():
				counter += 1
				print counter
			 	if len(network_positions) < 30:
					# check if seen already (avoid duplicates)
					if pos.id not in positions_seen:
						positions_seen.add(pos.id)
						network_positions.append({
							'id':pos.id,
							'title':pos.title,
							'co_name':pos.entity.name,
							'owner':pos.person.profile.full_name(),
							'owner_id':pos.person.id,
							'logo_path':pos.entity.default_logo(),
						})

		
			if pos.entity.name in entities_dict:
				entities_dict[pos.entity.name]['count'] += 1

				# check if person seen already (avoid duplicates)
				# 	additionally, cap people @ 5 for now
				if p.id not in people_seen and len(entities_dict[pos.entity.name]['people']) < 6:
					
					person_dict = {
						'name':p.profile.full_name(),
						'id':p.id,
					}
					entities_dict[pos.entity.name]['people'].append(person_dict)
					people_seen.add(p.id)

			else:
				people_list = [{
					'name':p.profile.full_name(),
					'id':p.id,
				}]
				
				entities_dict[pos.entity.name] = {
					'count' : 1,
					'id':pos.entity.id,
					'logo':pos.entity.default_logo(),
					'people':people_list,	
				}

	# for p in network_people:
	# 	# check to see if user is already in the dict
	# 	if p['id'] not in network_people_dict:
	# 		network_people_dict[p['id']] = {
	# 			'full_name': p['profile__first_name'] + " " + p['profile__last_name'],
	# 			'headline': p['profile__headline']
	# 		}
	# 	# check each record to make sure the profile pic gets picked up
	# 	if 'profile__pictures__pic' in p:
	# 		network_people_dict[p['id']]['pic'] = p['profile__pictures__pic']
	# 	if 'positions__entity__id' in p:
	# 	# increment the position counter
	# 		num_pos += 1
	# 		if p['positions__entity__name'] in entities_dict:
	# 			entities_dict[p['positions__entity__name']]['count'] += 1
	# 		else:
	# 			entities_dict[p['positions__entity__name']] = {
	# 				'count':1,
	# 				'id':p['positions__entity__name']
	# 			}


	# num_cos = len(set(entities))
	num_cos = len(entities)

	overview['network'] = {
		'num_people':len(network_people),
		'num_pos':num_pos,
		'num_cos':num_cos
	}

	all_people = User.objects.select_related('positions').filter(positions__careers=career).annotate(no_of_pos=Count('positions__pk')).order_by('-no_of_pos').distinct()

	num_pos = 0
	#entities = []
	entities = set()
	all_entities_dict = {}
	all_positions = []
	num_cos = 0

	## ALL
	# loop through all positions, identify those that belong to connections
	for p in all_people:
		# check if position held by 
		if p.id in user_ids:
			p.connected = True
		else:
			p.connected = False

		#num_pos += len(p.positions.all())
		for pos in p.positions.all():
			num_pos += 1
			if pos.entity.name in all_entities_dict:
				all_entities_dict[pos.entity.name]['count'] += 1
			else:
				all_entities_dict[pos.entity.name] = {
					'id':pos.entity.id,
					'count':1
				}
			# entities.append(pos.entity.id)
			entities.add(pos.entity.id)

	#num_cos = len(set(entities))
	num_cos = len(entities)

	overview['all'] = {
		'num_people':len(all_people),
		'num_pos':num_pos,
		'num_cos':num_cos
	}

	# Network Entities Top 3
	entities_dict = sorted(entities_dict.iteritems(), key=lambda x: x[1]['count'], reverse=True)
	overview['network']['bigplayers'] = entities_dict[:3]

	# All Entities Top 3
	all_entities_dict = sorted(all_entities_dict.iteritems(), key=lambda x: x[1]['count'], reverse=True)
	overview['all']['bigplayers'] = all_entities_dict[:3]

	# People in Network, All
	paths['network'] = network_people
	paths['all'] = all_people

	# TRIAL - adding entities information
	paths['networkOrgs'] = entities_dict
	paths['allOrgs'] = all_entities_dict

	# TRIAL - adding positions information
	paths['networkPositions'] = network_positions
	paths['allPositions'] = all_positions

	# Returns nested dict
	paths['overview'] = {
		'network' : overview['network'],
		'all':overview['all'],
		}

	# return paths, overview
	return paths


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
			#'logo_path':pos.entity.default_logo(),
			'logo_path':pos.entity.logo,
		}

		co_data = {
			# count logo id people name
			'name':pos.entity.name,
			'id':pos.entity.id,
			#'logo_path':pos.entity.default_logo(),
			'logo_path':pos.entity.logo,
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
			#'profile_pic':pos.person.profile.default_profile_pic(),
			'profile_pic':pos.person.profile.profile_pic,
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
	paths['networkPeople'] = network_people
	paths['allPeople'] = all_people

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

def search(request):
	
	# test if user is authenticated
	# show what?
	# print request.user.li_linked()
	data = {}
	if 'msg' in request.session:
		data['msg'] = request.session['msg']
	if request.user.is_authenticated():
		data['user'] = request.user

	# Clay: add saved paths here... not sure if this is where to do it
	#	but hey, it works
	# EDIT: add an array of path titles (we don't need the objects)
	saved_paths = SavedPath.objects.filter(owner=request.user)

	# if len(saved_paths) > 0:
	# 	path_titles = []
	# 	for path in saved_paths:
	# 		path_titles.append(path.title)

	# 	# Add path titles array
	# 	data['saved_paths'] = path_titles
	# 	print path_titles
		
	return render_to_response('entities/search.html',data,
		context_instance=RequestContext(request))

def companies(request):
	""" serves up JSON file of company search results """
	print 'hits companies'
	# initialize array of companies
	# companies = []
	# get search filters
	
	locationsSelected = request.GET.getlist('location')
	sectorsSelected = request.GET.getlist('sector')
	sizesSelected = request.GET.getlist('size')
	stagesSelected = request.GET.getlist('stage')

	companies = Entity.objects.values("name","summary","images__logo").filter(type="organization").annotate(freq=Count('financing__pk')).order_by('-freq')

	# companies = Entity.objects.values("name","summary")

	if locationsSelected:
		companies = companies.filter(office__city__in=locationsSelected)
	if sectorsSelected:
		companies = companies.filter(domains__name__in=sectorsSelected)
	if sizesSelected:
		# get dictionary of size ranges
		rgs = _get_size_filter(sizesSelected)
		# print rgs
		# setup complex query using size dict
		c = 0
		for rg in rgs:
			print rg
			if c == 0:
				q = Q(no_employees__gte=int(rg['lower']),no_employees__lte=int(rg['upper']))		
			else:
				q.add(Q(no_employees__gte=int(rg['lower']),no_employees__lte=int(rg['upper'])), Q.OR)
			c += 1
		companies = companies.filter(q)
	if stagesSelected:
		companies = companies.filter(financing__round__in=stagesSelected)

	# companies =  list(Entity.objects.filter(cb_type="company").values("full_name","summary","logo")[:20])
	print companies.query
	companies = list(companies[:20])
	return HttpResponse(simplejson.dumps(companies), mimetype="application/json")


# JSON dump - filters
def path_filters(request):
	""" serves up JSON object of params for path searches """

	# initialize array for all filters
	filters = []

	# get search filters
	locationsSelected = request.GET.getlist('location')
	sectorsSelected = request.GET.getlist('sector')
	positionsSelected = request.GET.getlist('position')
	careersSelected = request.GET.getlist('career')
	orgsSelected = request.GET.getlist('org')

	# set base filters

	# set career filters
	careersBase = User.objects.select_related().values("positions__careers__long_name").annotate(freq=Count('pk')).order_by('-freq').distinct()
	careersFiltered = careersBase

	if locationsSelected:
		careersFiltered = careersFiltered.filter(positions__entity__office__city__in=locationsSelected)

	if sectorsSelected:
		careersFiltered = careersFiltered.filter(positions__entity__domains__name__in=sectorsSelected)

	if positionsSelected:
		careersFiltered = careersFiltered.filter(positions__title__in=positionsSelected)

	if orgsSelected:
		careersFiltered = careersFiltered.filter(positions__entity__name__in=orgsSelected)

	careersBase = careersBase[:10]
	
	careersFilteredDict = {}
	for c in careersFiltered:
		careersFilteredDict[c['positions__careers__long_name']] = c['freq']

	for c in careersBase:
		# make sure it doesn't have a null value
		if c['positions__careers__long_name']:
			# get count from filtered dict
			if c['positions__careers__long_name'] in careersFilteredDict:
				freq = careersFilteredDict[c['positions__careers__long_name']]
			else:
				freq = 0
			# check to see if the value should be selected
			if c['positions__careers__long_name'] in careersSelected:
				filters.append({'name':c['positions__careers__long_name'],'value':c['positions__careers__long_name'],'category':'Career','count':freq,'selected':True})
			else:
				filters.append({'name':c['positions__careers__long_name'],'value':c['positions__careers__long_name'],'category':'Career','count':freq,'selected':None})

	# set organization filters
	orgsBase = User.objects.values("positions__entity__name").annotate(freq=Count('pk')).order_by('-freq').distinct()
	orgsFiltered = orgsBase

	if locationsSelected:
		orgsFiltered = orgsFiltered.filter(positions__entity__office__city__in=locationsSelected)

	if sectorsSelected:
		orgsFiltered = orgsFiltered.filter(positions__entity__domains__name__in=sectorsSelected)

	if positionsSelected:
		orgsFiltered = orgsFiltered.filter(positions__title__in=positionsSelected)

	if careersSelected:
		orgsFiltered = orgsFiltered.filter(positions__careers__long_name__in=careersSelected)

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
	locationsBase = User.objects.values("positions__entity__office__city").annotate(freq=Count('pk')).order_by('-freq').distinct()
	locationsFiltered = locationsBase

	if positionsSelected:
		locationsFiltered = locationsFiltered.filter(positions__title__in=positionsSelected)
	
	if sectorsSelected:
		locationsFiltered = locationsFiltered.filter(positions__entity__domains__name__in=sectorsSelected)

	if careersSelected:
		locationsFiltered = locationsFiltered.filter(positions__careers__long_name__in=careersSelected)

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
	# sectorsBase = User.objects.values('positions__entity__domains__name').annotate(freq=Count('pk')).distinct()
	# sectorsFiltered = sectorsBase[:10]

	# if locationsSelected:
	# 	sectorsFiltered = sectorsFiltered.filter(positions__entity__office__city__in=locationsSelected)

	# if positionsSelected:
	# 	sectorsFiltered = sectorsFiltered.filter(positions__title__in=positionsSelected)

	# sectorsFilteredDict = {}
	# for s in sectorsFiltered:
	# 	sectorsFilteredDict[s['positions__entity__domains__name']] = s['freq']

	# for s in sectorsBase:
	# 	# make sure it doesn't have a null value
	# 	if s['positions__entity__domains__name']:
	# 		# get count from sectorsFilteredDict
	# 		if s['positions__entity__domains__name'] in sectorsFilteredDict:
	# 			freq = sectorsFilteredDict[s['positions__entity__domains__name']]
	# 		else:
	# 			freq = 0
	# 		name = " ".join(word.capitalize() for word in s['positions__entity__domains__name'].replace("_"," ").split())
	# 		# check to see if the value should be selected
	# 		if s['positions__entity__domains__name'] in sectorsSelected:
	# 			filters.append({'name':name,'value':s['positions__entity__domains__name'],'category':'Sector','count':freq,'selected':True})
	# 		else:
	# 			filters.append({'name':name,'value':s['positions__entity__domains__name'],'category':'Sector','count':freq,'selected':None})
	
	# # get position filters
	# positionsBase = User.objects.values('positions__title').annotate(freq=Count('pk')).distinct()
	# positionsFiltered = positionsBase[:10]

	# if locationsSelected:
	# 	positionsFiltered = positionsFiltered.filter(positions__entity__office__city__in=locationsSelected)
	# if sectorsSelected:
	# 	positionsSelected = positionsFiltered.filter(positions__entity__domains__name__in=sectorsSelected)

	# positionsFilteredDict = {}
	# for p in positionsFiltered:
	# 	positionsFilteredDict[p['positions__title']] = p['freq']

	# for p in positionsBase:
	# 	# make sure it doesn't have a null value
	# 	if p['positions__title']:
	# 		# get count from positionsFilteredDict
	# 		if p['positions__title'] in positionsFilteredDict:
	# 			freq = positionsFilteredDict[p['positions__title']]
	# 		else:
	# 			freq = 0
	# 		# check to see if the value should be selected
	# 		if p['positions__title'] in positionsSelected:
	# 			selected = True
	# 		else:
	# 			selected = False
	# 		filters.append({'name':p['positions__title'],'value':p['positions__title'],'category':'Positions','count':freq,'selected':selected})

	# render response
	return HttpResponse(simplejson.dumps(filters), mimetype="application/json")


# CLAY: json dump of all filters
def filters(request):
	print 'hits filters'
	""" serves up JSON file of params for searches """
	# initialize array for all filters
	filters = []
	
	# get search filters
	locationsSelected = request.GET.getlist('location')
	sectorsSelected = request.GET.getlist('sector')
	sizesSelected = request.GET.getlist('size')
	stagesSelected = request.GET.getlist('stage')

	# print sizesSelected

	# set base search filter
	# locationsBase = Office.objects.values("city").annotate(freq=Count('pk')).order_by('-freq').distinct()[:10]
	locationsBase = Office.objects.values("city").annotate(freq=Count('pk')).order_by('-freq').distinct()
	locationsFiltered = locationsBase

	# get a count value for each location base on filters

	if stagesSelected:
		#print stagesSelected
		locationsFiltered = locationsFiltered.filter(entity__financing__round__in=stagesSelected)
		# locationsFiltered = Office.objects.filter(entity__financing__round__in=stagesSelected).values("city").annotate(freq=Count('pk')).order_by('-freq').distinct()[:10]
		# print locationsFiltered.query
	if sectorsSelected:
		locationsFiltered = locationsFiltered.filter(entity__domains__name__in=sectorsSelected)
		# print locationsFiltered.query
	if sizesSelected:
		# get dictionary of size ranges
		rgs = _get_size_filter(sizesSelected)
		# print rgs
		# setup complex query using size dict
		c = 0
		for rg in rgs:
			print rg
			if c == 0:
				q = Q(entity__no_employees__gte=int(rg['lower']),entity__no_employees__lte=int(rg['upper']))		
			else:
				q.add(Q(entity__no_employees__gte=int(rg['lower']),entity__no_employees__lte=int(rg['upper'])), Q.OR)
			c += 1
		locationsFiltered = locationsFiltered.filter(q)
		# print locationsFiltered.query
	# if sectorsSelected:
	# 	locationsFiltered = Office.objects.filter(entity__domain__in=sectorsSelected).values("city").annotate(freq=Count('pk')).order_by('-freq').distinct()[:10]
	# else:
	#  	locationsFiltered = locationsBase
	# print locations

	locationsBase = locationsBase[:10]
	# print locationsBase.query
	

	locationsFilteredDict = {}
	for l in locationsFiltered:
		locationsFilteredDict[l['city']] = l['freq']
	
	for l in locationsBase:
		# make sure it doesn't have a null value
		if l['city']:
			# get count from locationsFilteredDict
			if l['city'] in locationsFilteredDict:
				freq = locationsFilteredDict[l['city']]
			else:
				freq = 0
			# check to see if the value should be selected
			if l['city'] in locationsSelected:
				filters.append({'name':l['city'],'value':l['city'],'category':'Location','count':freq,'selected':True})
			else:
				filters.append({'name':l['city'],'value':l['city'],'category':'Location','count':freq,'selected':None})
	
	# get a list of all sectors
	# sectorsBase = Entity.objects.values('domain').annotate(freq=Count('pk')).distinct()
	sectorsBase = Industry.objects.values('name').annotate(freq=Count('pk')).distinct()
	sectorsFiltered = sectorsBase[:10]

	# if locationsSelected:
	# 	sectorsFiltered = Entity.objects.filter(office__city__in=locationsSelected).values('domain').annotate(freq=Count('pk')).distinct()
	# else:
	# 	sectorsFiltered = Entity.objects.values('domain').annotate(freq=Count('pk')).distinct()
	
	if locationsSelected:
		# sectorsFiltered = sectorsFiltered.filter(entity__office__city__in=locationsSelected)
		entitiesFilteredByLoaction = Entity.objects.filter(office__city__in=locationsSelected)
		sectorsFiltered = sectorsFiltered.filter(entity__in=entitiesFilteredByLoaction)
		# print sectorsFiltered.query
	if stagesSelected:
		sectorsFiltered = sectorsFiltered.filter(financing__round__in=stagesSelected)
	if sizesSelected:
		# get dictionary of size ranges
		rgs = _get_size_filter(sizesSelected)
		# print rgs
		# setup complex query using size dict
		c = 0
		for rg in rgs:
			print rg
			if c == 0:
				q = Q(entity__no_employees__gte=int(rg['lower']),entity__no_employees__lte=int(rg['upper']))		
			else:
				q.add(Q(entity__no_employees__gte=int(rg['lower']),entity__no_employees__lte=int(rg['upper'])), Q.OR)
			c += 1
		sectorsFiltered = sectorsFiltered.filter(q)

	sectorsFilteredDict = {}
	for l in sectorsFiltered:
		sectorsFilteredDict[l['name']] = l['freq']

	for s in sectorsBase:
		# make sure it doesn't have a null value
		if s['name']:
			# get count from sectorsFilteredDict
			if s['name'] in sectorsFilteredDict:
				freq = sectorsFilteredDict[s['name']]
			else:
				freq = 0
			name = " ".join(word.capitalize() for word in s['name'].replace("_"," ").split())
			# check to see if the value should be selected
			if s['name'] in sectorsSelected:
				filters.append({'name':name,'value':s['name'],'category':'Sector','count':freq,'selected':True})
			else:
				filters.append({'name':name,'value':s['name'],'category':'Sector','count':freq,'selected':None})
	
	sizes = {
		'a':'1-10',
		'b':'11-25',
		'c':'26-50',
		'd':'51-100',
		'e':'101-250',
		'f':'251-500',
		'g':'501+'
	}
	for k,v in iter(sorted(sizes.iteritems())):
		if sizesSelected and k in sizesSelected:
			filters.append({'name':v,'value':k,'category':'Size','count':None,'selected':True})
		else:
			filters.append({'name':v,'value':k,'category':'Size','count':None,'selected':None})
	
	stages = ['seed','a','b','c','d','e','f','g','h','IPO']
	for s in stages:
		if stagesSelected and s in stagesSelected:
			filters.append({'name':s,'value':s.lower(),'category':'Stage','count':None,'selected':True})
		else:
			filters.append({'name':s,'value':s.lower(),'category':'Stage','count':None,'selected':None})
	
	# render response
	return HttpResponse(simplejson.dumps(filters), mimetype="application/json")


# JSON dump
def paths(request):
	
	# get search filters
	careersSelected = request.GET.getlist('career')
	orgsSelected = request.GET.getlist('org')
	locationsSelected = request.GET.getlist('location')
	sectorsSelected = request.GET.getlist('sector')
	positionsSelected = request.GET.getlist('position')

	full_filters_string = "_".join(careersSelected + orgsSelected + locationsSelected)

	# check to see if cached
	paths = cache.get("search_paths_" + full_filters_string)
	if paths is None:
		print 'missed cache'
		# fetch and recache


		# initialize array of paths
		paths = []
		

		# fetch all users
		# TODO someway to order this to retrieve those most relevant
		users = User.objects.annotate(no_of_pos=Count('positions__pk')).exclude(pk=request.user.id).order_by('-no_of_pos')

		if locationsSelected:
			users = users.filter(positions__entity__office__city__in=locationsSelected)
		if sectorsSelected:
			users = users.filter(positions__entity__domains__name__in=sectorsSelected)
		if positionsSelected:
			users = users.filter(positions__title_in=positionsSelected)
		if careersSelected:
			users = users.filter(positions__careers__long_name__in=careersSelected)
		if orgsSelected:
			users = users.filter(positions__entity__name__in=orgsSelected)


		users = users[:20]

		# loop through all positions, identify those that belong to connections
		for u in users:
			# reset careers array
			careers = []
			# check if position held by 
			if request.user.profile in u.profile.connections.all():
				id = u.id
				connected = True
				name = u.profile.full_name()
				current_position = _get_latest_position(u)
				profile_pic = _get_profile_pic(u.profile)
				for p in u.positions.all():
					for c in p.careers.all():
						careers.append({'name':c.long_name,'id':c.id})
				# if current_position is not None:
				# 	positions = _get_positions_for_path(u.positions.all())
				# else:
				# 	positions = None
			else:
				id = u.id
				connected = False
				name = None
				current_position = _get_latest_position(u,anon=True)
				# positions = _get_positions_for_path(u.positions.all(),anon=True)
				profile_pic = None
				for c in u.profile.get_all_careers():
					careers.append({'name':c.long_name,'id':c.id})
				# need to convert positions to anonymous

			# paths.append({'id':u.id,'profile_pic':profile_pic,'full_name':name,'current_position':current_position,'positions':positions,'connected':connected})
			paths.append({'id':u.id,'profile_pic':profile_pic,'full_name':name,'current_position':current_position,'careers':careers,'connected':connected})
			# paths.append({'full_name':name,'current_position':current_position,'connected':connected})
			# store in cache
			cache.set("search_paths_" + full_filters_string,paths,10)
	else:
		print 'hit cache'

	return HttpResponse(simplejson.dumps(paths))

def path(request,user_id):
	print 'hits path'
	# fetch path
	positions = Position.objects.filter(person__id=user_id)
	# initialize arrays
	path_even = {}
	path_odd = {}
	path = {}
	# loop through positions
	i = 0
	prev_employer = None
	for p in positions:
		# check if even
		if i % 2 == 0:
			flag = "even"
		else:
			flag = "odd"
		# check if same employer as previous position
		if p.entity == prev_employer:
			# append to current box rather than create a new one
			path[p.entity.name].append({'title':p.title,'duration':p.duration(),'start_date':p.safe_start_time(),'end_date':p.safe_end_time()})
		else:
			# add new box
			path[p.entity.name] = [{'title':p.title,'duration':p.duration(),'start_date':p.safe_start_time(),'end_date':p.safe_end_time()}]
		prev_employer = p.entity
		i += 1

	# convert to list
	# path = list(path)
	odd = [1,3,5,7,9,11,13,15,17,19]
	even = [0,2,4,6,8,10,12,14,16,18]
	# return HttpResponse(simplejson.dumps(path),mimetype="application/json")
	return render_to_response('entities/path_viz.html',{'path':path,'odd':odd,'even':even},context_instance=RequestContext(request))

def career_filters(request):
	
	""" serves up JSON object of params for path searches """

	# initialize array for all filters
	filters = []

	# get search filters
	locationsSelected = request.GET.getlist('location')
	# sectorsSelected = request.GET.getlist('sector')
	positionsSelected = request.GET.getlist('position')

	# set base filters

	# set location filters
	locationsBase = User.objects.values("positions__entity__office__city").annotate(freq=Count('pk')).order_by('-freq').distinct()
	locationsFiltered = locationsBase

	if positionsSelected:
		locationsFiltered = locationsFiltered.filter(positions__title__in=positionsSelected)
	
	# if sectorsSelected:
	# 	locationsFiltered = locationsFiltered.filter(positions__entity__domains__name__in=sectorsSelected)

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
	# sectorsBase = User.objects.values('positions__entity__domains__name').annotate(freq=Count('pk')).distinct()
	# sectorsFiltered = sectorsBase

	# if locationsSelected:
	# 	sectorsFiltered = sectorsFiltered.filter(positions__entity__office__city__in=locationsSelected)

	# if positionsSelected:
	# 	sectorsFiltered = sectorsFiltered.filter(positions__title__in=positionsSelected)

	# sectorsFilteredDict = {}
	# for s in sectorsFiltered:
	# 	sectorsFilteredDict[s['positions__entity__domains__name']] = s['freq']

	# for s in sectorsBase:
	# 	# make sure it doesn't have a null value
	# 	if s['positions__entity__domains__name']:
	# 		# get count from sectorsFilteredDict
	# 		if s['positions__entity__domains__name'] in sectorsFilteredDict:
	# 			freq = sectorsFilteredDict[s['positions__entity__domains__name']]
	# 		else:
	# 			freq = 0
	# 		name = " ".join(word.capitalize() for word in s['positions__entity__domains__name'].replace("_"," ").split())
	# 		# check to see if the value should be selected
	# 		if s['positions__entity__domains__name'] in sectorsSelected:
	# 			filters.append({'name':name,'value':s['positions__entity__domains__name'],'category':'Sector','count':freq,'selected':True})
	# 		else:
	# 			filters.append({'name':name,'value':s['positions__entity__domains__name'],'category':'Sector','count':freq,'selected':None})
	
	# get position filters
	positionsBase = User.objects.values('positions__title').annotate(freq=Count('pk')).distinct()
	positionsFiltered = positionsBase

	if locationsSelected:
		positionsFiltered = positionsFiltered.filter(positions__entity__office__city__in=locationsSelected)
	# if sectorsSelected:
	# 	positionsSelected = positionsFiltered.filter(positions__entity__domains__name__in=sectorsSelected)

	positionsBase = positionsBase[:20]

	positionsFilteredDict = {}
	for p in positionsFiltered:
		positionsFilteredDict[p['positions__title']] = p['freq']

	for p in positionsBase:
		# make sure it doesn't have a null value
		if p['positions__title']:
			# get count from positionsFilteredDict
			if p['positions__title'] in positionsFilteredDict:
				freq = positionsFilteredDict[p['positions__title']]
			else:
				freq = 0
			# check to see if the value should be selected
			if p['positions__title'] in positionsSelected:
				selected = True
			else:
				selected = False
			filters.append({'name':p['positions__title'],'value':p['positions__title'],'category':'Positions','count':freq,'selected':selected})

	# render response
	return HttpResponse(simplejson.dumps(filters), mimetype="application/json")

def careers(request):
	"""
	returns HTML fragment for career views
	"""
	# get search filters
	locationsSelected = request.GET.getlist('location')
	positionsSelected = request.GET.getlist('position')

	# initialize parent array of careers
	careers, overview = _get_careers_in_network(request.user,{'locations':locationsSelected,'positions':positionsSelected})

	return render_to_response('entities/careers.html',{'careers':careers,'overview':overview},context_instance=RequestContext(request))

def _get_careers_brief_similar(user,**filters):

	user_id = user.id

	careers_sim = CareerSimBase()

	users = careers_sim.find_similar_careers(user_id)
	
	careers = Career.objects.prefetch_related('positions', 'positions__entity', 'positions__person').filter(positions__person_id__in=users).annotate(num_people=Count('positions__person__pk',num_pos=Count('positions__pk'),num_cos=Count('positions__entity__pk'))).order_by('-num_people').distinct()[:10]

	for c in careers:
		people = []
		cos = []
		c.num_pos = len(c.positions.all())
		c.num_pos = 0
		for p in c.positions.all():
			people.append(p.person.id)
			cos.append(p.entity.id)
		c.num_people = len(set(people))
		c.num_cos = len(set(cos))

	# careers = sorted(careers.iteritems(),key=lambda x:x[0], reverse=True)

	return careers

def _get_careers_brief_all(**filters):

	careers = Career.objects.annotate(num_people=Count('positions__person__pk'),num_pos=Count('positions__pk'),num_cos=Count('positions__entity__pk')).distinct()

	return careers

def _get_careers_brief_in_network(user,**filters):

	cxns = user.profile.connections.all().values('user__id').select_related('user')

	# sets avoid duplicates
	users = set()
	users =[c['user__id'] for c in cxns]
	# for u in users:
	# 	print u

	# careers = Career.objects.filter(positions__person_id__in=users).annotate(num_people=Count('positions__person__pk'),num_pos=Count('positions__pk'),num_cos=Count('positions__entity__pk')).order_by('-num_people').distinct()
	# careers = Career.objects.prefetch_related('positions').filter(positions__person_id__in=users).annotate(num_people=Count('positions__person__pk',num_pos=Count('positions__pk'),num_cos=Count('positions__entity__pk'))).order_by('-num_people').distinct()[:10]
	careers_pos = Career.objects.filter(positions__person__id__in=users).values('id','short_name','long_name','positions__id')
	careers_ppl = Career.objects.filter(positions__person__id__in=users).values('id','short_name','long_name','positions__person_id')
	careers_orgs = Career.objects.filter(positions__person__id__in=users).values('id','short_name','long_name','positions__entity_id')

	careers_dict = {}

	for c in careers_pos:
		if c['id'] in careers_dict and 'positions' in careers_dict[c['id']]:
			careers_dict[c['id']]['positions'].append(c['positions__id'])
		elif c['id'] in careers_dict:
			careers_dict[c['id']]['positions'] = [c['positions_id']]
		else:
			careers_dict[c['id']] = {'positions':[c['positions__id']],'people':[],'orgs':[],'short_name':c['short_name'],'long_name':c['long_name']}

	for c in careers_ppl:
		if c['id'] in careers_dict and 'people' in careers_dict[c['id']]:
			careers_dict[c['id']]['people'].append(c['positions__person_id'])
		elif c['id'] in careers_dict:
			careers_dict[c['id']]['people'] = [c['positions__person_id']]
		else:
			careers_dict[c['id']] = {'people':[c['positions__person_id']],'people':[],'orgs':[],'short_name':c['short_name'],'long_name':c['long_name']}

	for c in careers_orgs:
		if c['id'] in careers_dict and 'orgs' in careers_dict[c['id']]:
			careers_dict[c['id']]['orgs'].append(c['positions__entity_id'])
		elif c['id'] in careers_dict:
			careers_dict[c['id']]['orgs'] = [c['positions__entity_id']]
		else:
			careers_dict[c['id']] = {'orgs':[c['positions__entity_id']],'people':[],'orgs':[],'short_name':c['short_name'],'long_name':c['long_name']}

	for k,v in careers_dict.items():
		v['num_pos'] = len(set(v['positions']))
		v['num_people'] = len(set(v['people']))
		v['num_cos'] = len(set(v['orgs']))

	careers = sorted(careers_dict.iteritems(),key=lambda (k,v):v['num_people'],reverse=True)

	# for c in careers:
	# 	people = []
	# 	cos = []
	# 	c.num_pos = len(c.positions.all())
	# 	for p in c.positions.all():
	# 		people.append(p.person.id)
	# 		cos.append(p.entity.id)
	# 	c.num_people = len(set(people))
	# 	c.num_cos = len(set(cos))

	# careers = sorted(careers.iteritems(),key=lambda x:x[0], reverse=True)

	return careers

def _get_careers_in_community(user,**filters):

	"""
	returns array of all careers in community, with out-of-network contacts anonymized
	"""

	# get all users
	
	users = User.objects.select_related('profile','pictures').values('pk','positions__careers','profile__first_name','profile__last_name','profile__pictures__pic').distinct()
	if filters['positions']:
		users = users.filter(positions__title__in=filters['positions'])
	if filters['locations']:
		users = users.filter(positions__entity__office__city__in=filters['locations'])
	
	# get focal user connections

	cxns = user.connections.all().values('id')

	# users_known_list = [{'id':u['pk'],'first_name':u['profile__first_name'],'last_name':u['profile__last_name'],'profile_pic':u['profile__pictures__pic'],'careers':u['positions__careers']} for u in users if u['pd'] in cxns]
	# users_anon_list = [{'id':u['pk'],'first_name':u['profile__first_name'],'last_name':u['profile__last_name'],'profile_pic':u['profile__pictures__pic'],'careers':u['positions__careers']} for u in users if u['pd'] not in cxns]	
	# users_list = users_known_list + users.anon_list
	users_list = [{'id':u['pk'],'first_name':u['profile__first_name'],'last_name':u['profile__last_name'],'profile_pic':u['profile__pictures__pic'],'careers':u['positions__careers']} for u in users]
	user_ids = [u['id'] for u in users_list]
	
	# fetch all positions
	positions = Position.objects.select_related('entity','industries').values('pk','title','entity__name','careers').exclude(type="education").distinct()
	# add positions filter
	if filters['positions']:
		positions = positions.filter(title__in=filters['positions'])
	if filters['locations']:
		positions = positions.filter(entity__office__city__in=filters['locations'])
	
	# positions_list = [{'title':p.title,'org':p.entity.name,'industries':p.industries()} for p in positions]
	positions_list = [{'id':p['pk'],'title':p['title'],'org':p['entity__name'],'careers':p['careers']} for p in positions]
	positions_ids = [p['id'] for p in positions_list]
	# get all related entities
	# entities = Entity.objects.filter(positions__person_id__in=user_ids)
	entities = Entity.objects.select_related('images','domains').values('pk','name','positions__careers','images__logo').distinct()
	# add location filters
	if filters['locations']:
		entities = entities.filter(office__city__in=filters['locations'])
	# entities_list = [{'name':e.name,'domains':e.domains.all(),'logo':e.default_logo()} for e in entities]
	entities_list = [{'id':e['pk'],'name':e['name'],'careers':e['positions__careers'],'logo':e['images__logo']} for e in entities]
	entities_ids = [e['id'] for e in entities_list]
	# get industries
	# industries = Industry.objects.filter(entity__in=entities_ids).annotate(freq=Count('entity__positions')).order_by('-freq').distinct()
	careers = Career.objects.values('id','short_name','long_name').filter(positions__id__in=positions_ids).distinct()

	# overview = {'users':'','positions':'','orgs':''}
	overview = {}
	overview['users'] = {'count':len(users_list),'values':users_list}
	overview['positions'] = {'count':len(positions_list),'values':positions_list}
	overview['orgs'] = {'count':len(entities_list),'values':entities_list}

	# initialize master career array
	careers_dict = {}
	o = 0
	for c in careers:
		
		if c['short_name']:
			c['name'] = c['short_name']
		else:
			c['name'] = c['long_name']

		careers_dict[c['name']] = {
					"order": o,
					# "users": {'count':len(users_list),'values':[u for u in users_list if i.id == u['domains']]},
					# "positions": {'count':len(positions_list),'values':[p for p in positions_list if i.id == p['industries']]},
					# "orgs": {'count':len(entities_list),'values':[org for org in entities_list if i.id == org['domains']]}
					"users": {'values':[u for u in users_list if c['id'] == u['careers']]},
					"positions": {'values':[p for p in positions_list if c['id'] == p['careers']]},
					"orgs": {'values':[org for org in entities_list if c['id'] == org['careers']]}
				}
		careers_dict[c['name']]['users']['count'] = len(careers_dict[c['name']]['users']['values'])
		careers_dict[c['name']]['positions']['count'] = len(careers_dict[c['name']]['positions']['values'])
		careers_dict[c['name']]['orgs']['count'] = len(careers_dict[c['name']]['orgs']['values'])
		o += 1

	# sorted_careers = sorted(careers_dict.iteritems(),key=lambda x: x[1]['order'],reverse=True)
	return careers_dict, overview

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

	return (users_list, user_ids)

def _get_positions_in_network(user_ids,**filters):
	
	# fetch all positions in user's network
	positions = Position.objects.select_related('entity','industries').values('pk','title','entity__name','careers').filter(person_id__in=user_ids).exclude(type="education").distinct()
	# add positions filter
	if filters['positions']:
		positions = positions.filter(title__in=filters['positions'])
	if filters['locations']:
		positions = positions.filter(entity__office__city__in=filters['locations'])
	# positions_list = [{'title':p.title,'org':p.entity.name,'industries':p.industries()} for p in positions]
	positions_list = [{'id':p['pk'],'title':p['title'],'org':p['entity__name'],'careers':p['careers']} for p in positions]
	positions_ids = [p['id'] for p in positions_list]

	return positions_list,positions_ids

def _get_careers_in_network(user,filters):
	"""
	returns array of all careers in user's network
	"""
	# get schools from user
	schools = Entity.objects.filter(li_type="school",positions__person=user,positions__type="education").distinct()
	
	# get all connected users and those from the same schools
	
	users = User.objects.select_related('profile','pictures').values('pk','positions__careers','profile__first_name','profile__last_name','profile__pictures__pic').filter(Q(profile__in=user.profile.connections.all()) | (Q(positions__entity__in=schools))).distinct()
	if filters['positions']:
		users = users.filter(positions__title__in=filters['positions'])
	if filters['locations']:
		users = users.filter(positions__entity__office__city__in=filters['locations'])
	
	users_list = [{'id':u['pk'],'first_name':u['profile__first_name'],'last_name':u['profile__last_name'],'profile_pic':u['profile__pictures__pic'],'careers':u['positions__careers']} for u in users]	
	user_ids = [u['id'] for u in users_list]
	
	# fetch all positions in user's network
	positions = Position.objects.select_related('entity','industries').values('pk','title','entity__name','careers').filter(person_id__in=user_ids).exclude(type="education").distinct()
	# add positions filter
	if filters['positions']:
		positions = positions.filter(title__in=filters['positions'])
	if filters['locations']:
		positions = positions.filter(entity__office__city__in=filters['locations'])
	# positions_list = [{'title':p.title,'org':p.entity.name,'industries':p.industries()} for p in positions]
	positions_list = [{'id':p['pk'],'title':p['title'],'org':p['entity__name'],'careers':p['careers']} for p in positions]
	positions_ids = [p['id'] for p in positions_list]
	# get all related entities
	# entities = Entity.objects.filter(positions__person_id__in=user_ids)
	entities = Entity.objects.select_related('images','domains').values('pk','name','positions__careers','images__logo').filter(positions__person_id__in=user_ids).distinct()
	# add location filters
	if filters['locations']:
		entities = entities.filter(office__city__in=filters['locations'])
	# entities_list = [{'name':e.name,'domains':e.domains.all(),'logo':e.default_logo()} for e in entities]
	entities_list = [{'id':e['pk'],'name':e['name'],'careers':e['positions__careers'],'logo':e['images__logo']} for e in entities]
	entities_ids = [e['id'] for e in entities_list]
	# get industries
	# industries = Industry.objects.filter(entity__in=entities_ids).annotate(freq=Count('entity__positions')).order_by('-freq').distinct()
	careers = Career.objects.values('id','short_name','long_name').filter(positions__id__in=positions_ids).distinct()

	# overview = {'users':'','positions':'','orgs':''}
	overview = {}
	overview['users'] = {'count':len(users_list),'values':users_list}
	overview['positions'] = {'count':len(positions_list),'values':positions_list}
	overview['orgs'] = {'count':len(entities_list),'values':entities_list}

	# initialize master career array
	careers_dict = {}
	o = 0
	for c in careers:
		
		if c['short_name']:
			c['name'] = c['short_name']
		else:
			c['name'] = c['long_name']

		careers_dict[c['name']] = {
					"order": o,
					# "users": {'count':len(users_list),'values':[u for u in users_list if i.id == u['domains']]},
					# "positions": {'count':len(positions_list),'values':[p for p in positions_list if i.id == p['industries']]},
					# "orgs": {'count':len(entities_list),'values':[org for org in entities_list if i.id == org['domains']]}
					"users": {'values':[u for u in users_list if c['id'] == u['careers']]},
					"positions": {'values':[p for p in positions_list if c['id'] == p['careers']]},
					"orgs": {'values':[org for org in entities_list if c['id'] == org['careers']]}
				}
		careers_dict[c['name']]['users']['count'] = len(careers_dict[c['name']]['users']['values'])
		careers_dict[c['name']]['positions']['count'] = len(careers_dict[c['name']]['positions']['values'])
		careers_dict[c['name']]['orgs']['count'] = len(careers_dict[c['name']]['orgs']['values'])
		o += 1

	# sorted_careers = sorted(careers_dict.iteritems(),key=lambda x: x[1]['order'],reverse=True)
	return careers_dict, overview


def _get_careers_in_network_old(user,filters):
	"""
	returns array of all careers in user's network
	"""
	# get schools from user
	schools = Entity.objects.filter(li_type="school",positions__person=user,positions__type="education").distinct()
	
	# get all connected users and those from the same schools
	# users = User.objects.select_related('profile','pictures').filter(Q(profile__in=user.profile.connections.all()) | Q(positions__entity__in=schools)).distinct()[:25]
	
	users = User.objects.select_related('profile','pictures').values('pk','positions__entity__domains','profile__first_name','profile__last_name','profile__pictures__pic').filter(Q(profile__in=user.profile.connections.all()) | Q(positions__entity__in=schools)).distinct()
	if filters['positions']:
		users = users.filter(positions__title__in=filters['positions'])
	if filters['locations']:
		users = users.filter(positions__entity__office__city__in=filters['locations'])
	# users_list = [{'full_name':u.profile.full_name(),'profile_pic':u.profile.default_profile_pic(),'domains':u.profile.domains} for u in users]	
	users_list = [{'id':u['pk'],'first_name':u['profile__first_name'],'last_name':u['profile__last_name'],'profile_pic':u['profile__pictures__pic'],'domains':u['positions__entity__domains']} for u in users]	
	user_ids = [u['id'] for u in users_list]
	# fetch all positions in user's network
	positions = Position.objects.select_related('entity','industries').values('title','entity__name','entity__domains').filter(person_id__in=user_ids).exclude(type="education").distinct()
	# add positions filter
	if filters['positions']:
		positions = positions.filter(title__in=filters['positions'])
	if filters['locations']:
		positions = positions.filter(entity__office__city__in=filters['locations'])
	# positions_list = [{'title':p.title,'org':p.entity.name,'industries':p.industries()} for p in positions]
	positions_list = [{'title':p['title'],'org':p['entity__name'],'industries':p['entity__domains']} for p in positions]
	# get all related entities
	# entities = Entity.objects.filter(positions__person_id__in=user_ids)
	entities = Entity.objects.select_related('images','domains').values('pk','name','domains','images__logo').filter(positions__person_id__in=user_ids).distinct()
	# add location filters
	if filters['locations']:
		entities = entities.filter(office__city__in=filters['locations'])
	# entities_list = [{'name':e.name,'domains':e.domains.all(),'logo':e.default_logo()} for e in entities]
	entities_list = [{'id':e['pk'],'name':e['name'],'domains':e['domains'],'logo':e['images__logo']} for e in entities]
	entities_ids = [e['id'] for e in entities_list]
	# get industries
	industries = Industry.objects.filter(entity__in=entities_ids).annotate(freq=Count('entity__positions')).order_by('-freq').distinct()

	# overview = {'users':'','positions':'','orgs':''}
	overview = {}
	overview['users'] = {'count':len(users_list),'values':users_list}
	overview['positions'] = {'count':len(positions_list),'values':positions_list}
	overview['orgs'] = {'count':len(entities_list),'values':entities_list}

	# initialize master career array
	careers = {}
	o = 0
	for i in industries:
		
		careers[i.name] = {
					"order": o,
					# "users": {'count':len(users_list),'values':[u for u in users_list if i.id == u['domains']]},
					# "positions": {'count':len(positions_list),'values':[p for p in positions_list if i.id == p['industries']]},
					# "orgs": {'count':len(entities_list),'values':[org for org in entities_list if i.id == org['domains']]}
					"users": {'values':[u for u in users_list if i.id == u['domains']]},
					"positions": {'values':[p for p in positions_list if i.id == p['industries']]},
					"orgs": {'values':[org for org in entities_list if i.id == org['domains']]}
				}
		careers[i.name]['users']['count'] = len(careers[i.name]['users']['values'])
		careers[i.name]['positions']['count'] = len(careers[i.name]['positions']['values'])
		careers[i.name]['orgs']['count'] = len(careers[i.name]['orgs']['values'])
		o += 1

	# sorted_careers = sorted(careers.iteritems(),key=lambda x: x['order'],reverse=True)
	return careers, overview

def _get_size_filter(sizes):
	# dictionary of ranges
	base_list = {
		'a':'1-10',
		'b':'11-25',
		'c':'26-50',
		'd':'51-100',
		'e':'101-250',
		'f':'251-500',
		'g':'501+'
	}
	# initialize list for holding dicts of upper and lower boundaries
	size_boundaries = []
	# iterate through base dictionary, for any match from filters add range to result dict
	for k,v in base_list.iteritems():
		if k in sizes:
			rg = v.split('-')
			size_boundaries.append({'lower':rg[0],'upper':rg[1]})
	return size_boundaries
	
	
def _get_latest_position(user,anon=False):
	"""
	Returns string with position title and company of most recent (and current) position, not the users headline or summary
	"""
	# grab most recent position, ordered by start date and is current
	latest_position = Position.objects.filter(person=user,current=True).order_by('start_date')
	# make sure there is a latest position
	if latest_position.exists():
		# if anonymous, filter and return
		if anon:
			# get domain of company
			domains = latest_position[0].entity.domains.all()
			if domains:
				co = domains[0].name + " company"
			else:
				co = None
			# return latest_position[0].safe_title() + " " + co
			return co
		# not anonymous, return full title and company name
		if latest_position[0].safe_title() == "unnamed position":
			return latest_position[0].entity.name
		else:
			return latest_position[0].safe_title() + " at " + latest_position[0].entity.name
	# no matches, return None
	return None

def _get_positions_for_path(positions,anon=False):
	"""
	Returns JSON format of all user positions, with possible anonymity
	"""
	# # get positions for user
	# positions = Positions.objects.filter(person=user),order_by('-start_date').values('title','summary','start_date','end_date','entity__name')
	# check positions
	if positions:
		# initialize new array
		formatted_positions = []
		# loop through each position
		no_of_positions = len(positions)
		# attribs['no_of_positions'] = no_of_positions
		# print "# of pos: " + str(no_of_positions)
		i = 0
		for p in positions:
			# print p.id
			# get first industry domain of company
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
			
			# check to see if anonymous

			# Clay: extra line fixes case in which domain==None
			if anon and domain:
				attribs['co_name'] = domain + " company"
			else:
				attribs['co_name'] = p.entity.name

			formatted_positions.append(attribs)
			
			i += 1
			if i == no_of_positions:
				attribs['last_position'] = True
			else:
				attribs['last_position'] = False

			attribs['no_of_positions'] = no_of_positions
		return formatted_positions
	# if no positions, return None
	return None

def _get_profile_pic(profile):
	pics = Picture.objects.filter(person=profile,status="active").order_by("created")
	if pics.exists():
		return pics[0].pic.__unicode__()
	return None



def _order_preserving_uniquify(seq):
	checked = []
	return_seq = []

	print 'before ' + str(len(seq))
    
	for e in seq:
		print e.profile.full_name()

	for e in seq:
		if e.id not in checked:
			checked.append(e.id)
			return_seq.append(e)

	print 'after ' + str(len(return_seq))

	for e in seq:
		print e.profile.full_name()

	return return_seq 
  



