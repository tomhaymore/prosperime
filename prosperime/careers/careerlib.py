# from Python
import json
import urllib2
from datetime import datetime
from datetime import timedelta
import csv
import re
import os
import types


# from Django
from django.contrib.auth.models import User
from entities.models import Industry, Entity
from careers.models import Career, Position, IdealPosition
from django.core.exceptions import MultipleObjectsReturned
from django.core import management
from django.db.models import Count, Q

# get focal careers
def get_focal_careers(user,limit=10):
	career_path = CareerPathBase()
	careers = career_path.get_focal_careers(user,limit)
	return careers

def avg_duration_network(career,user):
	career_path = CareerPathBase()
	return career_path.avg_duration_network(career,user)

def avg_duration_all(career):
	career_path = CareerPathBase()
	return career_path.avg_duration_all(career)

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

def get_paths_in_career(user,career):
		# initialize overview array
		overview = {}
		paths = {}

		# get users in network
		users_list, user_ids = _get_users_in_network(user)

		network_people = User.objects.prefetch_related().select_related('positions','entities','accounts').filter(id__in=user_ids,positions__careers=career).annotate(no_of_pos=Count('positions__pk')).order_by('-no_of_pos').distinct()
		# CAUTION--values() can return multiple records when requesting M2M values; make sure to reduce
		# network_people = User.objects.prefetch_related().select_related('profile','positions','pictures').values('id','profile__headline','profile__first_name','profile__last_name','profile__pictures__pic','positions__entity__id','positions__entity__name').filter(id__in=user_ids,positions__careers=career).annotate(no_of_pos=Count('positions__id')).order_by('-no_of_pos')

		# Clayton -- need to uniqify this list, b/c lots of wasted time
		#	parsing duplicate people ... EDIT: not the problem, problem is
		#	duplicate positions!
		# network_people = _order_preserving_uniquify(network_people)

		network_people_dict = {}
		num_pos = 0
		entities = []
		# entities = set()
		entities_dict = {}
		num_cos = 0
		network_positions = []
		# counter = 0

		## Network
		for p in network_people:
			# check to see if user is already in the dict
			# if p.id not in network_people_dict:
			# 	network_people_dict[p.id] = {
			# 		'full_name': p.profile.full_name(),
			# 		'headline': p.profile.headline,
			# 		'pic':p.profile.default_profile_pic(),
			# 	}
			# check each record to make sure the profile pic gets picked up
			# if 'profile__pictures__pic' in p:
			# 	network_people_dict[p['id']]['pic'] = p['profile__pictures__pic']
			for pos in p.positions.all():
			# if 'positions__entity__id' in p:
			# increment the position counter
				entities.append(pos.entity.name)
				num_pos += 1
				if pos.entity.name in entities_dict:
					entities_dict[pos.entity.name]['count'] += 1
				else:
					entities_dict[pos.entity.name] = {
						'count':1,
						'id':pos.entity.name
					}
			# num_pos += len(p.positions.all())
			# # people_seen = set()
			# # positions_seen = set()

			# for pos in p.positions.all():
			# 	# num_pos += 1
			# 	entities.append(pos.entity.id)
			# 	# entities.add(pos.entity.id)

			# 	# if pos in career, add to positions
			# 	# 	additionally, impose 30 position cap
				
			# 	# if career in pos.careers.all():
			# 	# 	counter += 1
			# 	# 	print counter
			# 	#  	if len(network_positions) < 30:
			# 	# 		# check if seen already (avoid duplicates)
			# 	# 		if pos.id not in positions_seen:
			# 	# 			positions_seen.add(pos.id)
			# 	# 			network_positions.append({
			# 	# 				'id':pos.id,
			# 	# 				'title':pos.title,
			# 	# 				'co_name':pos.entity.name,
			# 	# 				'owner':pos.person.profile.full_name(),
			# 	# 				'owner_id':pos.person.id,
			# 	# 				'logo_path':pos.entity.default_logo(),
			# 	# 			})

			
			# 	if pos.entity.name in entities_dict:
			# 		entities_dict[pos.entity.name]['count'] += 1

			# 		# check if person seen already (avoid duplicates)
			# 		# 	additionally, cap people @ 5 for now
			# 		# if p.id not in people_seen and len(entities_dict[pos.entity.name]['people']) < 6:
						
			# 		# 	person_dict = {
			# 		# 		'name':p.profile.full_name(),
			# 		# 		'id':p.id,
			# 		# 	}
			# 		# 	entities_dict[pos.entity.name]['people'].append(person_dict)
			# 		# 	people_seen.add(p.id)

			# 	else:
			# 		# people_list = [{
			# 		# 	'name':p.profile.full_name(),
			# 		# 	'id':p.id,
			# 		# }]
					
			# 		entities_dict[pos.entity.name] = {
			# 			'count' : 1,
			# 			'id':pos.entity.id,
			# 			# 'logo':pos.entity.default_logo(),
			# 			# 'people':people_list,	
			# 		}

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


		num_cos = len(set(entities))
		# num_cos = len(entities)

		overview['network'] = {
			'num_people':len(network_people),
			'num_pos':num_pos,
			'num_cos':num_cos
		}

		# all_people = User.objects.select_related('profile','positions','pictures').values('id','profile__headline','profile__first_name','profile__last_name','profile__pictures__pic','positions__entity__id','positions__entity__name').filter(positions__careers=career).annotate(no_of_pos=Count('positions__id')).order_by('-no_of_pos')
		all_people = User.objects.select_related('positions').filter(positions__careers=career).annotate(no_of_pos=Count('positions__pk')).order_by('-no_of_pos').distinct()

		num_pos = 0
		entities = []
		# entities = set()
		all_entities_dict = {}
		all_positions = []
		num_cos = 0

		## ALL

		# for p in all_people:
		# 	# check to see if user is already in the dict
		# 	if p['id'] not in network_people_dict:
		# 		network_people_dict[p['id']] = {
		# 			'full_name': p['profile__first_name'] + " " + p['profile__last_name']
		# 		}
		# 		# if ['profile__headline'] in p:
		# 		# 	network_people_dict[p['id']]['headline'] = p['profile__headline']
		# 		# check to see if this is a connected user
		# 		if p['id'] in user_ids:
		# 			network_people_dict[p['id']]['connected'] = True
		# 		else:
		# 			network_people_dict[p['id']]['connected'] = False
		# 	# check each record to make sure the profile pic gets picked up
		# 	if 'profile__pictures__pic' in p:
		# 		network_people_dict[p['id']]['pic'] = p['profile__pictures__pic']
		# 	if 'positions__entity__id' in p:
		# 	# increment the position counter
		# 		entities.append(p['positions__entity__id'])
		# 		num_pos += 1
		# 		if p['positions__entity__name'] in entities_dict:
		# 			entities_dict[p['positions__entity__name']]['count'] += 1
		# 		else:
		# 			entities_dict[p['positions__entity__name']] = {
		# 				'count':1,
		# 				'id':p['positions__entity__name']
		# 			}

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
				entities.append(pos.entity.id)
				# entities.add(pos.entity.id)

		num_cos = len(set(entities))
		# num_cos = len(entities)

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
		# paths['networkOrgs'] = entities_dict
		# paths['allOrgs'] = all_entities_dict

		# # TRIAL - adding positions information
		# paths['networkPositions'] = network_positions
		# paths['allPositions'] = all_positions

		# Returns nested dict
		paths['overview'] = {
			'network' : overview['network'],
			'all':overview['all'],
			}

		# return paths, overview
		return paths

