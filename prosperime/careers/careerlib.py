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
from entities.models import Industry, Entity
from careers.models import Career, Position, IdealPosition
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core import management
from django.db.models import Count, Q

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

	def entry_positions_stats(self,user,career):

		# get all positions
		positions = Position.objects.values('person_id','title').filter(careers=career).order_by('start_date')

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

	def get_focal_careers(self,user,limit=5):

		careers = Career.objects.prefetch_related('positions').filter(ideal_positions__position__person=user).annotate(num=Count('positions__pk')).order_by('-num').distinct()[:limit]

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

class CareerBuild(CareerPathBase):

	def get_position_paths_from_ideal(self,ideal_id):
		# fetch all users / positions that have the ideal position in their career
		users = User.objects.values('id','positions__id','positions__type','positions__degree','positions__ideal_position_id','positions__ideal_position__level','positions__title','positions__degree','positions__entity__name','positions__entity_id','positions__type').filter(positions__ideal_position_id=ideal_id).order_by('positions__start_date').distinct()
		# init array
		paths = {}
		# collapse and sort by user
		for user in users:
			paths[user['id']] = [{'id':safe_int(u['id']),'title':u['positions__title'],'entity_id':safe_int(u['positions__entity_id']),'entity_name':u['positions__entity__name'],'ideal_id':safe_int(u['positions__ideal_position_id']),'pos_id':safe_int(u['positions__id']),'level':safe_int(u['positions__ideal_position__level']),'type':u['positions__type'],'degree':u['positions__degree']} for u in users if u['id'] == user['id']]

		return paths

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
		self.init_career_to_positions_map()
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

	def tokenize_position(self,title):
		"""
		tokenizes position title based on spaces
		"""
		import string
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
		ideals = IdealPosition.objects.values('id','matches').exclude(matches=None)

		# init career map dictionary
		ideal_positions_map = {}

		for i in ideals:
			
			matches = json.loads(i['matches'])
			# add career-to-position title mapping, reduced to lower case
			# if matches is not None:
			# 	titles = [t.lower() for t in titles]
			
			ideal_positions_map[i['id']] = matches

		self.positions_to_ideals_map = ideal_positions_map

	def match_position_to_ideals(self,pos,test=False):
		"""
		matches positions to ideals using matching data in ideal positions
		"""
		# break position title into ngrams
		title_ngrams = self.extract_ngrams(self.tokenize_position(pos.title))
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
				print "Final match: " + pos.title + " (" + str(ideals_objects[0]) + ") " + str(ideals)
			else:
				print pos.title + ": no match"

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
				if t not in self.STOP_LIST:
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
							# check to see if text matches
							else:
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
										print "Initial match: " + t + ": " + m['title']	
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
					if t not in self.STOP_LIST:
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

	def import_initial_ideals(self,path):
		from careers.models import IdealPosition
		"""
		imports initial ideal positions, will do superficial checks for duplicates and add rather than overwriting
		"""

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
				ipos = IdealPosition(title=i['title'],description=i['description'])
				print "@ import_initial_ideals() -- new ideal"
			
			# loop through all the listed industries
			for m in i['matches']:
				if 'industries' in m:
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
				print "@ import_initial_ideals() -- updating matches, skipping to next iteration"
				old_matches = json.loads(ipos.matches)
				new_matches = old_matches.extend(i['matches'])
				ipos.matches = json.dumps(new_matches)
				# go to next iteration
				continue
			else:
				ipos.matches = json.dumps(i['matches'])
			if 'level' in i:
				ipos.level = i['level']
			else:
				ipos.level = 1
			ipos.save()
			for c in i['careers']:
				career = Career.objects.get(pk=c)
				ipos.careers.add(career)
			ipos.save()
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