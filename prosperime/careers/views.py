# Python
import datetime
import json

# Django
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.utils import simplejson
from django.contrib.auth.decorators import login_required

# Prosperime
# from entities.models import Position
from careers.models import SavedPath, SavedPosition, Position, Career, GoalPosition, SavedCareer, IdealPosition
from accounts.models import Profile
import careers.careerlib as careerlib


######################################################
################## CORE VIEWS ########################
######################################################

@login_required
def home(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('welcome')
	data = {}
	user = request.user

	# data['user_careers'] = Career.objects.filter(positions__person__id=user.id)
	data['saved_paths'] = SavedPath.objects.filter(owner=user)
	data['saved_careers'] = request.user.saved_careers.all()
	data['saved_jobs'] = GoalPosition.objects.filter(owner=user)

	return render_to_response('home.html',data,context_instance=RequestContext(request))

@login_required
def personalize_careers_jobs(request):
	'''
	presents initial set of careers and jobs to user during onboarding for them to selected
	'''
	# initiate careerlib
	career_sim = careerlib.CareerSimBase()
	# data array for passing to template
	data = {}
	# check to see if tasks have been initiated
	if 'tasks' in request.session:
		data = {
			'profile_task_id':request.session['tasks']['profile'],
			'connections_task_id':request.session['tasks']['connections'],
		}

	careers_network = career_sim.get_careers_brief_in_network(request.user)
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
def add_personalization(request):
	# check to make sure POST data came through
	if request.POST:
		print request.POST
		if 'selected_careers[]' in request.POST:
			print request.POST.getlist('selected_careers[]')
			for career_id in set(request.POST.getlist('selected_careers[]')):
				career = Career.objects.get(pk=career_id)
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
		return render_to_response('api_success.html')
	else:
		return render_to_response('api_fail.html')

@login_required
def list_jobs(request):
	if request.GET:
		params = request.GET['q']
		print params
		jobs = IdealPosition.objects.values('title','id').filter(title__icontains=params)
	else:
		jobs = IdealPosition.objects.values('title','id').all()

	jobs_list = []

	for j in jobs:
		jobs_list.append({'value':j['title'],'id':j['id']})

	# jobs = json.dumps(list(jobs))
	jobs = json.dumps(jobs_list)
	return HttpResponse(jobs, mimetype="application/json")



# VIEW: display ALL user's paths
def show_paths(request):

	paths = SavedPath.objects.filter(owner=request.user)

	data = {
		'saved_paths': paths,
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


def prototype(request):

	response = []

	if request.GET.getlist('pos', False):
		pos_id = request.GET.getlist('pos', False)[0]
		position = Position.objects.get(id=pos_id)
		print 'Original Request: ' + position.title + " @ " + position.entity.name 

		other_jobs_at_co = Position.objects.filter(entity__name=position.entity.name)
		profiles_from_company = set()
		for p in other_jobs_at_co:
			profiles_from_company.add(Profile.objects.get(user=p.person))

		profiles_same_job_title = set()
		profiles_exact_same_job = set()

		other_people_who_have_held_this_job = Position.objects.filter(title=position.title)
		for pos in other_people_who_have_held_this_job:
			profile = Profile.objects.get(user=pos.person)
			if profile not in profiles_same_job_title:
				profiles_same_job_title.add(profile)
			if pos.entity.name == position.entity.name:
				# don't want dupes. ok for now
				profiles_exact_same_job.add(profile)

		# now ready all elements for json...
		json_profiles_from_company = _ready_profiles_for_json(profiles_from_company)
		json_profiles_same_job_title = _ready_profiles_for_json(profiles_same_job_title)
		json_profiles_exact_same_job = _ready_profiles_for_json(profiles_exact_same_job)

		response = {
			'same_company': json_profiles_from_company,
			'same_job_title': json_profiles_same_job_title,
			'same_job_exact': json_profiles_exact_same_job,
		}


	else:
		response = []

		all_positions = Position.objects.all()[:100]
		for p in all_positions:
			formatted_pos = _ready_position_for_proto(p)
			if formatted_pos:
				response.append(formatted_pos)

	return HttpResponse(simplejson.dumps(response))



######################################################
##################    HELPERS   ######################
######################################################


def _ready_profiles_for_json(profiles):
	formatted_profiles = []

	for p in profiles:
		attribs = {
			'first_name': p.first_name,
			'last_name:': p.last_name,
		}
		formatted_profiles.append(attribs)

	return formatted_profiles



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