# set max size of ngram
NGRAM_MAX = 10

# set min size of ngram
NGRAM_MIN = 1

# initialize global dictionary for career-to-position mapping
careers_to_positions_map = {}

# initilize array for stop words
STOP_LIST = [
	'director',
	'manager',
	'intern',
	'aide',
	'clerk',
	'consultant',
	'program director',
	'sales',
	'founder'
]

def _load_stop_list():
	global STOP_LIST
	try:
		reader = (open('career_map_stop_list.csv','rU'))
	except:
		return None
	for row in reader:
		STOP_LIST.append(row[0])

def _tokenize_position(title):
	"""
	tokenizes position title based on spaces
	"""
	if title:
		# tokenize position title
		tokens = title.split(" ")
		# reduce all strings to lower case
		tokens = [t.lower() for t in tokens]
		return tokens
	return None

def _extract_ngrams(tokens):
	"""
	breaks position titles into appropriate number of ngrams and returns as a list
	"""
	if tokens:
		ngrams = []
		n_tokens = len(tokens)
		for i in range(n_tokens):
			for j in range(i+1,min(n_tokens,NGRAM_MAX)+1):
				ngram = " ".join(tokens[i:j])
				ngrams.append(ngram)
				# ngrams.append(tokens[i:j])

		return ngrams
	return None

def init_careers_to_positions_map():
	"""
	fill in career map dictionary from db
	"""
	global careers_to_positions_map
	careers = Career.objects.values('id','pos_titles')
	
	career_map = {}

	for c in careers:
		if c['pos_titles'] is not None:
			titles = json.loads(c['pos_titles'])
			# add career-to-position title mapping, reduced to lower case
			if titles is not None:
				# print title
				# pass
				try:
					titles = [t.lower() for t in titles]
				except AttributeError:
					print titles
					# pass
			
			career_map[c['id']] = titles
			# print career_map

	careers_to_positions_map = career_map

