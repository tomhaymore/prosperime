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
	companies =  list(Entity.objects.filter(cb_type="company").values("full_name","summary")[:20])
	#data = serializers.serialize('json',companies)
	return HttpResponse(simplejson.dumps(companies), mimetype="application/json")
