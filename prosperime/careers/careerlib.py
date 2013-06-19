# from Python
import json
import urllib2
from datetime import datetime
from datetime import timedelta
from datetime import date
import csv
import re
import os
import types

# from Django
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core import management
from django.db.models import Count, Q

# from ProsperMe
from entities.models import Industry, Entity
from careers.models import Career, Position, IdealPosition
from careers.positionlib import IdealPositionBase

def safe_int(data):
	if data is not None:
		return int(data)
	else:
		return None

def import_initial_ideals(path):
	career_import = CareerImportBase()
	career_import.import_initial_ideals(path)

def match_position_to_ideals(pos,test=False):
	career_map = CareerMapBase()
	return career_map.match_position_to_ideals(pos,test)

def get_prof_longevity(user):
	career_path = CareerPathBase()
	return career_path.get_prof_longevity(user)

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

def get_paths_in_career(user,career):
	career_path = CareerPathBase()
	return career_path.get_paths_in_career(user,career)

def match_careers_to_position(pos):
	career_mapper = CareerMapBase()
	careers = career_mapper.match_careers_to_position(pos)
	return careers

def match_degree(deg):
	"""
	takes user input and matches to valid degree
	"""
	mapper = EdMapper()
	return mapper.match_degree(deg)


class CareerBase():

	def get_users_in_career_full(self,career):

		users = User.objects.prefetch_related('profile__connections').select_related('positions').filter(positions__careers=career)

		return users

	def get_users_in_network(user,**filters):

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
	flat_users = []
	user_ids = []
	# initializes single map
	users_orgs_map_single = {}
	users_orgs_map_single_valued = {}

	# initializes organizational map
	users_orgs_map = {}

	# initialize educational map
	users_eds_map = {}

	def __init__(self):
		self.load_users()
		self.load_maps()
		self.load_single_map()

	def _calc_time(self,x):
		"""
		calculates length of position
		"""
		
		start = x['positions__start_date']
		end = x['positions__end_date']
		if start:
			if not end:
				change = date.today() - start
			else:
				change = end - start

			return (x['id'],x['positions__entity__id'],abs(round(change.days / 365.25,2)),)


	def load_users(self):
		users = User.objects.values('id','positions__type','positions__entity__id','positions__start_date','positions__end_date')
		self.flat_users = users
		users_dict = {}
		for u in users:
			if u['id'] in users_dict:
				users_dict[u['id']]['positions'].append({'type':u['positions__type'],'id':u['positions__entity__id']})
			else:
				users_dict[u['id']] = {'positions':[{'type':u['positions__type'],'id':u['positions__entity__id']}]}
		self.users = users_dict
		self.user_ids = list(set([u['id'] for u in users]))
		# print self.users

	def load_single_map(self):
		"""
		loads set of org affiliations for each user
		"""
		# map positions to calculate duration
		mapped_list = map(self._calc_time,self.flat_users)
		# reduce / filter map
		for m in mapped_list:
			if m:
				# relabel variables for sanity
				u_id = m[0]
				e_id = m[1]
				dur = m[2]
				# add user if not already in array
				if u_id not in self.users_orgs_map_single_valued:
					self.users_orgs_map_single_valued[u_id] = {e_id:dur}
				# add entity if not in array
				elif e_id not in self.users_orgs_map_single_valued[u_id]:
					self.users_orgs_map_single_valued[u_id][e_id] = dur

				# else add to duration of existing entity entry
				else:
					self.users_orgs_map_single_valued[u_id][e_id] = dur + self.users_orgs_map_single_valued[u_id][e_id]

			
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
	
	def profile_get_majors_data(self):
		import cProfile

		cProfile.runctx('self.get_majors_data()',globals(),locals())

	def entry_positions_stats(self,user,career):

		# get all positions
		positions = positionson.objects.values('person_id','title').filter(careers=career).order_by('start_date')

		# init array of all connections
		connections = [u['user_id'] for u in user.profile.connections.values('user_id')]

		# init arrays
		entry_dict_network = {}
		senior_dict_users_network = {}
		senior_dict_network = {}
		entry_dict_all = {}
		senior_dict_users_all = {}
		senior_dict_all = {}		
		users_network = []
		users_all = []

		for p in positions:
			# check to see if in network
			if p['person_id'] in connections and p['person_id'] not in users_network:
				if p['title'] not in entry_dict_network:
					entry_dict_network[p['title']] = 1
				else:
					entry_dict_network[p['title']] += 1
				users_network.append(p['person_id'])
			elif p['person_id'] in connections and p['person_id'] in users_network:
				# add each successive position to users senior slot
				senior_dict_users_network[p['person_id']] = p['title']
			# if not in network add to all arrays
			elif p['person_id'] not in connections and p['person_id'] not in users_all:
				if p['title'] not in entry_dict_all:
					entry_dict_all[p['title']] = 1
				else:
					entry_dict_all[p['title']] += 1
				users_all.append(p['person_id'])
			elif p['person_id'] not in connections and p['person_id'] in users_all:
				# add each successive position to user's senior slot
				senior_dict_users_all[p['person_id']] = p['title']

		# sort entry dicts
		entry_dict_network_sorted = sorted(entry_dict_network.iteritems(), key=lambda x: x[1], reverse=True)
		entry_dict_all_sorted = sorted(entry_dict_all.iteritems(), key=lambda x: x[1], reverse=True)

		# compile senior dicts
		for k,v in senior_dict_users_network.items():
			if v not in senior_dict_network:
				senior_dict_network[p['title']] = 1
			else:
				senior_dict_network[p['title']] += 1

		for k,v in senior_dict_users_all.items():
			if v not in senior_dict_all:
				senior_dict_all[p['title']] = 1
			else:
				senior_dict_all[p['title']] += 1

		# sort senior dicts
		senior_dict_network_sorted = sorted(senior_dict_network.iteritems(), key=lambda x: x[1], reverse=True)
		senior_dict_all_sorted = sorted(senior_dict_all.iteritems(), key=lambda x: x[1], reverse=True)

		entry = {
			'network':entry_dict_network_sorted,
			'all':entry_dict_all_sorted
		}

		senior = {
			'network':senior_dict_network_sorted,
			'all':senior_dict_all_sorted
		}

		return (entry, senior, )

	def get_ed_overview(self,user,career):
		"""
		returns ed breakdown of career by school, for network and all users
		"""
		# users = self.get_users_in_career(career)
		users = User.objects.values('id','positions__type','positions__entity__name','positions__entity_id').prefetch_related('profile__connections').select_related('positions').filter(positions__careers=career)
		# positions = Position.objects.values('type','entity_id','entity__name','person_id').filter(careers=career,type="education")
		# preload all connections
		connections = [u['user_id'] for u in user.profile.connections.values('user_id')]
		# schools = Entity.objects.filter(li_type='school').values('id','name')
		
		# initialize dictionary
		eds_all = {}
		eds_network = {}
		eds = {}
		users_all = {}
		users_network = {}

		# loop through all users in a career
		for p in users:
			if p['positions__type'] == 'education':
				# check to see if this user-ed relationship has already been counted
				if p['id'] in users_all:
					if p['positions__entity_id'] not in users_all[p['id']]:
						if p['positions__entity_id'] not in eds_all:
							eds_all[p['positions__entity_id']] = {'count':1,'name':p['positions__entity__name']}
						else:
							eds_all[p['positions__entity_id']]['count'] += 1
				else:
					users_all[p['id']] = [p['positions__entity_id']]
					if p['positions__entity_id'] not in eds_all:
						eds_all[p['positions__entity_id']] = {'count':1,'name':p['positions__entity__name']}
					else:
						eds_all[p['positions__entity_id']]['count'] += 1
				# check to see if this user is part of the focal user's connections
				if p['id'] in connections:
					if p['id'] in users_network:
						if p['positions__entity_id'] not in users_network[p['id']]:
							if p['positions__entity_id'] not in eds_network:
								eds_network[p['positions__entity_id']] = {'count':1,'name':p['positions__entity__name']}
							else:
								eds_network[p['positions__entity_id']]['count'] += 1
					else:
						users_network[p['id']] = [p['positions__entity_id']]
						if p['positions__entity_id'] not in eds_network:
							eds_network[p['positions__entity_id']] = {'count':1,'name':p['positions__entity__name']}
						else:
							eds_network[p['positions__entity_id']]['count'] += 1

		eds['network'] = eds_network
		eds['all'] = eds_all

		return eds

	def _user_career_duration(self,user_id,career):
		# get all positions from user
		positions = Position.objects.values('start_date','end_date').filter(person_id=user_id,careers=career).order_by('-start_date')
		# setup placeholder end date
		end_date = None
		# loop through all positions
		i = 0
		for p in positions:
			if i == 0:
				start_date = p['start_date']
			if p['end_date'] is not None:
				end_date = p['end_date']
			i += 1
		# make sure there was at least one end_date
		if end_date is not None:
			# calculate duration
			# duration = end_date - start_date
			duration = end_date - start_date
			return duration
		else:
			return None

	def get_avg_duration(self,user,career):
		"""
		returns average time in career
		"""
		# users = self.get_full_users_in_network(user)
		# positions = Position.objects.filter(user=user.connections.all()).distinct()

		# init general dict
		avg_duration = {}
		# get all users
		users = User.objects.values('id').filter(positions__careers=career)
		
		# get list of all connections
		connections = [u['user_id'] for u in user.profile.connections.values('user_id')]
		
		# init array of durations
		network_durations = []
		all_durations = []
		
		# loop through all users, get duration
		for u in users:
			# check to see if user is in network
			if u['id'] in connections:
				duration = self._user_career_duration(u['id'],career)
				if duration is not None:
					network_durations.append(duration)
			# compile all stats
			duration = self._user_career_duration(u['id'],career)
			if duration is not None:
				all_durations.append(duration)

		# compile network durations
		if len(network_durations) > 0:
			avg = sum(network_durations,timedelta()) / len(network_durations)
			avg_duration['network'] = abs(round(avg.days / 365.25,2))
		else:
			avg_duration['network'] = None

		# compile all durations
		if len(all_durations) > 0:
			avg = sum(all_durations,timedelta()) / len(all_durations)
			avg_duration['all'] = abs(round(avg.days / 365.25,2))
		else:
			avg_duration['all'] = None

		return avg_duration

	def get_paths_in_career(self,user,career):
		# initialize overview array
		overview = {}
		paths = {}

		# get users in network
		# users_list, user_ids = _get_users_in_network(user)

		# init list of connections
		connections = [u['user_id'] for u in user.profile.connections.values('user_id')]

		# get all people (filter for connections in later step)
		# network_people = User.objects.prefetch_related().select_related('positions','entities','accounts').filter(id__in=user_ids,positions__careers=career).annotate(no_of_pos=Count('positions__pk')).order_by('-no_of_pos').distinct()
		# CAUTION--values() can return multiple records when requesting M2M values; make sure to reduce
		# network_people = User.objects.select_related('profile','positions','pictures').values('id','profile__headline','profile__first_name','profile__last_name','profile__pictures__pic','positions__entity__id','positions__entity__name').filter(id__in=user_ids,positions__careers=career).annotate(no_of_pos=Count('positions__id')).order_by('-no_of_pos')
		people = User.objects.select_related('profile','positions','pictures').values('id','profile__headline','profile__first_name','profile__last_name','profile__pictures__pic','positions__entity__id','positions__entity__name').filter(positions__careers=career).annotate(no_of_pos=Count('positions__id')).order_by('-no_of_pos')

		# Clayton -- need to uniqify this list, b/c lots of wasted time
		#	parsing duplicate people ... EDIT: not the problem, problem is
		#	duplicate positions!
		# network_people = _order_preserving_uniquify(network_people)

		network_people_dict = {}
		network_num_pos = 0
		network_entities = []
		network_entities_dict = {}
		network_num_cos = 0
		# network_positions = []
		network_num_people = 0

		all_people_dict = {}
		all_num_pos = 0
		all_entities = []
		all_entities_dict = {}
		all_num_cos = 0
		# all_positions = []
		all_num_people = 0

		# loop through all people, filter for those in and out of network, build dicts of paths
		for p in people:
			# check to see if in the network
			if p['id'] in connections:
				# check to see if user is already in the dict
				if p['id'] not in network_people_dict:
					network_people_dict[p['id']] = {
						'full_name': p['profile__first_name'] + " " + p['profile__last_name'],
						'headline': p['profile__headline']
					}
					network_num_people += 1
				# check each record to make sure the profile pic gets picked up
				if 'profile__pictures__pic' in p:
					network_people_dict[p['id']]['pic'] = p['profile__pictures__pic']
				if 'positions__entity__id' in p:
					network_entities.append(p['positions__entity__id'])
					network_num_pos += 1
					if p['positions__entity__name'] in network_entities_dict:
						network_entities_dict[p['positions__entity__name']]['count'] += 1
					else:
						network_entities_dict[p['positions__entity__name']] = {
							'count':1,
							'id':p['positions__entity__id']
						}
			# add all positions
			if p['id'] not in all_people_dict:
				all_people_dict[p['id']] = {
					'full_name': p['profile__first_name'] + " " + p['profile__last_name'],
					'headline': p['profile__headline']
				}
				# check to see if this is a connected user
				if p['id'] in connections:
					all_people_dict[p['id']]['connected'] = True
				else:
					all_people_dict[p['id']]['connected'] = False
				all_num_people += 1
			# check each record to make sure the profile pic gets picked up
			if 'profile__pictures__pic' in p:
				all_people_dict[p['id']]['pic'] = p['profile__pictures__pic']
			if 'positions__entity__id' in p:
			# increment the position counter
				all_entities.append(p['positions__entity__id'])
				all_num_pos += 1
				if p['positions__entity__name'] in all_entities_dict:
					all_entities_dict[p['positions__entity__name']]['count'] += 1
				else:
					all_entities_dict[p['positions__entity__name']] = {
						'count':1,
						'id':p['positions__entity__id']
					}
						

		# overview stats for network
		network_num_cos = len(set(network_entities))
		# num_cos = len(entities)

		overview['network'] = {
			'num_people':network_num_people,
			'num_pos':network_num_pos,
			'num_cos':network_num_cos
		}

		# overview stats for whole community
		all_num_cos = len(set(all_entities))
		# num_cos = len(entities)

		overview['all'] = {
			'num_people':all_num_people,
			'num_pos':all_num_pos,
			'num_cos':all_num_cos
		}

		# Network Entities Top 3
		network_entities_dict = sorted(network_entities_dict.iteritems(), key=lambda x: x[1]['count'], reverse=True)
		overview['network']['bigplayers'] = network_entities_dict[:3]

		# All Entities Top 3
		all_entities_dict = sorted(all_entities_dict.iteritems(), key=lambda x: x[1]['count'], reverse=True)
		overview['all']['bigplayers'] = all_entities_dict[:3]

		# People in Network, All
		paths['network'] = network_people_dict
		paths['all'] = all_people_dict

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

	CAREER_SCORE = {
		0:1,
		1:1.2,
		2:1.4,
		3:1.6,
		4:1.8,
		5:2.0
	}

	def focal_career_keyfunc(self,tup):
		key, d = tup
		return d['score']

	def get_focal_careers(self,users,limit=5):
		from operator import itemgetter
		# get all user positions
		positions = Position.objects.filter(person__in=users)
		# init array
		careers = {}
		# init vars
		all_dur = 0
		# loop through positions
		for p in positions:
			if p.ideal_position:
				p.dur = p.duration_in_years() if p.duration_in_years() is not None else 1
				p.level = p.ideal_position.level
				all_dur += p.dur
				
		# now that we have whole duration, loop through again
		for p in positions:
			if p.ideal_position:
				score = self.CAREER_SCORE[p.level] * (p.dur / all_dur)
				# loop through each career attached to position
				for c in p.ideal_position.careers.all():
					# check to see if career is already in dict
					if c.id in careers:
						careers[c.id]['score'] += score
					else:
						careers[c.id] = {
							'name':c.name,
							'id':c.id,
							'score':score
						}

		careers_sorted = sorted(careers.items(),key=self.focal_career_keyfunc,reverse=True)

		return careers_sorted

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

	def get_careers_in_schools(self,schools,user=None):
		# get all users related to school
		school_ids = [s.id for s in schools]
		users = User.objects.filter(positions__entity__id__in=school_ids)
		# get focal careers
		careers = self.get_focal_careers(users)
		# restructure into easier list
		all_careers = [{'id':c[0],'name':c[1]['name']} for c in careers]
		return all_careers

	def get_careers_from_major(self,major,user=None):
		"""
		returns list of careers from users with same degree
		"""
		# get relevant users
		if user:
			schools = Entity.objects.filter(type="school",positions__person=user)
			users = User.objects.filter(positions__ideal_position=major,positions__entity__in=schools)
		else:
			users = User.objects.filter(positions__ideal_position=major)
		# get focal careers
		careers = self.get_focal_careers(users)
		# restructure into easier list
		all_careers = [{'id':c[0],'name':c[1]['name']} for c in careers]

	def get_paths_from_schools(self,schools,user=None,limit=5):
		"""
		returns a set of user paths that contain the school
		"""
		users = User.objects.filter(positions__entity__in=schools,profile__status="active").distinct()[:5]
		return users

	def get_first_jobs_from_major(self,major,user=None):
		"""
		returns a list of first jobs users held after completing a particular major
		"""
		# init global vars
		paths = {}
		next = False
		final = False
		# if user is set, restrict to network
		if user:
			schools = [e['id'] for e in Entity.objects.filter(positions__person=user,positions__type="education").values('id')]
			users = User.objects.select_related("positions").filter(positions__ideal_position=major,positions__entity__id__in=schools)
		else:
			# get all users who shared major
			users = User.objects.select_related("positions").filter(positions__ideal_position=major,profile__status="active")
		# loop through
		for u in users:
			for p in u.positions.all().order_by("start_date"):

				if final:
					continue
				if next:
					# exclude education positions
					if p.type == "education":
						continue
					if not p.ideal_position:
						continue
					if p.ideal_position.id in paths:
						paths[p.ideal_position.id]['count'] += 1
					else:
						paths[p.ideal_position.id] = {
							'title':p.ideal_position.title,
							'id':p.id,
							'ideal_id':p.ideal_position.id,
							'count':1
						}
				if p.ideal_position == major:
					next = True
		paths = sorted(paths.iteritems(),key=lambda x: x[1]['count'],reverse=True)
		return paths

	def get_first_jobs_from_schools(self,schools,user=None):
		""" 
		returns a list of first jobs users held after leaving school
		"""
		# init global vars
		paths = {}
		next = False
		final = False
		users = User.objects.select_related("positions").filter(positions__entity__in=schools)
		for u in users:
			for p in u.positions.all().order_by("start_date"):
				if final:
					continue
				if next:
					if not p.ideal_position:
						continue
					if p.ideal_position.id in paths:
						paths[p.ideal_position.id]['count'] += 1
					else:
						paths[p.ideal_position.id] = {
							'title':p.ideal_position.title,
							'id':p.id,
							'ideal_id':p.ideal_position.id,
							'count':1
						}
				if p.entity in schools:
					next = True
		paths = sorted(paths.iteritems(),key=lambda x: x[1]['count'],reverse=True)
		return paths

	def get_prof_longevity(self,user):
		positions = Position.objects.filter(person=user).order_by("start_date").exclude(type="education")
		start_date = positions[0].start_date
		end_date = None
		z = False
		i = positions.count() - 1
		while not z:
			# print "@ get_prof_longevity -- cycling"
			if positions[i].end_date:
				z = True
				end_date = positions[i].end_date
			i = i - 1
		
		if end_date:
			delta = end_date - start_date
		else:
			delta = datetime.datetime.today() - start_date

		years = round(delta.days / 365.25,0)
		if years > 10:
			return "10+"
		return years


	def get_majors_data(self,**opts):
		"""
		returns data on majors, first jobs and users
		"""
		# get optional params

		user = opts.get('user',None)

		people = []
		positions = []
		majors = {}

		majors_set = set()
		people_set = set()
		positions_set = set()

		counter = 0

		# get schools from user
		if user:
			schools = Entity.objects.filter(li_type="school",positions__person=user,positions__type="education").distinct()
		else:
			schools = None

		# acceptable_majors = ["Science, Technology, and Society", "English", "Psychology", "Management Science & Engineering", "Computer Science", "International Relations", "Political Science", "Economics", "Human Biology", "Product Design", "History", "Civil Engineering", "Electrical Engineering", "Physics", "Symbolic Systems", "Mechanical Engineering", "Spanish", "Public Policy", "Materials Science & Engineering", "Biomechanical Engineering", "Mathematics", "Classics", "Feminist Studies", "Mathematical and Computational Sciences", "Atmosphere and Energy Engineering", "Urban Studies", "Chemistry", "Chemical Engineering", "Religious Studies", "Earth Systems"]
		# base_positions = Position.objects.filter(type="education", field__in=acceptable_majors).exclude(ideal_position=None).select_related("person")
		
		# get ideals
		first_ideals = dict((u['id'],u['profile__first_ideal_job']) for u in User.objects.values('id','profile__first_ideal_job'))

		# assemble all the positions
		
		if schools:
			# base_positions = Position.objects.filter(type="education",entity__in=schools).exclude(ideal_position=None).select_related("person")
			base_positions = Position.objects.filter(type="education",entity__in=schools).exclude(ideal_position=None).values('ideal_position__major','title','degree','field','ideal_position__id','person__id','person__profile__first_name','person__profile__last_name')
		else:
			# base_positions = Position.objects.filter(type="education",ideal_position__level=1).exclude(ideal_position=None,person__profile__status="crunchbase").select_related("person")
			# print "getting positions..."
			# base_positions = Position.objects.filter(type="education",ideal_position__level=1).exclude(ideal_position=None,person__profile__status="crunchbase").exclude(ideal_position=None).values('ideal_position__major','title','degree','field','ideal_position__id','person__id','person__profile__first_name','person__profile__last_name')
			base_positions = Position.objects.filter(type="education",ideal_position__level=1).values('person__profile__status','ideal_position__major','title','degree','field','ideal_position__id','person__id','person__profile__first_name','person__profile__last_name')
		# print "looping through positions..."
		for p in base_positions:
			if p['person__profile__status'] == 'crunchbase':
				continue
			# first_ideal = p.person.profile.first_ideal()
			# first_ideal = p.person.profile.first_ideal_job()
			# first_ideal = User.objects.get(id=p['person__id']).profile.first_ideal_job()
			# print first_ideals[p['person__id']]
			# first_ideal = IdealPosition.objects.get(id=first_ideals[p['person__id']]).values('id','major','title')
			
			if first_ideals[p['person__id']] is not None:
				first_ideal = IdealPosition.objects.get(position__id=first_ideals[p['person__id']])
			else:
				first_ideal = None
			# print first_ideal
			# first_ideal = first_ideals[p['person__id']]
			
			# get full name
			full_name = " ".join([p['person__profile__first_name'],p['person__profile__last_name']])
			# Majors
			if first_ideal:
				if p['ideal_position__major'] is None:
					continue
					# print p.title, p.degree, p.field
					# print p.ideal_position, p.ideal_position.id
				if p['ideal_position__major'] not in majors_set:
					majors_set.add(p['ideal_position__major'])
					majors[p['ideal_position__major']] = {"id":[p['ideal_position__id']],"people":[p['person__id']], "positions":[first_ideal.id], "index":len(majors_set)}
				# if p.field not in majors_set:
				# 	majors_set.add(p.field)
				# 	majors[p.field] = {"people":[p.person.id], "positions":[first_ideal.id], "index":len(majors_set)}
				else:
					# majors[p.field]["people"].append(p.person.id)
					# majors[p.field]["positions"].append(first_ideal.id)
					majors[p['ideal_position__major']]["people"].append(p['person__id'])
					majors[p['ideal_position__major']]["positions"].append(first_ideal.id)

				# People
				if p['person__id'] not in people_set:

					people_set.add(p['person__id'])
					people.append({'name':full_name, 'id':p['person__id'], "major_index":majors[p['ideal_position__major']]["index"], "major":p['ideal_position__major']})

					counter += 1	
					if counter == 72:
						break;


				if first_ideal.id not in positions_set:
					positions_set.add(first_ideal.id)
					positions.append({'title':first_ideal.title, 'id':first_ideal.id, "major_index":majors[p['ideal_position__major']]["index"], "major":p['ideal_position__major']})

		data = {
			"majors":json.dumps(majors),
			"positions":json.dumps(positions),
			"people":json.dumps(people),
			"result":"success"
		}

		return data

	def get_major_data(self,major,user=None,**opts):
		"""
		returns on a specific major, including users, first jobs, and current jobs
		"""
		from accounts.models import Profile
		
		# init arrays and sets
		people = []
		first_jobs = {}
		current_jobs = {}

		people_set = set()
		first_jobs_set = set()
		current_jobs_set = set()

		# get schools from user
		if user:
			schools = Entity.objects.filter(li_type="school",positions__person=user,positions__type="education").distinct()
		else:
			schools = None

		users = User.objects.filter(positions__ideal_position__id=major)
		# add schools filter if present
		if schools:
			users = users.filter(positions__entity__in=schools)

		first_ideals = dict((u.id,u.profile.first_ideal_job) for u in users)

		current_ideals = dict((u.id,u.profile.current_ideal_position()) for u in users)

		base_positions = Position.objects.filter(type="education",ideal_position__id=major).values('person__profile__status','ideal_position__major','ideal_position__title','title','degree','field','ideal_position__id','person__id','person__profile__first_name','person__profile__last_name')
		if schools:
			base_positions = base_positions.filter(entity__in=schools)


		for p in base_positions:
			# get first and current ideals 
			first_ideal = first_ideals[p['person__id']]
			current_ideal = current_ideals[p['person__id']]
			# skip this relationship if they don't have ideal position on either end
			if first_ideal is None or current_ideal is None:
				continue

			if p['person__id'] not in people_set:
				pic = Profile.objects.get(user__id=p['person__id']).default_profile_pic()
				fullname = p['person__profile__first_name'] + " " + p['person__profile__last_name']
				people_set.add(p['person__id'])
				people.append({"id":p['person__id'],"fullname":fullname,"first_job":first_ideal.id, "current_job":current_ideal.id,"pic":pic})
				
			if first_ideal.id not in first_jobs_set:
				first_jobs_set.add(first_ideal.id)
				first_jobs[first_ideal.id] = {"id":first_ideal.id,"title":first_ideal.title,"people":[p['person__id']],'current_jobs':[current_ideal.id]}
			else:
				first_jobs[first_ideal.id]['people'].append(p['person__id'])
				first_jobs[first_ideal.id]['current_jobs'].append(current_ideal.id)

			if current_ideal.id not in current_jobs_set:
				current_jobs_set.add(current_ideal.id)
				current_jobs[current_ideal.id] = {'id':current_ideal.id,"title":current_ideal.title,"people":[p['person__id']],"first_jobs":[first_ideal.id]}
			else:
				current_jobs[current_ideal.id]['people'].append(p['person__id'])
				current_jobs[current_ideal.id]['first_jobs'].append(first_ideal.id)

		first_jobs_list = [{"id":v['id'],"title":v['title'],"people":v['people'],'current_jobs':v['current_jobs']} for k,v in first_jobs.iteritems()]
		current_jobs_list = [{"id":v['id'],"title":v['title'],"people":v['people'],'first_jobs':v['first_jobs']} for k,v in current_jobs.iteritems()]

		data = {
			"current_jobs":current_jobs_list,
			"first_jobs":first_jobs_list,
			"people":people,
			"result":"success"
		}

		return data


	def get_majors_data_new(self,user=None,**opts):
		"""
		returns data on majors, first jobs and users
		"""
		from accounts.models import Profile
		# get optional params

		schools = opts.get('schools',None)
		majors_query = opts.get('majors',None)
		job = opts.get('jobs',None)
		
		people = []
		positions = []
		majors = {}

		majors_set = set()
		people_set = set()
		positions_set = set()

		counter = 0

		# get schools from user
		if user and schools:
			schools = Entity.objects.filter(Q(li_type="school",positions__person=user,positions__type="education")|Q(id__in=schools)).distinct()
		elif user:
			schools = Entity.objects.filter(li_type="school",positions__person=user,positions__type="education").distinct()
		elif schools:
			schools = Entity.objects.filter(id__in=schools).distinct()
		else:
			schools = None

		# acceptable_majors = ["Science, Technology, and Society", "English", "Psychology", "Management Science & Engineering", "Computer Science", "International Relations", "Political Science", "Economics", "Human Biology", "Product Design", "History", "Civil Engineering", "Electrical Engineering", "Physics", "Symbolic Systems", "Mechanical Engineering", "Spanish", "Public Policy", "Materials Science & Engineering", "Biomechanical Engineering", "Mathematics", "Classics", "Feminist Studies", "Mathematical and Computational Sciences", "Atmosphere and Energy Engineering", "Urban Studies", "Chemistry", "Chemical Engineering", "Religious Studies", "Earth Systems"]
		# base_positions = Position.objects.filter(type="education", field__in=acceptable_majors).exclude(ideal_position=None).select_related("person")
		
		# get ideals
		first_ideals = dict((u['id'],u['profile__first_ideal_job']) for u in User.objects.values('id','profile__first_ideal_job'))

		# assemble all the positions
		base_positions = Position.objects.filter(type="education",ideal_position__level=1).values('person__profile__status','ideal_position__major','ideal_position__title','title','degree','field','ideal_position__id','person__id','person__profile__first_name','person__profile__last_name')
		if schools:
			# base_positions = Position.objects.filter(type="education",entity__in=schools).exclude(ideal_position=None).select_related("person")
			base_positions = base_positions.filter(entity__in=schools)
		if majors_query:
			print majors_query
			base_positions = base_positions.filter(ideal_position__id__in=majors_query)	


		# base_positions.values('person__profile__status','ideal_position__major','ideal_position__title','title','degree','field','ideal_position__id','person__id','person__profile__first_name','person__profile__last_name')
		# print "looping through positions..."
		for p in base_positions:
			if p['person__profile__status'] == 'crunchbase':
				continue
			# first_ideal = p.person.profile.first_ideal()
			# first_ideal = p.person.profile.first_ideal_job()
			# first_ideal = User.objects.get(id=p['person__id']).profile.first_ideal_job()
			# print first_ideals[p['person__id']]
			# first_ideal = IdealPosition.objects.get(id=first_ideals[p['person__id']]).values('id','major','title')
			
			if first_ideals[p['person__id']] is not None:
				first_ideal = IdealPosition.objects.get(position__id=first_ideals[p['person__id']])
			else:
				first_ideal = None
			# print first_ideal
			# first_ideal = first_ideals[p['person__id']]
			if job and first_ideal.id != job:
				continue
			# get full name
			full_name = " ".join([p['person__profile__first_name'],p['person__profile__last_name']])
			# Majors
			if first_ideal:
				if p['ideal_position__major'] is None:
					continue
					# print p.title, p.degree, p.field
					# print p.ideal_position, p.ideal_position.id
				if p['ideal_position__major'] not in majors_set:
					majors_set.add(p['ideal_position__major'])
					majors[p['ideal_position__major']] = {"id":p['ideal_position__id'],"people":[p['person__id']], "positions":[first_ideal.id], "index":len(majors_set), "abbr":p['ideal_position__title'][:5]}
				# if p.field not in majors_set:
				# 	majors_set.add(p.field)
				# 	majors[p.field] = {"people":[p.person.id], "positions":[first_ideal.id], "index":len(majors_set)}
				else:
					# majors[p.field]["people"].append(p.person.id)
					# majors[p.field]["positions"].append(first_ideal.id)
					majors[p['ideal_position__major']]["people"].append(p['person__id'])
					majors[p['ideal_position__major']]["positions"].append(first_ideal.id)

				# People
				if p['person__id'] not in people_set:

					people_set.add(p['person__id'])
					pic = Profile.objects.get(user__id=p['person__id']).default_profile_pic()
					# people.append({'name':full_name, 'id':p['person__id'], 'major_id':p['ideal_position__id'],"major_index":majors[p['ideal_position__major']]["index"], "major":p['ideal_position__major'],"pic":pic})
					people.append({'name':full_name, 'id':p['person__id'], 'major_id':p['ideal_position__id'], "major":p['ideal_position__major'],"pic":pic})


					counter += 1	
					if counter == 84:
						break;


				if first_ideal.id not in positions_set:
					positions_set.add(first_ideal.id)
					# positions.append({'title':first_ideal.title, 'id':first_ideal.id,'major_id':p['ideal_position__id'], "major_index":majors[p['ideal_position__major']]["index"], "major":p['ideal_position__major']})
					positions.append({'title':first_ideal.title, 'id':first_ideal.id,'major_id':p['ideal_position__id'],"major":p['ideal_position__major']})

				## else: add major id, major_index to the position


		data = {
			"majors":json.dumps(majors),
			"positions":json.dumps(positions),
			"people":json.dumps(people),
			"result":"success"
		}

		return data