def match_careers_to_position(pos):
	career_mapper = CareerMapBase()
	careers = career_mapper.match_careers_to_position(pos)
	return careers

	# global STOP_LIST
	# title_ngrams = _extract_ngrams(_tokenize_position(pos.title))

	# careers = []

	# if title_ngrams is not None:
	# 	for t in title_ngrams:
	# 		if t is not None:
	# 			# make sure position title is not in stop list, e.g., "Manager" or "Director" or something equally generic
	# 			if t not in STOP_LIST:
	# 				for k,v in careers_to_positions_map.items():
	# 					if t in v and k not in careers:
	# 						# print 'hello'
	# 						careers.append(k)
	# 						# print t + ": " + career.name

	# return careers

def test_position(title):

	title_ngrams = _extract_ngrams(_tokenize_position(title))
	
	print title_ngrams

	for t in title_ngrams:
		# make sure position title is not in stop list, e.g., "Manager" or "Director" or something equally generic
		if t not in STOP_LIST:
			for k,v in careers_to_positions_map.items():
				# print v
				if t in v:
					career = Career.objects.get(pk=k)
					print title + " matches " + career.name

def test_match_careers_to_position(title=None):

	positions = Position.objects.all()

	for p in positions:
		careers = []

		if p.title:
			# print 'yes title'
			title_ngrams = _extract_ngrams(_tokenize_position(p.title))

			# print title_ngrams

			for t in title_ngrams:
				# make sure position title is not in stop list, e.g., "Manager" or "Director" or something equally generic
				if t not in STOP_LIST:
					# print 'not in stop list'
					for k,v in careers_to_positions_map.items():
						# print v
						if t in v and k not in careers:
							print t + " : " + str(v)
							careers.append(k)
							career = Career.objects.get(pk=k)
							# print str(k) + ": " + t
		# print str(p.title) + " : " + str(careers)

class CareerBase():

	def get_users_in_career(self,career):

		users = User.objects.prefetch_related('profile__connections').select_related('positions').filter(positions__careers=career)

		return users

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

	def get_users_full_in_network(user):
		"""
		returns User object for all users in network
		"""
		# ge schools from user
		schools = Entity.objects.filter(li_type="school",positions__person=user,positions__type="education").distinct()

		# get all connected users and those from the same schools
		users = User.objects.select_related('profile','pictures').filter(Q(profile__in=user.profile.connections.all()) | (Q(positions__entity__in=schools))).distinct()

		return users


