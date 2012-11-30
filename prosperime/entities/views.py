# from Python
# import pkg_resources
# pkg_resources.require('simplejson') # not sure why this is necessary
# import simplejson

# from Django
from django.contrib.auth import authenticate, login as auth_login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from entities.models import Entity, Office, Financing
from django.db.models import Count, Q
from django.utils import simplejson
# from django.core import serializers

def login(request):
	if request.method == "POST":
		user = authenticate(username=request.POST['username'],password=request.POST['password'])
		if user is not None:
			auth_login(request,user)
			return HttpResponseRedirect('/home')

def home(request):
	# fetch 20 most recently updated entities
	entities = Entity.objects.filter(cb_type="company").annotate(rounds=Count('target')).order_by('-rounds')[:20]
	# fetch all distinct locations
	locations = Office.objects.values_list("city",flat=True).annotate(freq=Count('pk')).order_by('-freq').distinct()
	#locations = Office.objects.all().values_list('city',flat=True).distinct()
	# fetch distinct sectors
	sectors1 = Entity.objects.values_list('domain',flat=True).distinct()
	sectors2 = [x for x in sectors1 if x]
	# fetch distinct stages
	#stages = Financing.objects.values_list('round',flat=True).order_by('round').distinct()
	stages = ['seed','a','b','c','d','e','f','g','h','IPO']
	# dictionary of sizes
	sizes = {
		'a':'1-10',
		'b':'11-25',
		'c':'26-50',
		'd':'51-100',
		'e':'101-250',
		'f':'251-500',
		'g':'501+'
	}
	# test if user is authenticated
	# show what?
	return render_to_response('entities/home.html',
		{'entities':entities,
		'locations':locations,
		'sectors':sectors2,
		'stages':stages,
		'sizes':sizes},
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

	companies = Entity.objects.values("full_name","summary","logo").filter(cb_type="company").annotate(freq=Count('financing__pk')).order_by('-freq')

	if locationsSelected:
		companies = companies.filter(office__city__in=locationsSelected)
	if sectorsSelected:
		companies = companies.filter(domain__in=sectorsSelected)
	if sizesSelected:
		# get dictionary of size ranges
		rgs = getSizeFilter(sizesSelected)
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
	companies = list(companies[:20])
	return HttpResponse(simplejson.dumps(companies), mimetype="application/json")

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
		locationsFiltered = locationsFiltered.filter(entity__domain__in=sectorsSelected)
		print locationsFiltered.query
	if sizesSelected:
		# get dictionary of size ranges
		rgs = getSizeFilter(sizesSelected)
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
	print locationsBase.query
	

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
	sectorsBase = Entity.objects.values('domain').annotate(freq=Count('pk')).distinct()
	sectorsFiltered = sectorsBase

	# if locationsSelected:
	# 	sectorsFiltered = Entity.objects.filter(office__city__in=locationsSelected).values('domain').annotate(freq=Count('pk')).distinct()
	# else:
	# 	sectorsFiltered = Entity.objects.values('domain').annotate(freq=Count('pk')).distinct()
	
	if locationsSelected:
		sectorsFiltered = sectorsFiltered.filter(office__city__in=locationsSelected)
	if stagesSelected:
		sectorsFiltered = sectorsFiltered.filter(financing__round__in=stagesSelected)
	if sizesSelected:
		# get dictionary of size ranges
		rgs = getSizeFilter(sizesSelected)
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
		sectorsFiltered = sectorsFiltered.filter(q)

	sectorsFilteredDict = {}
	for l in sectorsFiltered:
		sectorsFilteredDict[l['domain']] = l['freq']

	for s in sectorsBase:
		# make sure it doesn't have a null value
		if s['domain']:
			# get count from sectorsFilteredDict
			if s['domain'] in sectorsFilteredDict:
				freq = sectorsFilteredDict[s['domain']]
			else:
				freq = 0
			name = " ".join(word.capitalize() for word in s['domain'].replace("_"," ").split())
			# check to see if the value should be selected
			if s['domain'] in sectorsSelected:
				filters.append({'name':name,'value':s['domain'],'category':'Sector','count':freq,'selected':True})
			else:
				filters.append({'name':name,'value':s['domain'],'category':'Sector','count':freq,'selected':None})
	
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

def getSizeFilter(sizes):
	# dictionary of ranges
	baseList = {
		'a':'1-10',
		'b':'11-25',
		'c':'26-50',
		'd':'51-100',
		'e':'101-250',
		'f':'251-500',
		'g':'501+'
	}
	# initialize list for holding dicts of upper and lower boundaries
	sizeBoundaries = []
	# iterate through base dictionary, for any match from filters add range to result dict
	for k,v in baseList.iteritems():
		if k in sizes:
			rg = v.split('-')
			sizeBoundaries.append({'lower':rg[0],'upper':rg[1]})
	return sizeBoundaries
	
	


	
