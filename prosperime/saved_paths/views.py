# Python
import datetime

# Django
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.utils import simplejson

# Prosperime
from entities.models import Position
from saved_paths.models import Saved_Path

# # will add a particular position to a particular path, then return
# def save_position(request, title, pos_id):	
# 	## TODO add a 'success message'

# 	# need to know if career paths already exist or not
# 	user = request.user
# 	# Note: do not allow duplicate cp's, nor ''
# 	career_path = Saved_Path.objects.get(owner=user, title=title)
# 	print career_path.title
# 	position = Position.objects.get(id=pos_id)

# 	if not career_path:
# 		# this should not happen
# 		print "save_position called on non-existent path. error."
# 	else: 
# 		# add to existing career path
# 		print 'Adding position to cp: '+title+', pos_id: ' + pos_id
# 		career_path.positions.add(position)
# 		career_path.save()

# 	return HttpResponseRedirect('/search/')


# VIEW: display ALL user's paths
def show_paths(request):
	print 'show paths'

	saved_paths = Saved_Path.objects.filter(owner=request.user)
	data = {
		'saved_paths':saved_paths,
	}
	return render_to_response('saved_paths/saved_paths.html', data,
		context_instance=RequestContext(request))

# JSON dumper
def get_paths(request):
	paths = []

	# Check if get parameters or not
	# If so, show a single path
	if request.GET.getlist('t'):
		path_requested = request.GET.getlist('t')[0]
		path = Saved_Path.objects.get(title=path_requested)
		positions = _get_positions_for_path(path.positions.all())
		paths.append({'title': path.title, 'positions': positions})

	# If not, show all path_requested
	else:
		all_paths = Saved_Path.objects.filter(owner=request.user)

		if all_paths is not None:
			# then add to data
			for path in all_paths:

				# delegate position formatting to helper
				positions = _get_positions_for_path(path.positions.all())	
				paths.append({'title': path.title, 'positions': positions})

		# else do nothing
	print simplejson.dumps(paths)
	return HttpResponse(simplejson.dumps(paths), mimetype="application/json")
	

# VIEW: display a specific path, denoted by title
def show_path(request, title):
	print 'saved_paths.show_path : ' + title
	data = []
	# data['message'] = "delete.delete.i.eat.meat"
	# pass the path as JSON here



	return HttpResponse(simplejson.dumps(data), mimetype="application/json")

	# return render_to_response('saved_paths/saved_paths.html', data,
	# 	context_instance=RequestContext(request))

# VIEW: creates a path with positions
def create_path(request, title):
	print "saved_paths.create_path, creating path: " + title
	_create_and_return_path(request.user, title)

	return HttpResponseRedirect('/search/')

# VIEW: creates a path and adds a position
def create_path_add_position(request, title, pos_id):
	print 'yahtzee'
	new_path = _create_and_return_path(request.user, title)
	position = Position.objects.get(id=pos_id)
	new_path.positions.add(position)
	new_path.save()

	return HttpResponseRedirect('/search/')

def delete(request, title, pos_id):

	print 'delete request, '+title+', ' + str(pos_id)
	path = Saved_Path.objects.get(owner=request.user, title=title)
	position = Position.objects.get(id=pos_id)
	path.positions.remove(position)
	path.save()
	
	return HttpResponseRedirect('/saved_paths/')

# VIEW: responds to ajax POST request only 
def save(request):

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

	path = Saved_Path.objects.get(title=title, owner=request.user)
	if not path:
		response.update({'errors':['path could not be found']})
	else:
		position = Position.objects.get(id=pos_id)
		path.positions.add(position)

	return HttpResponse(simplejson.dumps(response))

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
		new_path = Saved_Path()
		new_path.title = title
		new_path.owner = request.user
		new_path.save()
		response.update({'success': True})

	except:
		response.update({'success': False})


	return HttpResponse(simplejson.dumps(response))

# HELPER: to unify reused code
def _create_and_return_path(user, title):
	new_path = Saved_Path()
	new_path.owner = user
	new_path.title = title
	new_path.save()
	return new_path

# code taken w/ few modifications from entities.views
def _get_positions_for_path(positions):
	"""
	Returns JSON format of all user positions, with possible anonymity
	"""
	if positions:
		formatted_positions = []
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
			
			# Clay: extra line fixes case in which domain==None
			if domain:
				attribs['co_name'] = domain + " company"
			else:
				attribs['co_name'] = p.entity.name

			formatted_positions.append(attribs)

		return formatted_positions
	# if no positions, return None
	return None