class CareerSimBase():

	# fetch all users
	# users = User.objects.prefetch_related('positions').exclude(profile__status="deleted")
	users = {}

	# initializes single map
	users_orgs_map_single = {}

	# initializes organizational map
	users_orgs_map = {}

	# initialize educational map
	users_eds_map = {}

	def __init__(self):
		self.load_users()
		self.load_maps()

	def load_users(self):
		users = User.objects.values('id','positions__type','positions__entity__id')
		users_dict = {}
		for u in users:
			if u['id'] in users_dict:
				users_dict[u['id']]['positions'].append({'type':u['positions__type'],'id':u['positions__entity__id']})
			else:
				users_dict[u['id']] = {'positions':[{'type':u['positions__type'],'id':u['positions__entity__id']}]}
		self.users = users_dict
		# print self.users

	def load_single_map(self):
		"""
		loads set of org affiliations for each user
		"""
		for k,v in self.users.items():
			orgs = []
			for p in v['positions']:
				orgs.append(p['id'])
			if orgs:
				self.users_orgs_map_single[k] = set(orgs)

	def load_maps(self):
		"""
		loads set of orgs / eds for each user
		"""
		for k,v in self.users.items():
			orgs = []
			eds = []
			for p in v['positions']:
				if p['type'] == "education":
					eds.append(p['id'])
				else:
					orgs.append(p['id'])
			if orgs:
				self.users_orgs_map[k] = set(orgs)
			if eds:
				self.users_eds_map[k] = set(eds)

	def get_focal_orgs(self,id):
		"""
		gets set of orgs / eds for focal user
		"""
		# fetch focal user
		user = User.objects.get(pk=id)
		# initialize holding arrays
		orgs = []
		eds =[]
		# loop through all positions to get unique entity ids
		for p in user.positions.all():
			if p.type == "education":
				eds.append(p.entity.id)
			else:
				orgs.append(p.entity.id)
		orgs_set = set(orgs)
		eds_set = set(eds)
		focal_orgs = {
			'orgs': orgs_set,
			'eds': eds_set
		}
		return focal_orgs

	def find_similar_people_in_career(self,id,career):
		"""
		finds similar users within a career
		"""
		all_users_in_career = User.objects.values_list('id').filter(positions__careers__in=career)

		focal_orgs = self.get_focal_orgs(id) 
		sim = []
		
		for k,v in self.users_orgs_map_single.items():
			# check to see if user has the job
			if k in all_users_in_career:
				intersect = focal_orgs['orgs'].intersection(v)
				jaccard = float(len(intersect))/float(len(v))
				sim.append((k,jaccard,))

		sorted_sim = sorted(sim, key=lambda x:x[1],reverse=True)

		sorted_sim = [u[0] for u in sorted_sim]

		users = User.objects.filter(id__in=sorted_sim)

		return users

	def find_similar_people_in_position(self,id,pos):
		"""
		finds similar users within a position
		"""
		all_users_in_position = User.objects.values_list('id').filter(position__in=pos)

		focal_orgs = self.get_focal_orgs(id) 
		sim = []
		
		for k,v in self.users_orgs_map_single.items():
			# check to see if user has the job
			if k in all_users_in_position:
				intersect = focal_orgs['orgs'].intersection(v)
				jaccard = float(len(intersect))/float(len(v))
				sim.append((k,jaccard,))

		sorted_sim = sorted(sim, key=lambda x:x[1],reverse=True)

		sorted_sim = [u[0] for u in sorted_sim]

		users = User.objects.filter(id__in=sorted_sim)

		return users

	def find_similar_people(self,id):
		"""
		measures intersection of sets between focal and other users, returns User objects
		"""
		focal_orgs = self.get_focal_orgs(id) 
		sim = []
		
		for k,v in self.users_orgs_map_single.items():
			intersect = focal_orgs['orgs'].intersection(v)
			jaccard = float(len(intersect))/float(len(v))
			sim.append((k,jaccard,))

		sorted_sim = sorted(sim, key=lambda x:x[1],reverse=True)

		sorted_sim = [u[0] for u in sorted_sim]

		users = User.objects.filter(id__in=sorted_sim)

		return users

	def find_similar_people_ids(self,id):
		"""
		measures intersection of sets between focal user and other users to find most similar
		"""
		focal_orgs = self.get_focal_orgs(id) 
		orgs_sim = []
		eds_sim = []
		
		for k,v in self.users_orgs_map.items():
			intersect = focal_orgs['orgs'].intersection(v)
			jaccard = float(len(intersect))/float(len(v))
			orgs_sim.append((k,jaccard,))

		for k,v in self.users_eds_map.items():
			intersect = focal_orgs['eds'].intersection(v)
			jaccard = float(len(intersect))/float(len(v))
			eds_sim.append((k,jaccard,))	

		sorted_orgs_sim = sorted(orgs_sim, key=lambda x:x[1],reverse=True)
		sorted_eds_sim = sorted(eds_sim, key=lambda x:x[1],reverse=True)	

		sorted_orgs_sim = [u[0] for u in sorted_orgs_sim]

		return sorted_orgs_sim[:10]

	def get_careers_brief_similar(self,user,**filters):

		user_id = user.id

		users = self.find_similar_people_ids(user_id)
		
		careers = Career.objects.prefetch_related('positions').filter(positions__person_id__in=users).annotate(num_people=Count('positions__person__pk',num_pos=Count('positions__pk'),num_cos=Count('positions__entity__pk'))).order_by('-num_people').distinct()[:10]

		for c in careers:
			people = []
			cos = []
			c.num_pos = len(c.positions.all())
			for p in c.positions.all():
				people.append(p.person.id)
				cos.append(p.entity.id)
			c.num_people = len(set(people))
			c.num_cos = len(set(cos))

		# careers = sorted(careers.iteritems(),key=lambda x:x[0], reverse=True)

		return careers

