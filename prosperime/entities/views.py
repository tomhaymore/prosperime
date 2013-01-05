# from Python
# import pkg_resources
# pkg_resources.require('simplejson') # not sure why this is necessary
# import simplejson

# from Django
# from django.contrib.auth import authenticate, login as auth_login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from accounts.models import Picture
from entities.models import Entity, Office, Financing, Industry, Position
from django.db.models import Count, Q
from django.utils import simplejson
from django.contrib import messages
# from django.core import serializers


# @login_required
def home(request):
	if request.user.is_authenticated():
		# user is logged in, display personalized information
		return HttpResponseRedirect('search')
	data = {}
	return render_to_response('home.html',data,context_instance=RequestContext(request))

def search(request):
	
	# test if user is authenticated
	# show what?
	# print request.user.li_linked()
	data = {}
	if 'msg' in request.session:
		data['msg'] = request.session['msg']
	if request.user.is_authenticated():
		data['user'] = request.user
	return render_to_response('entities/search.html',data,
		context_instance=RequestContext(request))

def companies(request):
	""" serves up JSON file of company search results """
	
	# initialize array of companies
	
	# companies = []

	# get search filters
	
	locationsSelected = request.GET.getlist('location')
	sectorsSelected = request.GET.getlist('sector')
	sizesSelected = request.GET.getlist('size')
	stagesSelected = request.GET.getlist('stage')

	# print locationsSelected

	companies = Entity.objects.values("name","summary","image__logo").filter(type="organization").annotate(freq=Count('financing__pk')).order_by('-freq')

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
	# print companies.query
	companies = list(companies[:20])
	return HttpResponse(simplejson.dumps(companies), mimetype="application/json")

def path_filters(request):
	
	""" serves up JSON object of params for path searches """

	# initialize array for all filters
	filters = []

	# get search filters
	locationsSelected = request.GET.getlist('location')
	sectorsSelected = request.GET.getlist('sector')
	positionsSelected = request.GET.getlist('position')

	# set base filters

	# set location filters
	locationsBase = User.objects.values("positions__entity__office__city").annotate(freq=Count('pk')).order_by('-freq').distinct()
	locationsFiltered = locationsBase

	if positionsSelected:
		locationsFiltered = locationsFiltered.filter(positions__title__in=positionsSelected)
	
	if sectorsSelected:
		locationsFiltered = locationsFiltered.filter(positions__entity__domains__name__in=sectorsSelected)

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
	sectorsBase = User.objects.values('positions__entity__domains__name').annotate(freq=Count('pk')).distinct()
	sectorsFiltered = sectorsBase

	if locationsSelected:
		sectorsFiltered = sectorsFiltered.filter(positions__entity__office__city__in=locationsSelected)

	if positionsSelected:
		sectorsFiltered = sectorsFiltered.filter(positions__title__in=positionsSelected)

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
	
	# get position filters
	positionsBase = User.objects.values('positions__title').annotate(freq=Count('pk')).distinct()
	positionsFiltered = positionsBase

	if locationsSelected:
		positionsFiltered = positionsFiltered.filter(positions__entity__office__city__in=locationsSelected)
	if sectorsSelected:
		positionsSelected = positionsFiltered.filter(positions__entity__domains__name__in=sectorsSelected)

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

def filters(request):

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
	sectorsFiltered = sectorsBase

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

def paths(request):
	# initialize array of paths
	paths = []

	# get search filters
	locationsSelected = request.GET.getlist('location')
	sectorsSelected = request.GET.getlist('sector')
	positionsSelected = request.GET.getlist('position')

	# fetch all users
	# TODO someway to order this to retrieve those most relevant
	users = User.objects.annotate(no_of_pos=Count('positions__pk')).exclude(pk=request.user.id).order_by('-no_of_pos')

	if locationsSelected:
		users = users.filter(positions__entity__office__city__in=locationsSelected)
	if sectorsSelected:
		users = users.filter(positions__entity__domains__name__in=sectorsSelected)
	if positionsSelected:
		users = users.filter(positions__title_in=positionsSelected)

	users = users[:20]

	# loop through all positions, identify those that belong to connections
	for u in users:
		# check if position held by 
		if request.user.profile in u.profile.connections.all():
			connected = True
			name = u.profile.full_name()
			current_position = _get_latest_position(u)
			profile_pic = _get_profile_pic(u.profile)
			if current_position is not None:
				positions = _get_positions_for_path(u.positions.all())
			else:
				positions = None
		else:
			connected = False
			name = None
			current_position = _get_latest_position(u,anon=True)
			positions = _get_positions_for_path(u.positions.all(),anon=True)
			profile_pic = None
			# need to convert positions to anonymous

		paths.append({'id':u.id,'profile_pic':profile_pic,'full_name':name,'current_position':current_position,'positions':positions,'connected':connected})
		# paths.append({'full_name':name,'current_position':current_position,'connected':connected})

	return HttpResponse(simplejson.dumps(paths), mimetype="application/json")

def path(request,user_id):
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
			if p.type == "education":
				attribs = {
					'domain':domain,
					'duration':p.duration(),
					'title':p.degree + ", " + p.field
				}
			else:
				attribs = {
					'domain':domain,
					'duration':p.duration(),
					'title':p.title
				}
			if p.start_date is not None:
				attribs['start_date'] = p.start_date.strftime("%m/%Y")
			if p.end_date is not None:
				attribs['end_date'] = p.end_date.strftime("%m/%Y")
			
			# check to see if anonymous
			if anon:
				attribs['co_name'] = domain + " company",
			else:
				attribs['co_name'] = p.entity.name

			formatted_positions.append(attribs)
			
			i += 1
			if i == no_of_positions:
				attribs['last_position'] = True
			else:
				attribs['last_position'] = False
		return formatted_positions
	# if no positions, return None
	return None

def _get_profile_pic(profile):
	pics = Picture.objects.filter(person=profile,status="active").order_by("created")
	if pics.exists():
		return pics[0].pic.path
	return None

