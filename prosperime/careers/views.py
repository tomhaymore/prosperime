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
from django.core.cache import cache

# Prosperime
from entities.models import Entity, Industry
from careers.models import SavedPath, SavedPosition, Position, Career, GoalPosition, SavedCareer, IdealPosition, CareerDecision
from accounts.models import Profile
import careers.careerlib as careerlib
from entities.models import Entity
from django.db.models import Count, Q

######################################################
################## CORE VIEWS ########################
######################################################

# dev only
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



def next(request):
	data = {}

	print request.GET

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
		print industry_data
		new_data = {
			'lvl':2,
			'start_name':data['start_name'],
			'start_id':data['start_id'],
			'end_name':industry_data[0],
			'end_id':ind_2,
			'total_people':industry_data[1],
			'people':industry_data[2],
		}

		print 'Double Query: ' + str(ind_1) + ' --> ' + str(ind_2)
		return HttpResponse(simplejson.dumps(new_data))


	## Single Industry ##
	# All info about a single industry
	elif ind_1:

		# Check cache
		data = cache.get('next_industry_data_'+str(request.user.id)+'_'+str(ind_1))
		if data is None:
			cache.set('next_industry_data_'+str(request.user.id)+'_'+str(ind_1),_get_industry_data(ind_1),600)
			data = cache.get('next_industry_data_'+str(request.user.id)+'_'+str(ind_1))
	

		print 'Single Query: ' + str(ind_1)
		return HttpResponse(simplejson.dumps(data))

	## Plain Page ##
	else:
		return render_to_response('careers/next.html',data,context_instance=RequestContext(request))


# constructs the return data structure for a single industry view
## NOTE: this is a beast, and stores all the dsts needed for the 
## industry --> industry sub-views. 

### FINAL NOTE: eventually, we might want to be able to segment this by 
### 'my network' & 'prosperime community'. I do nothing about this now
def _get_industry_data(ind_id):

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

	## Iterate through all positions from given industry
	for p in related_positions:
		person = Profile.objects.get(user=p.person)

		## Use set to count the # people related to each industry
		if p.id not in people_set:
			people_set.add(p)

		## My ghetto logic where I assume that the next position
		## in the db is the next pos in someone's timeline
		next = Position.objects.get(pk=p.pk + 1)

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
			'transitions':transitions,
		}

	return data



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


def viewCareerDecisions(request):
	data = {}

	return render_to_response('careers/career_decisions.html',data,context_instance=RequestContext(request))

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



def entityAutocomplete(request):
	response = {}
	query = request.GET.getlist('query')[0]
	print 'autocomplete: ' + query
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
	data['career_decisions'] = CareerDecision.objects.all()
	return render_to_response('home.html',data,context_instance=RequestContext(request))

@login_required
def discover(request):

	# initiate CarerSimBase
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

	# init careerlib
	career_path = careerlib.CareerPathBase()

	# get ed overview
	ed_overview = cache.get('career_profile_ed_overview_'+str(request.user.id)+"_"+str(career_id))
	# check to see if cache was empty
	if ed_overview is None:
		cache.set('career_profile_ed_overview_'+str(request.user.id)+"_"+str(career_id),career_path.get_ed_overview(request.user,career))
		ed_overview = cache.get('career_profile_ed_overview_'+str(request.user.id)+"_"+str(career_id))
		# ed_overview = career_path.get_ed_overview(request.user,career)

	# get paths overview
	paths = cache.get('paths_in_career_'+str(request.user.id)+"_"+str(career_id))
	# check to see if cache is empty
	if paths is None:
		cache.set('paths_in_career_'+str(request.user.id)+"_"+str(career_id),careerlib.get_paths_in_career(request.user,career),10)
		paths = cache.get('paths_in_career_'+str(request.user.id)+"_"+str(career_id))

	# break down paths to make it easier to parses
	paths_in_career = {}
	paths_in_career['network'] = paths['network']
	paths_in_career['all'] = paths['all']

	overview = {}
	overview['network'] = paths['overview']['network']
	overview['all'] = paths['overview']['all']

	return render_to_response('careers/career_profile.html',{'career':career,'ed_overview':ed_overview,'paths':paths_in_career,'overview':overview},context_instance=RequestContext(request))

@login_required
def discover_career(request,career_id):

	# initiate CarerSimBase
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

	# initiate CarerSimBase
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

	# initiate CarerSimBase
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
def discover_position(request,pos_id):

	return render_to_response('careers/discover_position.html',{},context_instance=RequestContext(request))

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
	careers_similar_ids = []

	for c in careers_similar:
		careers_similar_ids.append(c.id)

	careers = {}

	careers['network'] = careers_network
	careers['similar'] = careers_similar

	return render_to_response('careers/personalize_careers.html',{'data':data,'careers':careers},context_instance=RequestContext(request))


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
		return render_to_response('api_success.html')
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
def manual_save(user_id, path_id, pos_id):

	path = SavedPath.objects.get(id=path_id)
	position = Position.objects.get(id=pos_id)

	saved_position = SavedPosition()
	saved_position.position = position
	saved_position.path = path
	saved_position.index = path.get_next_index()
	saved_position.save()	

	return 'Success'

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