class CareerPathBase(CareerBase):

	def get_ed_overview(self,user,career):
		"""
		returns ed breakdown of career by school, for network and all users
		"""
		users = self.get_users_in_career(career)
		connections = user.profile.connections.all()
		schools = Entity.objects.filter(li_type='school').values('id','name')
		
		# initialize dictionary
		eds_all = {}
		eds_network = {}
		eds = {}
		# loop through all users in a career
		for u in users:
			user_eds_all = []
			user_eds_network = []
			for p in u.positions.all():
				if p.type == "education":
					user_eds_all.append(p.entity.id)
				# if u.profile in user.profile.connections.all():
				if u.profile in connections:
					user_eds_network.append(p.entity.id)
			user_eds_all = set(user_eds_all)
			user_eds_network = set(user_eds_network)
			for e in user_eds_all:
				if e in eds_all:
					eds_all[e]['count'] += 1
				else:
					for s in schools:
						if e == s['id']:
							# org = Entity.objects.get(pk=e)
							eds_all[e] = {'count':1,'name':s['name']}
			for e in user_eds_network:
				if e in eds_network:
					eds_network[e]['count'] += 1
				else:
					for s in schools:
						if e == s['id']:
							# org = Entity.objects.get(pk=e)
							eds_network[e] = {'count':1,'name':s['name']}
					# org = Entity.objects.get(pk=e)
					# eds_network[e] = {'count':1,'name':org.name}

		eds['network'] = eds_network
		eds['all'] = eds_all

		return eds

	def _user_career_duration(self,user,career):
		# get all positions from user
		positions = Position.objects.filter(person=user,careers=career).order_by('-start_date')
		# setup placeholder end date
		end_date = None
		# loop through all positions
		i = 0
		for p in positions:
			if i == 0:
				start_date = p.start_date
			if p.end_date:
				end_date = p.end_date
			i += 1
		# make sure there was at least one end_date
		if end_date is not None:
			# calculate duration
			# duration = end_date - start_date
			duration = start_date - end_date
			return duration
		else:
			return None

	def avg_duration_network(self,career,user):
		"""
		returns average time in career for focal user's network
		"""
		# users = self.get_full_users_in_network(user)
		# positions = Position.objects.filter(user=user.connections.all()).distinct()

		users = User.objects.filter(positions__careers=career)
		connections = user.profile.connections.all()
		durations = []
		for u in users:
			if u in connections:
				duration = self._user_career_duration(u,career)
				if duration is not None:
					durations.append(duration)
		if len(durations) > 0:
			avg = sum(durations,timedelta()) / len(durations)
			return round(avg.days / 365.25,2)
		return None

	def avg_duration_all(self,career):
		"""
		returns average time in career for all users
		"""
		users = User.objects.filter(positions__careers=career)

		durations = []
		for u in users:
			duration = self._user_career_duration(u,career)
			if duration is not None:
				durations.append(duration)
		if len(durations) > 0:
			avg = sum(durations,timedelta()) / len(durations)
			return round(avg.days / 365.25,2)
		return None

	def get_paths_in_career(self,user,career):
		# initialize overview array
		overview = {}
		paths = {}

		# get users in network
		users_list, user_ids = _get_users_in_network(user)

		# network_people = User.objects.prefetch_related().select_related('positions','entities','accounts').filter(id__in=user_ids,positions__careers=career).annotate(no_of_pos=Count('positions__pk')).order_by('-no_of_pos').distinct()
		# CAUTION--values() can return multiple records when requesting M2M values; make sure to reduce
		network_people = User.objects.select_related('profile','positions','pictures').values('id','profile__headline','profile__first_name','profile__last_name','profile__pictures__pic','positions__entity__id','positions__entity__name').filter(id__in=user_ids,positions__careers=career).annotate(no_of_pos=Count('positions__id')).order_by('-no_of_pos')

		# Clayton -- need to uniqify this list, b/c lots of wasted time
		#	parsing duplicate people ... EDIT: not the problem, problem is
		#	duplicate positions!
		# network_people = _order_preserving_uniquify(network_people)

		network_people_dict = {}
		num_pos = 0
		entities = []
		# entities = set()
		entities_dict = {}
		num_cos = 0
		network_positions = []
		# counter = 0

		## Network
		for p in network_people:
			# check to see if user is already in the dict
			if p['id'] not in network_people_dict:
				network_people_dict[p['id']] = {
					'full_name': p['profile__first_name'] + " " + p['profile__last_name'],
					'headline': p['profile__headline']
				}
			# check each record to make sure the profile pic gets picked up
			if 'profile__pictures__pic' in p:
				network_people_dict[p['id']]['pic'] = p['profile__pictures__pic']
			if 'positions__entity__id' in p:
			# increment the position counter
				entities.append(p['positions__entity__id'])
				num_pos += 1
				if p['positions__entity__name'] in entities_dict:
					entities_dict[p['positions__entity__name']]['count'] += 1
				else:
					entities_dict[p['positions__entity__name']] = {
						'count':1,
						'id':p['positions__entity__name']
					}
			# num_pos += len(p.positions.all())
			# # people_seen = set()
			# # positions_seen = set()

			# for pos in p.positions.all():
			# 	# num_pos += 1
			# 	entities.append(pos.entity.id)
			# 	# entities.add(pos.entity.id)

			# 	# if pos in career, add to positions
			# 	# 	additionally, impose 30 position cap
				
			# 	# if career in pos.careers.all():
			# 	# 	counter += 1
			# 	# 	print counter
			# 	#  	if len(network_positions) < 30:
			# 	# 		# check if seen already (avoid duplicates)
			# 	# 		if pos.id not in positions_seen:
			# 	# 			positions_seen.add(pos.id)
			# 	# 			network_positions.append({
			# 	# 				'id':pos.id,
			# 	# 				'title':pos.title,
			# 	# 				'co_name':pos.entity.name,
			# 	# 				'owner':pos.person.profile.full_name(),
			# 	# 				'owner_id':pos.person.id,
			# 	# 				'logo_path':pos.entity.default_logo(),
			# 	# 			})

			
			# 	if pos.entity.name in entities_dict:
			# 		entities_dict[pos.entity.name]['count'] += 1

			# 		# check if person seen already (avoid duplicates)
			# 		# 	additionally, cap people @ 5 for now
			# 		# if p.id not in people_seen and len(entities_dict[pos.entity.name]['people']) < 6:
						
			# 		# 	person_dict = {
			# 		# 		'name':p.profile.full_name(),
			# 		# 		'id':p.id,
			# 		# 	}
			# 		# 	entities_dict[pos.entity.name]['people'].append(person_dict)
			# 		# 	people_seen.add(p.id)

			# 	else:
			# 		# people_list = [{
			# 		# 	'name':p.profile.full_name(),
			# 		# 	'id':p.id,
			# 		# }]
					
			# 		entities_dict[pos.entity.name] = {
			# 			'count' : 1,
			# 			'id':pos.entity.id,
			# 			# 'logo':pos.entity.default_logo(),
			# 			# 'people':people_list,	
			# 		}

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


		num_cos = len(set(entities))
		# num_cos = len(entities)

		overview['network'] = {
			'num_people':len(network_people),
			'num_pos':num_pos,
			'num_cos':num_cos
		}

		all_people = User.objects.select_related('profile','positions','pictures').values('id','profile__headline','profile__first_name','profile__last_name','profile__pictures__pic','positions__entity__id','positions__entity__name').filter(positions__careers=career).annotate(no_of_pos=Count('positions__id')).order_by('-no_of_pos')
		# all_people = User.objects.select_related('positions').filter(positions__careers=career).annotate(no_of_pos=Count('positions__pk')).order_by('-no_of_pos').distinct()

		num_pos = 0
		entities = []
		# entities = set()
		all_entities_dict = {}
		all_positions = []
		num_cos = 0

		## ALL

		for p in all_people:
			# check to see if user is already in the dict
			if p['id'] not in network_people_dict:
				network_people_dict[p['id']] = {
					'full_name': p['profile__first_name'] + " " + p['profile__last_name']
				}
				# if ['profile__headline'] in p:
				# 	network_people_dict[p['id']]['headline'] = p['profile__headline']
				# check to see if this is a connected user
				if p['id'] in user_ids:
					network_people_dict[p['id']]['connected'] = True
				else:
					network_people_dict[p['id']]['connected'] = False
			# check each record to make sure the profile pic gets picked up
			if 'profile__pictures__pic' in p:
				network_people_dict[p['id']]['pic'] = p['profile__pictures__pic']
			if 'positions__entity__id' in p:
			# increment the position counter
				entities.append(p['positions__entity__id'])
				num_pos += 1
				if p['positions__entity__name'] in entities_dict:
					entities_dict[p['positions__entity__name']]['count'] += 1
				else:
					entities_dict[p['positions__entity__name']] = {
						'count':1,
						'id':p['positions__entity__name']
					}

		# loop through all positions, identify those that belong to connections
		# for p in all_people:
		# 	# check if position held by 
		# 	if p.id in user_ids:
		# 		p.connected = True
		# 	else:
		# 		p.connected = False

		# 	#num_pos += len(p.positions.all())
		# 	for pos in p.positions.all():
		# 		num_pos += 1
		# 		if pos.entity.name in all_entities_dict:
		# 			all_entities_dict[pos.entity.name]['count'] += 1
		# 		else:
		# 			all_entities_dict[pos.entity.name] = {
		# 				'id':pos.entity.id,
		# 				'count':1
		# 			}
		# 		# entities.append(pos.entity.id)
		# 		entities.add(pos.entity.id)

		num_cos = len(set(entities))
		# num_cos = len(entities)

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
		# paths['networkOrgs'] = entities_dict
		# paths['allOrgs'] = all_entities_dict

		# # TRIAL - adding positions information
		# paths['networkPositions'] = network_positions
		# paths['allPositions'] = all_positions

		# Returns nested dict
		paths['overview'] = {
			'network' : overview['network'],
			'all':overview['all'],
			}

		# return paths, overview
		return paths

	def get_focal_careers(self,user,limit=5):

		careers = Career.objects.prefetch_related('positions').annotate(num=Count('positions__pk')).order_by('-num').distinct()[:limit]

		return careers

	def get_careers_brief_in_network(self,user,**filters):

		cxns = user.profile.connections.all().values('user__id').select_related('user')

		users = [c['user__id'] for c in cxns]

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

		return careers

