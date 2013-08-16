
# View for invidiual profiles
@login_required
def profile_old(request, user_id):

	user = User.objects.get(id=user_id)
	if user.profile.status == "dormant":
		HttpResponseRedirect("/home/")

	profile = user.profile
	profile_pic = user.profile.default_profile_pic()
	
	own_profile = False
	own_profile_javascript = "false"
	queue = None
	viewer_saved_paths = []
	saved_path_ids = None
	goal_careers = None
	career_decision_position = "false"
	goal_positions = None

	# career_map = profile.all_careers
	top_careers = profile.get_all_careers(3)
	career_map = None
	# top_careers = None

	# Convert positions to timeline info
	positions = Position.objects.filter(person=user).select_related('careerDecision')
	formatted_positions, start_date, end_date, total_time, current = _prepare_positions_for_timeline(positions)

	# If Own Profile, get extra information
	if int(user_id) == int(request.user.id):
		own_profile = True
		own_profile_javascript = "true"

		# Your Saved Paths
		saved_path_queryset = SavedPath.objects.filter(owner=request.user).exclude(title='queue')
		viewer_saved_paths = []
		saved_path_ids = []
		for path in saved_path_queryset:
			viewer_saved_paths.append(_saved_path_to_json(path))
			saved_path_ids.append([path.id, path.title])

		# Your Goal Careers
		goal_careers_queryset = SavedCareer.objects.filter(owner=request.user).select_related("career")
		goal_careers = []
		for career in goal_careers_queryset:
			formatted_career = _saved_career_to_json(career.career)
			formatted_career["saved_career_id"] = career.id
			goal_careers.append(formatted_career)

		# Your Goal Positions
		goal_positions_queryset = GoalPosition.objects.filter(owner=request.user).select_related("position")
		goal_positions = []
		for pos in goal_positions_queryset:
			formatted_position = _ideal_position_to_json(pos.position)
			formatted_position["goal_id"] = pos.id
			goal_positions.append(formatted_position)

		# Positions of Interest ('Queue')
		try:
			queue = SavedPath.objects.filter(owner=request.user, title='queue').prefetch_related()
			queue = _saved_path_to_json(queue[0])
		except:
			queue = []

		# Career Decision Prompt
		# career_decision = _get_career_decision_prompt_position(top_careers, positions, profile)
		# if career_decision is None:
		# 	career_decision_position = None;
		# else:
		# 	career_decision_position = {
		# 		'id':career_decision.id,
		# 		'title':career_decision.title,
		# 		'co_name':career_decision.entity.name,
		# 		'type':career_decision.type,
		# 	}
		career_decision_position = "false"


	if not own_profile:
		# see if connected
		viewer = request.user.profile
		if profile in viewer.connections.all():
			is_connected = True
		else:
			is_connected = False


		# Users Saved Paths
		saved_path_queryset = SavedPath.objects.filter(owner__id=user_id).exclude(title='queue')
		viewer_saved_paths = []
		saved_path_ids = []
		for path in saved_path_queryset:
			viewer_saved_paths.append(_saved_path_to_json(path))
			saved_path_ids.append([path.id, path.title])

	else:
		is_connected = True


	response = {
		'user':user,
		'profile':profile,
		'viewer_saved_paths':simplejson.dumps(viewer_saved_paths),
		'saved_path_ids':saved_path_ids,
		'profile_pic':profile_pic,
		'positions':simplejson.dumps(formatted_positions),
		'current':current,
		'start_date':start_date,
		'end_date':end_date,
		'total_time':total_time,
		# 'career_map':career_map,
		'top_careers':top_careers,
		'career_decision_prompt':career_decision_position,
		'own_profile':own_profile,
		'own_profile_javascript':own_profile_javascript, # b/c js has true/false, not True/False
		'queue':simplejson.dumps(queue),
		'goal_careers':simplejson.dumps(goal_careers),
		'goal_positions':simplejson.dumps(goal_positions),
		'is_connected':is_connected,
	}

	return render_to_response('accounts/profile.html', response, context_instance=RequestContext(request))


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

	#return render_to_response('accounts/profile_org.html', response, context_instance=RequestContext(request))

	return render_to_response('accounts/profile.html', {'profile':profile, 'saved_paths': saved_paths, 'profile_pic': profile_pic, 'orgs':org_list, 'ed':ed_list, 'current':current, 'start_date':start_date, 'end_date':end_date, 'total_time': total_time, 'compress': compress, 'career_map': career_map}, context_instance=RequestContext(request))



