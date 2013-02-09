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
from careers.models import SavedPath, SavedPosition


######################################################
################## CORE VIEWS ########################
######################################################


# VIEW: display ALL user's paths
def show_paths(request):

	paths = SavedPath.objects.filter(owner=request.user)

	data = {
		'SavedPaths': paths,
	}

	return render_to_response('careers/saved_paths.html', data,
		context_instance=RequestContext(request))

# JSON dumper
def get_paths(request):
	paths = []

	# Check if get parameters or not
	# If so, show a single path
	if request.GET.getlist('id'):
		path_requested = request.GET.getlist('id')[0]
		path = SavedPath.objects.get(id=path_requested)
		path_owner = path.owner

		SavedPositions = SavedPosition.objects.filter(path=path)
		positions = _get_positions_for_path(SavedPositions)

		paths.append({'title': path.title, 'positions': positions, 'id': path.id})

	# If not, show all path_requested
	else:
		all_paths = SavedPath.objects.filter(owner=request.user)

		if all_paths is not None:
			# then add to data
			for path in all_paths:

				# delegate position formatting to helper
				SavedPositions = SavedPosition.objects.filter(path=path)
				positions = _get_positions_for_path(SavedPositions)	
				paths.append({'title': path.title, 'positions': positions, 'id': path.id})

		# else do nothing

	return HttpResponse(simplejson.dumps(paths), mimetype="application/json")
	

# AJAX POST requests only
def remove(request):

	path_id = request.POST.get('path_id', False)
	pos_id = request.POST.get('pos_id', False)
	response = {}

	# Error checking...
	if not request.is_ajax or not request.POST or not path_id or not pos_id:
		print 'Error @ SavedPaths.create'
		response.update({'success':False})
		return HttpResponse(simplejson.dumps(response))
	
	try:
		path = SavedPath.objects.get(id=path_id)
		position = Position.objects.get(id=pos_id)

		SavedPosition = SavedPosition.objects.get(path=path, position=position)
		deleted_pos_index = int(SavedPosition.index)
		SavedPosition.delete()
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
		print 'Error @ SavedPaths.save - get request'
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

		SavedPosition = SavedPosition()
		SavedPosition.position = position
		SavedPosition.path = path
		SavedPosition.index = path.get_next_index()
		SavedPosition.save()	

		# path.positions.add(position)

	return HttpResponse(simplejson.dumps(response))


# VIEW: creates a path, responds to POST request via AJAX
def create(request):
	title = request.POST.get('title', False)

	# Error checking... what to do with them??
	if not request.is_ajax:
		print 'Error @ SavedPaths.create - non ajax requested'
	if not request.POST:
		print 'Error @ SavedPaths.create - get request!'
	if not title:
		print 'Error @ SavedPaths.create - no title'

	response = {}

	try:
		new_path = SavedPath()
		new_path.title = title
		new_path.owner = request.user
		new_path.last_index = 1

		# automatically add current position to any new cp
		print 'before before'
		currentPos = Position.objects.filter(person=request.user, current=True).exclude(type='education')
		print 'before'
		if currentPos:
			print 'after'
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

# AJAX POST only, changes the indexing of SavedPositions
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


def prototype(request):

	response = []

	all_positions = Position.objects.all()[:100]
	for p in all_positions:
		formatted_pos = _ready_position_for_proto(p)
		if formatted_pos:
			response.append(formatted_pos)

	return HttpResponse(simplejson.dumps(response))

def prototype_data(request):

	resonse = []
	print request.GET.getlist('pos')



	return HttpResponse(simplejson.dumps(response))


######################################################
##################    HELPERS   ######################
######################################################

# code taken w/ few modifications from entities.views
# Note: 'SavedPositions' = SavedPosition objects
def _get_positions_for_path(SavedPositions):
	"""
	Returns JSON format of all user positions, with possible anonymity
	"""

	positions = []
	index_list = []
	for saved_pos in SavedPositions:
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

			formatted_positions.append(attribs)
			i += 1

		return formatted_positions
	# if no positions, return None
	return None


# Note, this uses the old school Position object, not SavedPosition
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


