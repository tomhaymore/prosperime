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
from django.db.models import Count
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
	companies =  list(Entity.objects.filter(cb_type="company").values("full_name","summary","logo")[:20])
	return HttpResponse(simplejson.dumps(companies), mimetype="application/json")

def filters(request):
	""" serves up JSON file of params for searches """
	# should break this down by type -- that might mean more requests to the server, however
	# TODO: add count for different filters; needs to accept parameters to limit result set
	# categories = []
	# sizesDict = {'name':'Size','value':'sizes','filters':[
	# 	{'name':'1-10','value':'a'},
	# 	{'name':'11-25','value':'b'},
	# 	{'name':'26-50','value':'c'},
	# 	{'name':'51-100','value':'d'},
	# 	{'name':'101-250','value':'e'},
	# 	{'name':'251-500','value':'f'},
	# 	{'name':'500+','value':'g'}]
	# }
	# categories.append(sizesDict)
	# stagesDict = {'name':'Locations','value':'locations','filters':[
	# 	{'name':'Seed','value':'seed'},
	# 	{'name':'A','value':'a'},
	# 	{'name':'B','value':'b'},
	# 	{'name':'C','value':'c'},
	# 	{'name':'D','value':'d'},
	# 	{'name':'E','value':'e'},
	# 	{'name':'F','value':'f'},
	# 	{'name':'G','value':'g'},
	# 	{'name':'H','value':'h'},
	# 	{'name':'IPO','value':'ipo'},
	# ]}
	# categories.append(stagesDict)
	# sectors = Entity.objects.values('domain').distinct()
	# sectorsDict = {'filters':[],'name':'Sectors','value':'sectors'}
	# for s in sectors:
	# 	if s['domain']:
	# 		#name = s['domain'].replace("_"," ")
	# 		name = " ".join(word.capitalize() for word in s['domain'].replace("_"," ").split())
	# 		sectorsDict['filters'].append({'name':name,'value':s['domain']})
	# categories.append(sectorsDict)
	# locations = Office.objects.values("city").annotate(freq=Count('pk')).order_by('-freq').distinct()[:20]
	# locationsDict = {'filters':[],'name':'Locations','value':'locations'}
	# for l in locations:
	# 	if l['city']:
	# 		value = l['city'].replace(" ","_").lower()
	# 		locationsDict['filters'].append({'name':l['city'],'value':value})
	# categories.append(locationsDict)
	# cats = {'categories':categories}
	filters = []
	locations = Office.objects.values("city").annotate(freq=Count('pk')).order_by('-freq').distinct()[:20]
	for l in locations:
		if l['city']:
			filters.append({'name':l['city'],'value':l['city'],'category':'Location'})
	sectors = Entity.objects.values('domain').distinct()
	for s in sectors:
		if s['domain']:
			name = " ".join(word.capitalize() for word in s['domain'].replace("_"," ").split())
			filters.append({'name':name,'value':s['domain'],'category':'Sector'})
	sizes = {
		'a':'1-10',
		'b':'11-25',
		'c':'26-50',
		'd':'51-100',
		'e':'101-250',
		'f':'251-500',
		'g':'501+'
	}
	for k,v in sizes.iteritems():
		filters.append({'name':v,'value':k,'category':'Size'})
	stages = ['seed','a','b','c','d','e','f','g','h','IPO']
	for s in stages:
		filters.append({'name':s,'value':s.lower(),'category':'Stage'})
	return HttpResponse(simplejson.dumps(filters), mimetype="application/json")