# Deletes a goal positions, saved careers, or interested position 
def deleteItem(request):

	response = {}

	item_type = request.POST.get('type')
	item_id = request.POST.get('id')

	print "Delete: " + str(item_type) + ' ' + str(item_id)

	if not item_type:
		response["result"] = "Failure"
		response["errors"] = "no query found"
		return HttpResponse(simplejson.dumps(response))

	if item_type == "goal-position":
		gp = GoalPosition.objects.get(id=item_id)
		gp.delete()
		response["result"] = "Success"

	elif item_type == "saved-career":
		sc = SavedCareer.objects.get(id=item_id)
		sc.delete()
		response["result"] = "Success"

	elif item_type == "queue-position":
		poi = SavedPosition.objects.get(position__id=item_id, path__title="queue", path__owner=request.user)
		poi.delete()
		response["result"] = "Success"

	return HttpResponse(simplejson.dumps(response))


# Called after a goal position, saved career is added to a profile, allowing
#	backbone to refresh the template
def updateProfile(request):

	response = {}
	query = request.GET.getlist('query')

	if query:

		if query[0] == "goalPositions":

			goal_positions_queryset = GoalPosition.objects.filter(owner=request.user).select_related("position")
			goal_positions = []
			for pos in goal_positions_queryset:
				goal_positions.append(_ideal_position_to_json(pos.position))

			response["data"] = goal_positions

		elif query[0] == "savedCareers":

			goal_careers_queryset = SavedCareer.objects.filter(owner=request.user).select_related("career")
			goal_careers = []
			for career in goal_careers_queryset:
				goal_careers.append(_saved_career_to_json(career.career))

			response["data"] = goal_careers

		else:
			response["data"] = None

		response["result"] = "success"
		return HttpResponse(simplejson.dumps(response))

	response["result"] = 'failure'
	return HttpResponse(simplejson.dumps(response))

def _test_career_prompt():


	# get random profile
	profile_max = Profile.objects.count()
	profile_num = random.randint(1, profile_max)

	profile = Profile.objects.get(pk=profile_num)
	positions = Position.objects.filter(person=profile.user)

	top_careers = profile.top_careers

	values = _get_career_decision_prompt_position(top_careers, positions, profile)
	
	if values is None:
		print 'Person: ' + str(profile.user.id) + profile.full_name() + ' has no positinos?'
	else:
		for value in values:
			print 'Person: ' +str(profile.user.id) + profile.full_name()
			if value.title is not None:
				print 'Return Value: ' + value.title + ' ' + value.entity.name
			else:
				print 'Return Value: nameless ' + value.entity.name

	return values


def _get_career_decision_prompt_position(top_careers, positions, profile):
	eligible_candidates = []
	unique_set = set()

	# Convert QuerySet to List & Uniqify
	for pos in positions:
		if pos.title is None:
			pos.title = ""

		if pos.title+pos.entity.name not in unique_set:
			eligible_candidates.append(pos)
			unique_set.add(pos.title + pos.entity.name)

	if len(positions) == 0:
		return None
	else: 
		already_asked = CareerDecision.objects.filter(position__in=positions)
		print "already asked:"
		print already_asked

		# ignore positions that we've already asked about
		for decision in already_asked:
			eligible_candidates.remove(decision.position)

		# need a copy so that removing from list doesn't short the loop...
		# 	annoying python implementation quirk
		candidates_copy = eligible_candidates[:]
		for candidate in candidates_copy:
			# ignore singleton entries, in which we have only one position
			#	for that entity
			print 'testing: ' +str(candidate.id)

			# Test for Singleton Entity
			# if Position.objects.filter(entity__name=candidate.entity.name).count() <= 1:
			# 	eligible_candidates.remove(candidate)
			# 	print 'remove: '+str(candidate.id) + ' singleton entity'

			# Test for Singleton Position
			if Position.objects.filter(title=candidate.title).count() <=1:
				eligible_candidates.remove(candidate)
				print 'remove: '+str(candidate.id)+ ' singleton pos'

			# Test for no title (ok for ed)
			elif candidate.title is "" and candidate.type is not 'education':
				eligible_candidates.remove(candidate)
				print 'remove: '+str(candidate.id) + ' no title non ed'

			## nagging issues - jobs @ universities... cut them?
			## CEO, Board Member...
			## what if all eliminated??

			## idea for better: filter by # entity, position matches

	for e in eligible_candidates:
		print str(e.id)

	# for now, just return top hit
	if len(eligible_candidates) >= 1:
		return eligible_candidates[0]
	else:
		return None


## Takes Saved Path object and returns dict
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
			'org':p.position.entity.name,
			'type':p.position.type,
		})
	formatted_path['positions'] = positions
	return formatted_path

## Takes a career object and returns dict
def _saved_career_to_json(career):

	formatted_career = {
		'title':career.long_name,
		'career_id':career.id,
	}

	return formatted_career

## Takes Ideal Position object and returns dict
def _ideal_position_to_json(position):

	formatted_position = {
		'title':position.title,
		'description':position.description,
		'ideal_id':position.id,
	}

	return formatted_position