class CareerMapBase():

	# set max size of ngram
	NGRAM_MAX = 10

	# set min size of ngram
	NGRAM_MIN = 1

	# initialize global dictionary for career-to-position mapping
	careers_to_positions_map = {}

	# initilize array for stop words
	STOP_LIST = [
		'director',
		'manager',
		'intern',
		'aide',
		'clerk',
		'consultant',
		'program director',
		'sales',
		'founder'
	]

	def __init__(self):
		# fill in career to positions map
		self.init_career_to_positions_map()
		# self.load_stop_list()

	def load_stop_list(self):
		try:
			print 'trying to open reader'
			reader = (open('career_map_stop_list.csv','rU'))
		except:
			print 'reader dies'
			return None
		for row in reader:
			self.STOP_LIST.append(row[0])

	def tokenize_position(self,title):
		"""
		tokenizes position title based on spaces
		"""
		if title:
			# tokenize position title
			tokens = title.split(" ")
			# reduce all strings to lower case
			tokens = [t.lower() for t in tokens]
			return tokens
		return None

	def extract_ngrams(self,tokens):
		"""
		breaks position titles into appropriate number of ngrams and returns as a list
		"""
		if tokens:
			ngrams = []
			n_tokens = len(tokens)
			for i in range(n_tokens):
				for j in range(i+1,min(n_tokens,self.NGRAM_MAX)+1):
					ngram = " ".join(tokens[i:j])
					ngrams.append(ngram)
					# ngrams.append(tokens[i:j])

			return ngrams
		return None

	def init_career_to_positions_map(self):
		"""
		fill in career map dictionary from db
		"""
		# fetch career ids and position titles
		careers = Career.objects.values('id','pos_titles')

		# init career map dictionary
		career_map = {}

		for c in careers:
			if c['pos_titles'] is not None:
				titles = json.loads(c['pos_titles'])
				# add career-to-position title mapping, reduced to lower case
				if titles is not None:
					titles = [t.lower() for t in titles]
				
				career_map[c['id']] = titles

		self.careers_to_positions_map = career_map

	def match_careers_to_position(self,pos):
		# break position title into ngrams
		title_ngrams = self.extract_ngrams(self.tokenize_position(pos.title))
	
		# initialize careers array
		careers = []

		if title_ngrams is not None:
			for t in title_ngrams:
				if t is not None:
					# make sure position title is not in stop list, e.g., "Manager" or "Director" or something equally generic
					if t not in self.STOP_LIST:
						for k,v in self.careers_to_positions_map.items():
							if t in v and k not in careers:
								
								careers.append(k)
								# print t + ": " + career.name

		return careers
		# for c_id in careers:
		# 	c = Career.objects.get(pk=c_id)
		# 	pos.careers.add(c)
		# pos.save()

	def test_position(self,title):

		title_ngrams = self.extract_ngrams(self.tokenize_position(title))
		
		print title_ngrams

		for t in title_ngrams:
			# make sure position title is not in stop list, e.g., "Manager" or "Director" or something equally generic
			if t not in self.STOP_LIST:
				for k,v in self.careers_to_positions_map.items():
					# print v
					if t in v:
						career = Career.objects.get(pk=k)
						print title + " matches " + career.name

	def test_match_careers_to_position(self,title=None):

		positions = Position.objects.all()

		for p in positions:
			careers = []

			if p.title:
				title_ngrams = self.extract_ngrams(self.tokenize_position(p.title))

				# print title_ngrams

				for t in title_ngrams:
					# make sure position title is not in stop list, e.g., "Manager" or "Director" or something equally generic
					if t not in self.STOP_LIST:
						for k,v in self.careers_to_positions_map.items():
							if t in v and k not in careers:
								careers.append(k)
								career = Career.objects.get(pk=k)
								# print t + ": " + career.name
			print careers

	def list_unmatched_positions(self):
		'''
		print list of all positions that are not matched to a career
		'''
		positions = Position.objects.filter(careers=None).exclude(type="education")
		for p in positions:
			if p.title:
				print p.title

