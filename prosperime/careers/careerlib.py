# from Python
import json
import urllib2
from datetime import datetime
import csv
import re
import os
import types


# from Django
from entities.models import Industry, User, Entity
from careers.models import Career, Position, IdealPosition
from django.core.exceptions import MultipleObjectsReturned
from django.core import management
from django.db.models import Count, Q

# get focal careers
def get_focal_careers(user,limit=10):
	career_sim = CareerSimBase()
	careers = career_sim.get_focal_careers(user,limit)
	return careers

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

	return (users_list, user_ids)

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
	global STOP_LIST
	title_ngrams = _extract_ngrams(_tokenize_position(pos.title))

	careers = []

	if title_ngrams is not None:
		for t in title_ngrams:
			if t is not None:
				# make sure position title is not in stop list, e.g., "Manager" or "Director" or something equally generic
				if t not in STOP_LIST:
					for k,v in careers_to_positions_map.items():
						if t in v and k not in careers:
							# print 'hello'
							careers.append(k)
							# print t + ": " + career.name

	return careers

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

class CareerSimBase():

	# fetch all users
	# users = User.objects.prefetch_related('positions').exclude(profile__status="deleted")
	users = {}

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

	def find_similar_careers(self,id):
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

	def get_paths_in_career(self,user,career):
		# initialize overview array
		overview = {}
		paths = {}

		# get users in network
		users_list, user_ids = _get_users_in_network(user)

		network_people = User.objects.prefetch_related().select_related('positions','entities','accounts').filter(id__in=user_ids,positions__careers=career).annotate(no_of_pos=Count('positions__pk')).order_by('-no_of_pos').distinct()
		# CAUTION--values() can return multiple records when requesting M2M values; make sure to reduce
		# network_people = User.objects.values('id','profile__headline','profile__first_name','profile__last_name','profile__pictures__pic','positions__entity__id','positions__entity__name').annotate(no_of_pos=Count('positions__id')).order_by('-no_of_pos')

		# Clayton -- need to uniqify this list, b/c lots of wasted time
		#	parsing duplicate people ... EDIT: not the problem, problem is
		#	duplicate positions!
		# network_people = _order_preserving_uniquify(network_people)

		network_people_dict = {}
		num_pos = 0
		# entities = []
		entities = set()
		entities_dict = {}
		num_cos = 0
		network_positions = []
		counter = 0

		## Network
		for p in network_people:
			# num_pos += len(p.positions.all())
			people_seen = set()
			positions_seen = set()

			for pos in p.positions.all():
				num_pos += 1
				# entities.append(pos.entity.id)
				entities.add(pos.entity.id)

				# if pos in career, add to positions
				# 	additionally, impose 30 position cap
				
				if career in pos.careers.all():
					counter += 1
					print counter
				 	if len(network_positions) < 30:
						# check if seen already (avoid duplicates)
						if pos.id not in positions_seen:
							positions_seen.add(pos.id)
							network_positions.append({
								'id':pos.id,
								'title':pos.title,
								'co_name':pos.entity.name,
								'owner':pos.person.profile.full_name(),
								'owner_id':pos.person.id,
								'logo_path':pos.entity.default_logo(),
							})

			
				if pos.entity.name in entities_dict:
					entities_dict[pos.entity.name]['count'] += 1

					# check if person seen already (avoid duplicates)
					# 	additionally, cap people @ 5 for now
					if p.id not in people_seen and len(entities_dict[pos.entity.name]['people']) < 6:
						
						person_dict = {
							'name':p.profile.full_name(),
							'id':p.id,
						}
						entities_dict[pos.entity.name]['people'].append(person_dict)
						people_seen.add(p.id)

				else:
					people_list = [{
						'name':p.profile.full_name(),
						'id':p.id,
					}]
					
					entities_dict[pos.entity.name] = {
						'count' : 1,
						'id':pos.entity.id,
						'logo':pos.entity.default_logo(),
						'people':people_list,	
					}

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


		# num_cos = len(set(entities))
		num_cos = len(entities)

		overview['network'] = {
			'num_people':len(network_people),
			'num_pos':num_pos,
			'num_cos':num_cos
		}

		all_people = User.objects.select_related('positions').filter(positions__careers=career).annotate(no_of_pos=Count('positions__pk')).order_by('-no_of_pos').distinct()

		num_pos = 0
		#entities = []
		entities = set()
		all_entities_dict = {}
		all_positions = []
		num_cos = 0

		## ALL
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
				# entities.append(pos.entity.id)
				entities.add(pos.entity.id)

		#num_cos = len(set(entities))
		num_cos = len(entities)

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
		paths['networkOrgs'] = entities_dict
		paths['allOrgs'] = all_entities_dict

		# TRIAL - adding positions information
		paths['networkPositions'] = network_positions
		paths['allPositions'] = all_positions

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

	def get_careers_brief_similar(self,user,**filters):

		user_id = user.id

		users = self.find_similar_careers(user_id)
		
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
	STOP_LIST = []

	def __init__(self):
		# fill in career to positions map
		self.init_career_to_positions_map()
		self.load_stop_list()

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
		careers = Career.objects.values('id','pos_titles')

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
		title_ngrams = self.extract_ngrams(self.tokenize_position(pos.title))
	
		careers = []

		if title_ngrams is not None:
			for t in title_ngrams:
				if t is not None:
					# make sure position title is not in stop list, e.g., "Manager" or "Director" or something equally generic
					if t not in self.STOP_LIST:
						for k,v in self.careers_to_positions_map.items():
							if t in v and k not in careers:
								print 'hello'
								careers.append(k)
								# print t + ": " + career.name

		for c_id in careers:
			c = Career.objects.get(pk=c_id)
			pos.careers.add(c)
		pos.save()

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


init_careers_to_positions_map()
# _load_stop_list()
