# from Python 
import json
from datetime import datetime, timedelta
import re
import os

# from Django
from django.contrib.auth.models import User
from careers.models import Career, Position, IdealPosition
from entities.models import Entity, Office
from django.db.models import Count, Q

def get_avg_duration_to_position(user,position):
	positionlib = PositionBase()
	return positionlib.get_avg_duration_to_position(user,position)

class NestedDict(dict):
	"""                                                                       
	Nested dictionary of arbitrary depth with autovivification.
	Allows data access via extended slice notation.                           
	"""
	def __getitem__(self, keys):
		if not isinstance(keys, basestring):
			try:
				node = self
				for key in keys:
					node = dict.__getitem__(node, key)
				return node
			except TypeError:
			# *keys* is not a list or tuple.
				pass
		try:
			return dict.__getitem__(self, keys)
		except KeyError:
			raise KeyError(keys)

	def __setitem__(self, keys, value):
		# Let's assume *keys* is a list or tuple.
		if not isinstance(keys, basestring):
			try:
				node = self
				for key in keys[:-1]:
					try:
						node = dict.__getitem__(node, key)
					except KeyError:
						node[key] = type(self)()
						node = node[key]
				return dict.__setitem__(node, keys[-1], value)
			except TypeError:
				# *keys* is not a list or tuple.
				pass
		dict.__setitem__(self, keys, value)

class PositionBase():

	def get_ed_overview(self,user,position):
		"""
		returns ed breakdown of position by school, for network and all users
		"""
		# users = self.get_users_in_career(career)
		users = User.objects.values('id','positions__type','positions__entity__name','positions__entity_id').prefetch_related('profile__connections').select_related('positions').filter(positions__ideal_position=position)
		
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

	def get_avg_duration_to_position(self,user,position):
		"""
		returns average time in reach a position
		"""

		# init general dict
		avg_duration = {}
		# get all users
		users = User.objects.values('id').filter(positions__ideal_position=position)
		
		# get list of all connections
		connections = [u['user_id'] for u in user.profile.connections.values('user_id')]
		
		# init array of durations
		network_durations = []
		all_durations = []
		
		# loop through all users, get duration
		for u in users:
			# check to see if user is in network
			if u['id'] in connections:
				duration = self._duration_to_position(u['id'],position)
				if duration is not None:
					network_durations.append(duration)
			# compile all stats
			duration = self._duration_to_position(u['id'],position)
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

	def _duration_to_position(self,user_id,position):
		
		# get all positions from user
		positions = Position.objects.values('start_date','end_date','ideal_position_id').filter(person_id=user_id).order_by('-start_date')
		
		# setup placeholder end date
		end_date = None
		
		# loop through all positions
		i = 0
		for p in positions:
			if i == 0:
				start_date = p['start_date']
			if p['ideal_position_id'] == position.id:
				end_date = p['end_date']
			i += 1

		# make sure there was at least one end_date
		if end_date is not None and start_date is not None:
			# calculate duration
			# duration = end_date - start_date
			duration = end_date - start_date
			return duration
		else:
			return None