class CareerImportBase():

	# positions to never match, too general
	CENSUS_STOP_LIST = [
		'Intern',
		'Aide',
		'Assistant',
		'Attendant',
		'n.s.',
		'\ specified not listed',
		'Manager',
		'Director'
		]

	# trigger words to truncate position titles from census
	CENSUS_REMOVE_LIST = [
		r' \\ n\.s\.',
		r' \\ any activity',
		r'n\.s\.',
		r'--See',
		r', associate degree',
		r', less than associate degree',
		r', exc',
		r'\(.+\)',
		r'\\',
		r', specified',
		r', other specified',
		r', secretarial',
		r', exc'
	]

	# matches strings that should be split into separate strings
	CENSUS_SPLIT_LIST = [
		'Host/Hostess',
		'Waiter/Waitress'
	]

	def convert_career_titles_to_positions(self):
		careers = Career.objects.all()

		for c in careers:
			titles = c.get_pos_titles()
			if titles:
				for t in titles:
					try:
						ideal_pos = IdealPosition.objects.get(title=t)
					except:
						ideal_pos = IdealPosition(title=t)
					ideal_pos.save()
					ideal_pos.careers.add(c)
					ideal_pos.save()

	def test_import_census_matching_data(self,path):
		# initiate career dict
		career_positions_dict = {}
		# open file, conver to csv DictReader object
		f = open(path,'rU')
		c = csv.DictReader(f)
		# loop through each row in the file
		for row in c:
			
			title = row['2010 OCCUPATION TITLE']
			code = row['2010 Census Occupation Code']
			# make sure it's not a pointer row and has an actual occupation code
			if row['2010 Census Occupation Code']:
				# format position title
				# remove all patterns from the remove list
				for t in self.CENSUS_REMOVE_LIST:
					m = re.search(t,title)
					if m:
						title = title[:m.start()]
				# check to see if it's on stop list
				if title not in self.CENSUS_STOP_LIST:
					# check to see if the dictionary already has an entry for this
					if code not in career_positions_dict:
						# print title
						career_positions_dict[code] = [title]
					elif title not in career_positions_dict[code]:
						# print title
						career_positions_dict[code].append(title)
						# print career_positions_dict[code]
		for k,v in career_positions_dict.items():
			for position in v:
				if not isinstance(position,types.StringTypes):
					print k, str(position)
		f = open('careers_dump.txt','w')
		f.write(json.dumps(career_positions_dict))
		f.close()

	def import_census_matching_data(self,path):
		# initiate career dict
		career_positions_dict = {}
		# open file, conver to csv DictReader object
		f = open(path,'rU')
		c = csv.DictReader(f)
		# loop through each row in the file
		for row in c:
			title = row['2010 OCCUPATION TITLE']
			code = row['2010 Census Occupation Code']
			if row['2010 Census Occupation Code']:
				
				# format position title
				
				for t in self.CENSUS_REMOVE_LIST:
					m = re.search(t,title)
					if m:
						title = title[:m.start()]
				# check to see if it's on stop list
				if title not in self.CENSUS_STOP_LIST:
					if code not in career_positions_dict:
						# print title
						career_positions_dict[code] = [title]
					elif title not in career_positions_dict[code]:
						# print title
						career_positions_dict[code].append(title)
						# print career_positions_dict[code]
		# add each title to career
		for k,v in career_positions_dict.items():
			print k + ": " + str(v)
			# check to see if career already exists
			try:
				career = Career.objects.get(census_code=k)
			except MultipleObjectsReturned:	
				mult_careers = Career.objects.filter(census_code=k)
				career = mult_careers[0]
			except:
				career = Career()
				career.census_code = k
				career.save()
			for pos in v:
				career.add_pos_title(pos)
			career.save()
		# print career_positions_dict

	def import_careers_from_file(self,path):

		f = open(path,'rU')
		c = csv.DictReader(f)
		for row in c:
			career = Career()
			career.short_name = row['short_name']
			career.long_name = row['long_name']
			career.save()
			if row['titles'] is not None and row['titles'] is not "":
				new_titles = row['titles'].split(',')
				for t in new_titles:
					career.add_pos_title(t)
			career.save()

	def import_careers_from_url(self,path):

		data = urllib2.urlopen(path).read()
		c = csv.DictReader([data])
		for row in c:
			career = Career()
			career.short_name = row['short_name']
			career.long_name = row['long_name']
			career.save()
			if row['titles'] is not None and row['titles'] is not "":
				new_titles = row['titles'].split(',')
				for t in new_titles:
					career.add_pos_title(t)
			career.save()

class CareerExportBase():

	def export_careers_fixtures(self):
		"""
		exports JSON fixtures for careers in current directory
		"""
		file_name = 'careers_fixture_' + datetime.now().strftime('%Y%m%d%H%M') + '.json'
		careers = Career.objects.all().values('id','short_name','long_name','description','parent','census_code','soc_code','pos_titles')
		fixtures = json.dumps(list(careers))
		f = open(file_name,'w')
		f.write(fixtures)
		f.close()

	def export_careers(self):

		file_name = 'careers_' + datetime.now().strftime('%Y%m%d%H%M') + '.csv'
		fieldnames = {'short_name':'short_name','long_name':'long_name','titles':'titles'}
		f = open(file_name,'w')
		c = csv.DictWriter(f,fieldnames=fieldnames)
		careers = Career.objects.all()
		c.writerow(fieldnames)
		for career in careers:
			c.writerow({'short_name':career.short_name,'long_name':career.long_name,'titles':career.get_pos_titles()})
		f.close()

	def export_careers_to_screen(self):

		careers = Career.objects.values_list('id','short_name','long_name','soc_code','census_code','description','parent','pos_titles').all()

		stdout.write(list(careers))


# init_careers_to_positions_map()
# _load_stop_list()