class CareerBuild(CareerPathBase):

	def keyfunc(self,tup):
		key, d = tup
		return d['count']

	def get_position_paths_from_ideal(self,ideal_id):
		# fetch all users / positions that have the ideal position in their career
		users = User.objects.values('id','positions__id','positions__type','positions__degree','positions__ideal_position_id','positions__ideal_position__title','positions__ideal_position__level','positions__title','positions__degree','positions__entity__name','positions__entity_id','positions__type').filter(positions__ideal_position_id=ideal_id).order_by('positions__start_date').distinct()
		# init array
		paths = {}
		# collapse and sort by user
		for user in users:
			paths[user['id']] = [{'id':safe_int(u['id']),'title':u['positions__title'],'ideal_title':u['positions__ideal_position__title'],'entity_id':safe_int(u['positions__entity_id']),'entity_name':u['positions__entity__name'],'ideal_id':safe_int(u['positions__ideal_position_id']),'pos_id':safe_int(u['positions__id']),'level':safe_int(u['positions__ideal_position__level']),'type':u['positions__type'],'degree':u['positions__degree']} for u in users if u['id'] == user['id']]

		return paths

	def get_next_build_step_ideal(self,start_ideal_id,start_pos_id):
		positionlib = IdealPositionBase()
		from operator import itemgetter
		# get ideal position object
		ideal_pos = IdealPosition.objects.get(pk=start_ideal_id)
		# get pos object
		reg_pos = Position.objects.get(pk=start_pos_id)
		init_user = reg_pos.person
		# get paths
		paths = self.get_position_paths_from_ideal(start_ideal_id)
		# init arrays
		next = []
		finished = []
		positions = {}
		# init is_ed flag
		is_ed = False
		# init overall count 
		overall_count = 0
		# loop through each user
		for k,v in paths.iteritems():
			# loop through position for each user 
			for p in v:
				level = p['level']
				u_id = p['id']
				type = p['type']
				pos_id = p['pos_id']
				ideal_id = p['ideal_id']
				ideal_title = p['ideal_title']
				entity_id = p['entity_id']
				entity_name = p['entity_name']
				title = p['title']
				# filter out various ineligible positions
				if ideal_id is None:
					continue
				if p['level'] is not None and is_ed is True and int(p['level']) == int(ideal_pos.level):
					print "same level ed @ build"
					continue
				if p['level'] and int(p['level']) < int(ideal_pos.level):
					print "same ideal pos level @ build"
					continue
				if p['type'] == 'education' and p['degree'] is None:
					print "education with no degree @ build"
					continue
				if p['id'] in next and p['id'] not in finished and int(p['pos_id']) != int(start_pos_id):
					# increment overall count
					overall_count += 1
					# next step in the path, add to array
					if ideal_id in positions:
						# increment counter
						positions[ideal_id]['count'] += 1
						# add to positions
						positions[ideal_id]['positions'].append({'pos_id':pos_id,'ideal_id':ideal_id,'ideal_title':ideal_title,'title':title,'entity_name':entity_name,'level':level})
						# see if this company is already in the array
						if entity_id in positions[ideal_id]['orgs']:
							positions[ideal_id]['orgs'][entity_id]['count'] += 1
						else:
							# positions[ideal_id]['orgs'].append({entity_id:{'name':entity_name,'id':entity_id,'count':1}})
							positions[ideal_id]['orgs'][entity_id] = {
								'name':entity_name,
								'id':entity_id,
								'count':1
								}
					else:
						positions[ideal_id] = {
							'count':0,
							'positions':None,
							'orgs':{},
							'ideal_id':ideal_id,
							'ideal_title':ideal_title
						}
						positions[ideal_id]['count'] += 1
						positions[ideal_id]['positions'] = [{'pos_id':pos_id,'ideal_id':ideal_id,'title':title,'ideal_title':ideal_title,'entity_name':entity_name,'level':level}]
						# positions[ideal_id]['orgs'] = [{entity_id:{'name':entity_name,'id':entity_id,'count':1}}]
						
						positions[ideal_id]['orgs'][entity_id] = {
							'name':entity_name,
							'id':entity_id,
							'count':1
							}
						# add duration
						# positions[ideal_id]['duration'] = positionlib.get_avg_duration_to_position(init_user,ideal_pos)
						positions[ideal_id]['duration'] = None
						# add similar people
						positions[ideal_id]['people'] = [{'name':p.profile.full_name(),'position':p.profile.current_position(),'pic':p.profile.default_profile_pic(),'id':p.id} for p in positionlib.get_ideal_people(ideal_pos)[:3]]
						# positions[ideal_id]['people'] = None
					# add to processed positions array
					finished.append(u_id)
				if ideal_id == int(start_ideal_id):
					# print 'match'
					next.append(u_id)
				if type == "education":
					is_ed = True
				else:
					is_ed = False


		# collapse orgs list
		for k,v in positions.iteritems():
			v['orgs'] = [{'name':v1['name'],'id':v1['id'],'count':v1['count']} for k1, v1 in v['orgs'].iteritems()]
			v['orgs'] = sorted(v['orgs'],key=itemgetter('count'),reverse=True)

		positions_list = [{'ideal_title':v['ideal_title'],'ideal_id':v['ideal_id'],'prop_raw':float(v['count'])/overall_count,'prop':"{0:.0f}%".format((float(v['count'])/overall_count)*100),'count':v['count'],'positions':v['positions'],'orgs':v['orgs'],'people':v['people'],'duration':v['duration']} for k,v in positions.iteritems()]

		# sort result by count
		sorted_positions = sorted(positions_list, key=itemgetter('count'), reverse=True)
		return sorted_positions

	

	def get_next_build_step(self,ideal_id,pos_id):
		# get ideal position object
		ideal_pos = IdealPosition.objects.get(pk=ideal_id)
		# get paths
		paths = self.get_position_paths_from_ideal(ideal_id)
		# init arrays
		next = []
		finished = []
		positions = []
		# init is_ed flag
		is_ed = False
		# loop through each user
		for k,v in paths.iteritems():
			# loop through position for each user 
			for p in v:
				# filter out various ineligible positions
				if p['level'] is not None and is_ed is True and int(p['level']) == int(ideal_pos.level):
					print "same level ed @ build"
					continue
				if p['level'] and int(p['level']) < int(ideal_pos.level):
					print "same ideal pos level @ build"
					continue
				if p['type'] == 'education' and p['degree'] is None:
					print "education with no degree @ build"
					continue
				# if u['positions__type'] is not "education" and u['positions__title'] is not "Student":
					# # print u['positions__ideal_position_id']
					# print "'" + u['positions__title'] + "'"
				if p['id'] in next and p['id'] not in finished and int(p['pos_id']) != int(pos_id):
					positions.append({'pos_id':p['pos_id'],'ideal_id':p['ideal_id'],'title':p['title'],'entity_name':p['entity_name'],'level':p['level']})
					# add to processed positions array
					finished.append(p['id'])
				if p['ideal_id'] == int(ideal_id):
					# print 'match'
					next.append(p['id'])
				if p['type'] == "education":
					is_ed = True
				else:
					is_ed = False
				# set career flag
				prev_career = None
		return positions
				