class IdealPositionBase(PositionBase):
	

	def get_ideal_people(self,ideal_pos):
		"""
		returns top people for ideal id, based on time in position
		"""
		import operator
		users = User.objects.filter(positions__ideal_position=ideal_pos).order_by("-positions__start_date")
		return users

	def get_entities_from_ideal(self,ideal_pos,limit=5):
		"""
		returns all entities that share ideal position
		"""

		# entities = Entity.objects.filter(positions__ideal_position=ideal_pos).annotate(pop=Count("positions__id")).order_by("-pop")[:limit]
		# entities = Entity.objects.filter(positions__ideal_position=ideal_pos).prefetch_related('offices').distinct()[:limit]
		entities = Entity.objects.filter(positions__ideal_position=ideal_pos)[:limit]

		# print entities
		
		# entities_list = [{'name':e.name,'id':e.id,'descr':e.description,'no_employees':e.no_employees,'locations':[o.city for o in e.offices.all()]} for e in entities]
		entities_list = [{'name':e.name,'id':e.id,'descr':e.description,'no_employees':e.no_employees} for e in entities]

		# print entities_list

		return entities_list

	def get_ideal_paths(self,ideal_pos_id,initial=None,limit=20):
		import operator
		# init paths
		paths = {}
		# fetch ideal position object
		ideal_pos = IdealPosition.objects.get(pk=ideal_pos_id)

		users = User.objects.filter(positions__ideal_position=ideal_pos).order_by("profile__status").distinct()[:limit]

		# breakout all positions, in oder
		for u in users:
			print u.id
			paths[u.id] = [{
				'pos_title':p.title,
				'pos_id':p.id,
				'ideal_title': p.ideal_position.title if p.ideal_position else None,
				'ideal_id':p.ideal_position_id if p.ideal_position else None,
				'entities':self.get_entities_from_ideal(p.ideal_position),
				'entity':p.entity.name,
				'entity_id':p.entity.id,
				'start_date': p.start_date.year if p.start_date else None ,
				'end_date':p.end_date.year if p.end_date else None,
				'duration':(p.end_date - p.start_date).days/365.25 if p.start_date and p.end_date else None
				} for p in u.positions.all() if p is not None]
			# paths[u.id] = [{'pos_title':p.title,'pos_id':p.id,'ideal_title': p.ideal_position.title if p.ideal_position else None,'ideal_id':p.ideal_position_id if p.ideal_position else None,'entity':p.entity.name,'entity_id':p.entity.id,'start_date': p.start_date.year if p.start_date else None ,'end_date':p.end_date.year if p.end_date else None} for p in u.positions.all() if p is not None]
			paths[u.id] = sorted(paths[u.id],key=operator.itemgetter('start_date'))
		return paths		

	def get_paths_to_ideal_position(self,ideal_pos_id,initial=None,limit=5):
		# fetch ideal position object
		ideal_pos = IdealPosition.objects.get(pk=ideal_pos_id)
		if initial:
			reg_pos = Position.objects.get(pk=initial)
		# get all paths with ideal position
		users = User.objects.values('id','positions__ideal_position_id','positions__entity__name','positions__entity__id','positions__id','positions__title').filter(positions__ideal_position_id=ideal_pos_id).order_by("positions__start_date").distinct()

		# loop through and build nested dictionary
		all_paths = {}
		for user in users:
			all_paths[user['id']] = [{'id':u['id'],'title':u['positions__title'],'entity_id':u['positions__entity__id'],'entity_name':u['positions__entity__name'],'ideal_id':u['positions__ideal_position_id'],'pos_id':u['positions__id']} for u in users if u['id'] == user['id']]

		all_ideal_paths = NestedDict()

		# loop throgh each user
		i = 1
		for k,v in all_paths.items():
			# init flags
			next = []
			# init arrays for nestdict ref
			local_path = []
			local_count_path = []
			# loop over each position
			for pos in v:
				# print pos
				# print local_path
				# print all_ideal_paths

				if initial:
					
					if pos['entity_id'] is not None and int(pos['entity_id']) == int(reg_pos.entity_id):
						next.append(k)
						continue

					if k not in next:
						continue

				# finish loop if this position is or is past ideal position
				if pos['ideal_id'] == ideal_pos_id:
					continue

				if pos['entity_name'] not in all_ideal_paths[local_path]:
					all_ideal_paths[local_path][pos['entity_name']] = {'entity_name':pos['entity_name'],'title':pos['title'],'ideal_id':pos['ideal_id'],'pos_id':pos['pos_id'],'count':1,'paths':{}}
					local_path.extend([pos['entity_name'],'paths'])
					
					# local_count_path.append('count')
				else:
					# print pos
					if local_path:
						local_count_path = local_path[:-1].append('count')
					else:
						local_count_path.extend([pos['entity_name'],'count'])
					# print local_count_path

					all_ideal_paths[local_count_path] += 1
					# print all_ideal_paths[local_count_path]
			i+=1
			if i > limit:
				break

		return all_ideal_paths

	def get_users_matching_ideal_path(self,path):
		import operator
		path = set(path)
		users = User.objects.exclude(profile__status="dormant")

		user_ideal_ids = {}
		user_ideal_match = {}

		for u in users:
			user_ideal_ids[u.id] = [p.ideal_position_id for p in u.positions.all()]

		# print user_ideal_ids 
		for k,v in user_ideal_ids.iteritems():
			intersect = len(path.intersection(v))
			user_ideal_match[k] = intersect

		sorted_matches = sorted(user_ideal_match.iteritems(), key=operator.itemgetter(1))
		sorted_matches_ids = [s[0] for s in sorted_matches]
		matched_users = [{'id':u.id,'full_name':u.profile.full_name(),'pic':u.profile.default_profile_pic()} for u in User.objects.filter(id__in=sorted_matches_ids)]

		return matched_users[:5]