class CareerMapBase():

	# set max size of ngram
	NGRAM_MAX = 10

	# set min size of ngram
	NGRAM_MIN = 1

	# initialize global dictionary for career-to-position mapping
	careers_to_positions_map = {}

	# initialize global dictionary for positions-to-ideals mapping
	positions_to_ideals_map = {}

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
		# self.init_career_to_positions_map()
		self.init_positions_to_ideals_map()
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

	def tokenize_position(self,pos,**opts):
		"""
		tokenizes position title based on spaces
		"""
		import string
		title = ''
		# check to see if education
		if hasattr(pos,'type') and pos.type == 'education':
			# concatenate title and degree / field of study
			if pos.degree:
				title = " ".join([title,pos.degree])
			if pos.field:
				title = " ".join([title,pos.field])
			# remove any "with honors" mentions
			pattern = re.compile(re.escape(" with honors"), re.IGNORECASE)
			title = pattern.sub("",title)
			# remove any forward slashes
			pattern = re.compile(re.escape("/"),re.IGNORECASE)
			title = pattern.sub(" ",title)

		else:
			title = pos.title
		if title:
			remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)
			# print remove_punctuation_map
			# remove all punctuation 
			# title = title.translate(string.maketrans("",""),string.punctuation)
			# title = " ".join([w.translate(remove_punctuation_map) for w in title])
			# tokenize position title
			tokens = title.split(" ")
			# reduce all strings to lower case
			tokens = [t.lower() for t in tokens]
			# print tokens
			tokens = [w.translate(remove_punctuation_map) for w in tokens]
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
		title_ngrams = self.extract_ngrams(self.tokenize_position(pos))
		
		# initialize careers array
		careers = []

		if title_ngrams is not None:
			for t in title_ngrams:
				if t is not None:
					# make sure position title is not in stop list, e.g., "Manager" or "Director" or something equally generic
					if t not in self.STOP_LIST:
						for k,v in self.careers_to_positions_map.items():
							if t in v and k not in careers:
								# print str(t) + ": " + str(k)
								careers.append(k)
								# print t + ": " + career.name

		return careers

	def init_positions_to_ideals_map(self):
		"""
		fill in ideal position map dictionary
		"""
		# fetch matching information for ideal positions and matching career ids
		# careers = Career.objects.values('id','pos_titles')
		ideals = IdealPosition.objects.values('id','matches').exclude(matches=None).exclude(matches='')

		# init excluded set
		excluded = [2018,2031,2039,2041,2044,2045,2054]
		# init career map dictionary
		ideal_positions_map = {}

		for i in ideals:
			if i['id'] not in excluded:
				matches = json.loads(i['matches'])
				# add career-to-position title mapping, reduced to lower case
				# if matches is not None:
				# 	titles = [t.lower() for t in titles]
				
				ideal_positions_map[i['id']] = matches

		self.positions_to_ideals_map = ideal_positions_map

	def return_ideal_from_position(self,pos):
		"""
		returns matching idealposition from position title
		"""
		# break position title into ngrams
		title_ngrams = self.extract_ngrams(self.tokenize_position(pos))
		# fetch industries for position
		industries = []
		# initialize careers array
		ideals = []
		ideals_objects = []

		# loop through ngrams to match
		if title_ngrams is not None:
			ideals = self._get_matching_ideals(title_ngrams,industries)
			
		if ideals:
			# fetch all matched ideal positions, sorted by length of title
			ideals_objects = IdealPosition.objects.filter(pk__in=ideals).extra(order_by=[len("-title")])

			return ideals_objects[0]
		return None


	def match_position_to_ideals(self,pos,test=False):
		"""
		matches positions to ideals using matching data in ideal positions
		"""
		# break position title into ngrams
		title_ngrams = self.extract_ngrams(self.tokenize_position(pos))
		# fetch industries for position
		industries = [i.id for i in pos.entity.domains.all()]
		# initialize careers array
		ideals = []
		ideals_objects = []

		# loop through ngrams to match
		if title_ngrams is not None:
			ideals = self._get_matching_ideals(title_ngrams,industries)
			
		if ideals:
			# fetch all matched ideal positions, sorted by length of title
			ideals_objects = IdealPosition.objects.filter(pk__in=ideals).extra(order_by=[len("-title")])

		if not test:
			if ideals_objects:
				pos.ideal_position = ideals_objects[0]
				pos.save()
				return True
			else:
				return False
		else:
			if ideals_objects:
				print "@ match_position_to_ideals() -- final match: " + pos.title + " (" + str(ideals_objects[0]) + ") " + str(ideals)
				return True
			else:
				print pos.title + ": no match"
				return False

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

	def _get_matching_ideals(self,title_ngrams,industries):
		ideals = []
		if title_ngrams is not None:
			for t in title_ngrams:
				# check stop list
				# if t not in self.STOP_LIST:
				for k,v in self.positions_to_ideals_map.items():
					# loop through each dict in matches
					for m in v:
						# initiate flag to test for match
						is_match = False
						# check if it's a wild match
						if 'type' in m:
							if m['type'] == 'wild':
								# check for regex match with wild token
								p = re.compile(r"\b%s\b"%m['token'],flags=re.IGNORECASE)
								match = re.search(p,t)
								# check to see if the token matches and the base string is in the title
								if m['title'] in t and match:
									is_match = True
									if 'industries' in m and industries is not None:
										if m['industries']:
											if not (set(industries) & set(m['industries'])):
												is_match = False
												continue
									# check for entity qualifiers
									if 'entities' in m:
										if pos.entity.id not in m['entities']:
											is_match = False
											continue
									if is_match == True:
										ideals.append(k)	
										print "Initial match: " + t + ": " + m['title']	
							elif m['type'] == 'education':
								# check to see if degree and / or field of study is in the string
								for tt in m['title']:
									if tt == t:
										is_match = True
								if is_match == True:
									ideals.append(k)	
						# check to see if text matches
						else:
							# print "@ _get_matching_ideals() -- not a wild match"
							if t == m['title'] and k not in ideals:
								is_match = True
								# ideals.append(k)
								# check for industry qualifiers
								if 'industries' in m and industries is not None:
									if m['industries']:
										if not (set(industries) & set(m['industries'])):
											is_match = False
											continue
								# check for entity qualifiers
								if 'entities' in m:
									if pos.entity.id not in m['entities']:
										is_match = False
										continue
								if is_match == True:
									ideals.append(k)	
									print "@ _get_matching_ideals() -- initial match: " + t + ": " + m['title']	
		return ideals

	def test_match_position_to_ideals(self,title,industries=[]):
		title_ngrams = self.extract_ngrams(self.tokenize_position(title))
		ideals = []
		ideals.extend(self._get_matching_ideals(title_ngrams,industries))

		if ideals:
			# fetch all matched ideal positions, sorted by length of title
			ideals_objects = IdealPosition.objects.filter(pk__in=ideals).extra(order_by=[len("-title")])
			return ideals_objects
		else:
			return 'no match'

	def test_match_careers_to_position(self,title=None):

		positions = Position.objects.all()

		for p in positions:
			careers = []

			if p.title:
				title_ngrams = self.extract_ngrams(self.tokenize_position(p.title))

				# print title_ngrams

				for t in title_ngrams:
					# make sure position title is not in stop list, e.g., "Manager" or "Director" or something equally generic
					# if t not in self.STOP_LIST:
					for k,v in self.careers_to_positions_map.items():
						if t in v and k not in careers:
							careers.append(k)
							career = Career.objects.get(pk=k)
							print t + ": " + career.name
			print careers

	def list_unmatched_positions(self):
		'''
		print list of all positions that are not matched to a career
		'''
		positions = Position.objects.filter(careers=None).exclude(type="education")
		for p in positions:
			if p.title:
				print p.title

class EdMapper(CareerMapBase):
	"""
	specialized class for mapping educaitonal positions, degrees, etc.
	"""

	positions_to_ideals_map = None

	def __init__(self):
		# get all ed ideal positions
		self._init_positions_to_ideals_map()

	def _init_positions_to_ideals_map(self):
		"""
		fill in ideal position map dictionary
		"""
		
		# fetch matching information for ideal positions and matching career ids
		# ideals = IdealPosition.objects.filter(cat="ed").values('id','matches').exclude(matches=None).extra(order_by=[len("-title")])
		ideals = IdealPosition.objects.filter(cat="ed").values('id','matches').exclude(matches=None)

		# init career map dictionary
		ideal_positions_map = {}

		for i in ideals:
			
			try:
				matches = json.loads(i['matches'])
			except:
				continue
			
			ideal_positions_map[i['id']] = matches

		self.positions_to_ideals_map = ideal_positions_map

	def match_degree(self,deg):
		# initialize match variables
		is_match = False
		ideals = []
		# cycle through ideal ed positions to find match
		for k,v in self.positions_to_ideals_map.items():
			# go through each match for each ideal pos
			for m in v:
				# cycle through list of possible degree names
				for d in m['title']:
					if d in deg:
						is_match = True
						ideals.append(k)
		if is_match:
			# fetch and return best match
			ip = IdealPosition.objects.get(pk=ideals[0])
			return ip
		else:
			return None



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
			for p in c.positions.all():
				try:
					ideal_pos = IdealPosition.objects.get(title=p.title)
					print "matched"
				except:
					ideal_pos = IdealPosition(title=p.title)
					print "no match"
				# save ideal position and add career association
				ideal_pos.save()
				ideal_pos.careers.add(c)
				ideal_pos.save()
				# associate ideal position with actual position
				p.ideal_position = ideal_pos
				p.save()

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

	def update_initial_careers(self,path):
		from careers.models import IdealPosition

		ideals = json.loads(open(path).read())

		for i in ideals:
			try:
				ipos = IdealPosition.objects.get(title=i['title'])
			except:
				ipos = None

			if ipos:
				for c in i['careers']:
					try:
						career = Career.objects.get(pk=c)
						ipos.careers.add(career)
						ipos.save()
						print "@ import_initial_ideals() -- added career: " + str(c)
					except ObjectDoesNotExist:
						print "@ import_initial_ideals() -- missing career: " + str(c)

	def import_initial_ideals(self,path):
		"""
		imports initial ideal positions, will do superficial checks for duplicates and add rather than overwriting
		"""
		from careers.models import IdealPosition

		ideals = json.loads(open(path).read())
		# initiate existing flag
		
		for i in ideals:
			existing = False
			# check to see if ideal position already exists
			try:
				ipos = IdealPosition.objects.get(title=i['title'])
				existing = True
				print "@ import_initial_ideals() -- existing ideal, will update"
			except MultipleObjectsReturned:
				# already multiples, flag and return later
				print "@ import_initial_ideals -- duplicate ideal position " + i['title']
				continue
			except ObjectDoesNotExist:
				# create new ideal position
				if 'description' in i:
					ipos = IdealPosition(title=i['title'],description=i['description'])
				else:
					ipos = IdealPosition(title=i['title'])
				print "@ import_initial_ideals() -- new ideal"
			
			# loop through all the listed industries
			for m in i['matches']:
				if 'industries' in m:
					if m['industries']:
						industry_ids = []
						# replace industry names with ids
						for industry in m['industries']:
							try:
								new_industry = Industry.objects.get(name=industry)
							except MultipleObjectsReturned:
								new_industry = Industry.objects.filter(name=industry)[0]
							except:
								new_industry = Industry(name=industry)
								new_industry.save()
							industry_ids.append(new_industry.id)
						m['industries'] = industry_ids
			if existing:
				old_matches = json.loads(ipos.matches)
				# print "Old matches: " + str(old_matches)
				# print "New matches: " + str(i['matches'])
				if old_matches:
					new_matches = old_matches + i['matches']
				else:
					new_matches = i['matches']
				# print "Full matches: " + str(new_matches)
				ipos.matches = json.dumps(new_matches)
				# ipos.save()
				# go to next iteration
				# continue

			else:
				ipos.matches = json.dumps(i['matches'])
			if 'level' in i:
				ipos.level = i['level']
			if 'cat' in i:
				ipos.cat = i['cat']
			if 'major' in i:
				ipos.major = i['major']
			else:
				ipos.level = 1
			ipos.save()
			for c in i['careers']:
				try:
					career = Career.objects.get(pk=c)
					ipos.careers.add(career)
				except ObjectDoesNotExist:
					print "@ import_initial_ideals() -- missing career: " + str(c)
			ipos.save()
			if existing:
				print "@ import_initial_ideals() -- updated matches " + ipos.title
			else:
				print "@ import_initial_ideals() -- added new ideal " + ipos.title

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