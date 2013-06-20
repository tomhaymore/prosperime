# from Python
import bs4
import urllib2
import json
import re
import sys
from operator import itemgetter

# from Django
from django.db.models import Q

# from prospr
from utilities.helpers import _get_json 
from careers.models import Career, Position, IdealPosition
from entities.models import Entity


class ParseBase():

	# init lists for matching
	ENTITIES_LIST = []
	POSITIONS_LIST = []
	POSITION_DICT = {}

	# set max size of ngram
	NGRAM_MAX = 10

	# set min size of ngram
	NGRAM_MIN = 1

	# init list for all missed positions
	MISSSED_POSITIONS = []

	# init alpha list
	abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

	# init degrees list
	DEGREES = [
		'BA',
		'BS',
		'AB',
		'MA',
		'LLM',
		'LLD',
		'Bachelor of Science',
		'MJS',
		'MPH',
		'M.Litt',
		'MPP',
		'EdD',
		'Doctorate in Geology',
		'prelaw',
		'Bachelor of Law',
		'doctoral degree',
		'JD',
		'Juris Doctor',
		'MBA',
		'MCP',
		'MD',
		'Master of Divinity',
		'PhD',
		'DBA',
		'BSc',
		'BArch',
		'SB',
		'ScB',
		'BAAS',
		'BEng',
		'BE',
		'BSE',
		'BESc',
		'BSEng',
		'BASc',
		'BTech',
		'BSEE',
		'BBA',
		'BAcy',
		'BAcc',
		'DDS',
		'BN',
		'BNSc',
		'BSN',
		'DVM',
		'PharmD',
		'BVSc',
		'BVMS',
		'BFA',
		'MFA',
		'LLB',
		'MEd',
		'Master of Architecture',
		'Bachelor of Engineering',
		'MS Ed',
		'Bachelor of Arts',
		'Juris Doctorate',
		'MS',
		'AA',
		'Associate of Arts',
		'Doctor of Philosophy',
		'MPS',
		'MSEE',
		'MPA',
		'Fulbright Scholarship',
		'graduate work',
		'attended',
		'studied'
	]

	DEGREES = [d.lower() for d in DEGREES]

	DEGREES.sort(key=len,reverse=True)

	def _init_entity_list(self):
		self.ENTITIES_LIST = [{'name':self._standardize_names(e.name),'id':e.id} for e in Entity.objects.all()]

	def _init_position_list(self):
		all_positions = set([p.title for p in Position.objects.exclude(Q(title=None) | Q(title=""))])
		pos_list = [self._standardize_names(p) for p in all_positions]
		pos_dict = {}
		for p in all_positions:
			pos_dict[self._standardize_names(p)] = p
		# pos_list = [{'string':p.title,'match':self._standardize_names(p.title)} for p in Position.objects.exclude(Q(title=None) | Q(title=""))]
		all_ideals = [p.title for p in IdealPosition.objects.exclude(title=None)]
		ideal_pos_list = [self._standardize_names(p.title) for p in IdealPosition.objects.exclude(title=None)]
		for p in ideal_pos_list:
			norm_title = self._standardize_names(p)
			if norm_title not in pos_dict:
				pos_dict[norm_title] = p
		full_list = pos_list + ideal_pos_list
		self.POSITIONS_LIST = list(set(full_list))
		self.POSITION_DICT = pos_dict

	def get_json(self,url):
		print "fetching..." + str(url)
		return _get_json(url)

	def get_html(self,url):
		print "fetching..." + str(url)
		try:
			html = urllib2.urlopen(url).read()
			return html
		except urllib2.URLError, e:
			print str(e)
			return None
		except:
			return None

	def get_soup(self,url):
		html = self.get_html(url)
		soup = bs4.BeautifulSoup(html)
		# print soup
		return soup

	def _standardize_names(self,data):
		"""
		standardizes entity / position names like tokens
		"""
		import string
		if data:
			# init punctuation map
			remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)
			
			# reduce all strings to lower case and strip any leading / trailing whitespace
			data = data.lower()
			data = data.strip()
			
			# remove punctuation
			data = data.translate(remove_punctuation_map)
			return data

		return None

	def _match_entity(self,ngrams):
		matched_ents = [{'name':len(e['name']),'id':e['id']} for e in self.ENTITIES_LIST if e['name'] in ngrams]
		if matched_ents:
			sorted_matched_ents = sorted(matched_ents,key=itemgetter('name'),reverse=True)
			entity = Entity.objects.get(pk=sorted_matched_ents[0]['id'])
			return entity
		return None

	def _match_position(self,ngrams):
		matched_pos = [p for p in self.POSITIONS_LIST if p in ngrams]
		# if anything matched, sort by length of string
		if matched_pos:
			sorted_matched_pos = sorted(matched_pos,key=len,reverse=True)
			title = self.POSITION_DICT[sorted_matched_pos[0]]
			return title
		return None

	def _match_degree(self,ngrams):
		matched_degrees = [d for d in self.DEGREES if d in ngrams]
		if matched_degrees:
			degree = matched_degrees[0].upper()
			return degree
		return None

	def _extract_dates(self,pos):
		# set defaults
		start_date = None
		end_date = None
		splits = pos.split('.')
		for s in splits:
			if 'commission' in s:
				# it's a start date
				# dates = re.findall("((January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2}\,\s\d{4})",pos)
				# start_date = datetime.strftime(dates[2][0],"%B %d, %Y")
				date = re.search("((January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2}\,\s\d{4})",s)
				start_date = datetime.strftime(date.group(0),"%B %d, %Y")
			elif 'terminated' i s:
				# it's an end date
				date = re.search("((January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2}\,\s\d{4})",s)
				end_date = datetime.strftime(date.group(0),"%B %d, %Y")
		return start_date, end_date

	def _tokenize(self,data):
		"""
		tokenizes position title based on spaces
		"""
		import string
		if data:
			# init punctuation map
			remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)
			
			# tokenize
			tokens = data.split(" ")

			# reduce all strings to lower case and strip any leading / trailing whitespace
			tokens = [t.lower() for t in tokens]
			tokens = [t.strip() for t in tokens]
			
			# remove punctuation
			tokens = [w.translate(remove_punctuation_map) for w in tokens]

			return tokens
		return None

	def _extract_ngrams(self,tokens):
		"""
		assembles tokens into appropriate number of ngrams and returns as a list
		"""
		if tokens:
			ngrams = []
			n_tokens = len(tokens)
			for i in range(n_tokens):
				for j in range(i+1,min(n_tokens,self.NGRAM_MAX)+1):
					ngram = " ".join(tokens[i:j])
					ngrams.append(ngram)

			return ngrams
		return None

	def _log_missed_positions(self):
		import datetime
		filename = "parselib_missed_positions_" + str(datetime.datetime.now()).replace(" ","_") + ".json"
		f = open(filename,'w')
		f.write(json.dumps(self.MISSSED_POSITIONS))
		f.close()

class ParseBG(ParseBase):

	# global variables

	ALL_POS_COUNT = 0

	MATCHED_POS_COUNT = 0

	ENTITIES_LIST = []

	POSITIONS_LIST = []

	POSITION_DICT = {}

	MISSSED_POSITIONS = []

	HIT_POSITIONS = []

	DEGREES = [
		'BA',
		'BS',
		'AB',
		'MA',
		'LLM',
		'LLD',
		'Bachelor of Science',
		'MJS',
		'MPH',
		'M.Litt',
		'MPP',
		'EdD',
		'Doctorate in Geology',
		'prelaw',
		'Bachelor of Law',
		'doctoral degree',
		'JD',
		'Juris Doctor',
		'MBA',
		'MCP',
		'MD',
		'Master of Divinity',
		'PhD',
		'DBA',
		'BSc',
		'BArch',
		'SB',
		'ScB',
		'BAAS',
		'BEng',
		'BE',
		'BSE',
		'BESc',
		'BSEng',
		'BASc',
		'BTech',
		'BSEE',
		'BBA',
		'BAcy',
		'BAcc',
		'DDS',
		'BN',
		'BNSc',
		'BSN',
		'DVM',
		'PharmD',
		'BVSc',
		'BVMS',
		'BFA',
		'MFA',
		'LLB',
		'MEd',
		'Master of Architecture',
		'Bachelor of Engineering',
		'MS Ed',
		'Bachelor of Arts',
		'Juris Doctorate',
		'MS',
		'AA',
		'Associate of Arts',
		'Doctor of Philosophy',
		'MPS',
		'MSEE',
		'MPA',
		'Fulbright Scholarship',
		'graduate work',
		'attended',
		'studied'
	]

	DEGREES.sort(key=len)

	DEGREES = [d.lower() for d in DEGREES]

	# DEGREES_REGEX = [{'string':d,'regex':re.compile(d.lower())} for d in DEGREES]

	DEGREES.sort(key=len,reverse=True)

	BASE_URL = "http://bioguide.congress.gov/scripts/biodisplay.pl?index="

	DOB_BOUNDARY = 1920

	soup = bs4.BeautifulSoup

	SENATE = None

	HOUSE = None

	# variables for each person

	ORIG_POS = {}

	PERSON = None

	NGRAMS = None

	TYPE = None

	def __init__(self):
		# initialize lists
		self._init_entity_list()
		self._init_position_list()
		# initialize Senate and House objects
		self.SENATE = Entity.objects.get(name="U.S. Senate")
		self.HOUSE = Entity.objects.get(name="U.S. House of Representatives")

	def _init_entity_list(self):
		self.ENTITIES_LIST = [{'name':self._standardize_names(e.name),'id':e.id} for e in Entity.objects.all()]

	def _init_position_list(self):
		all_positions = set([p.title for p in Position.objects.exclude(Q(title=None) | Q(title=""))])
		pos_list = [self._standardize_names(p) for p in all_positions]
		pos_dict = {}
		for p in all_positions:
			pos_dict[self._standardize_names(p)] = p
		# pos_list = [{'string':p.title,'match':self._standardize_names(p.title)} for p in Position.objects.exclude(Q(title=None) | Q(title=""))]
		all_ideals = [p.title for p in IdealPosition.objects.exclude(title=None)]
		ideal_pos_list = [self._standardize_names(p.title) for p in IdealPosition.objects.exclude(title=None)]
		for p in ideal_pos_list:
			norm_title = self._standardize_names(p)
			if norm_title not in pos_dict:
				pos_dict[norm_title] = p
		full_list = pos_list + ideal_pos_list
		self.POSITIONS_LIST = list(set(full_list))
		self.POSITION_DICT = pos_dict

	def _full_url(self,stub):
		return self.BASE_URL+stub

	def _reset_orig_values(self):
		self.ORIG_PERSON = None
		self.PERSON = None
		self.NGRAMS = None
		self.TYPE = None

	def end_of_letter(self,soup):
		"""
		check whether empty record is returned, indicating end of this index
		"""
		text = soup.get_text()
		m = re.search('does not exist',text)
		if m:
			return True
		return False

	def is_past(self,soup):
		"""
		fetchs dob and compares to set boundary
		"""
		text = soup.find_all('table')[1].table.td.find_all('font')[1].get_text()
		m = re.search('[0-9]+(?:\.[0-9]*)?',text)
		if m:
			dob = int(m.group(0))
			if dob < self.DOB_BOUNDARY:
				print "@ parselib -- too old, skipping"
				return True
		return False

	def add_ed(self,pos,person):
		# init array for saving to model
		params = {
			'type':'education',
			'person':person,
			'entity':None,
			'degree':'Unknown',
			'start_date':None,
			'end_date':None
		}
		# get ngrams from text
		# ngrams = self._extract_ngrams(self._tokenize(pos))
		ngrams = self.NGRAMS
		degree = None
		matched_degrees = [d for d in self.DEGREES if d in ngrams]
		if matched_degrees:
			degree = matched_degrees[0].upper()
		# for reg in self.DEGREES_REGEX:
		# 	if re.search(reg['regex'],pos):
		# 		# print "@ parselib -- matching reg " + reg['string']
		# 		degree = reg['string']
		if degree:
			params['degree'] = degree
			# print "@ parselib -- matching reg " + params['degree']
		else:
			# print "@ parselib -- no matching degrees"
			pass
		date = re.findall("[0-9]+(?:\.[0-9]*)?",pos)
		# try to get start and end dates
		if len(date) == 1:
			params['end_date'] = date[0]
		elif len(date) == 2:
			params['start_date'] = date[0]
			params['end_date'] = date[1]
		
		# print ngrams
		matched_ents = [{'name':len(e['name']),'id':e['id']} for e in self.ENTITIES_LIST if e['name'] in ngrams]
		if matched_ents:
			sorted_matched_ents = sorted(matched_ents,key=itemgetter('name'),reverse=True)
			params['entity'] = Entity.objects.get(pk=sorted_matched_ents[0]['id'])
		# for e in self.ENTITIES_LIST:
			
		# 	if e['name'] in ngrams:
		# 		params['entity'] = Entity.objects.get(pk=e['id'])
		if params['entity'] is not None:
			# print 'match'
			# print "@ parselib -- degree " + params['degree']
			self.MATCHED_POS_COUNT += 1
			if params['degree'] == "Unknown":
				print pos
			print "@ parselib -- entity id: " + str(params['entity'].id)
			print "@ parselib -- added education: " + params['degree'] + " from " + str(params['entity'])  + ", " + str(params['start_date']) + " - " + str(params['end_date'])
			# position = Position(params)
			# position.save()
		else:
			# print 'no match'
			pass

	def _is_ed_degree(self,pos):
		if 'graduated' in pos or 'attended' in pos or 'graduate' in pos:
			return True
		# get ngrams from text
		self.NGRAMS = self._extract_ngrams(self._tokenize(pos))
		ngrams = self.NGRAMS
		matched_degrees = [d for d in self.DEGREES if d in ngrams]
		if matched_degrees:
			return True
		# if any(reg['regex'].search(pos) for reg in self.DEGREES_REGEX):
		# 	return True

	def add_pos(self,pos,person):
		# init array for saving to model
		
		params = {
			'type':'professional',
			'person':person,
			'title':'Unknown',
			'entity':None,
			'start_date':None,
			'end_date':None
		}
		date = re.findall("[0-9]+(?:\.[0-9]*)?",pos)
		# try to get start and end dates
		if len(date) == 1:
			params['end_date'] = date[0]
		elif len(date) == 2:
			params['start_date'] = date[0]
			params['end_date'] = date[1]
		# get ngrams from text
		# ngrams = self._extract_ngrams(self._tokenize(pos))
		ngrams = self.NGRAMS
		# check for military careers
		if "served in" in ngrams and "navy" in ngrams:
			params['title'] = "Military"
		if "enlisted in" in ngrams:
			params['title'] = "Military"
		# check for position name
		matched_pos = [p for p in self.POSITIONS_LIST if p in ngrams]
		# if anything matched, sort by length of string
		if matched_pos:
			sorted_matched_pos = sorted(matched_pos,key=len,reverse=True)
			params['title'] = self.POSITION_DICT[sorted_matched_pos[0]]
		matched_ents = [{'name':len(e['name']),'id':e['id']} for e in self.ENTITIES_LIST if e['name'] in ngrams]
		if matched_ents:
			sorted_matched_ents = sorted(matched_ents,key=itemgetter('name'),reverse=True)
			params['entity'] = Entity.objects.get(pk=sorted_matched_ents[0]['id'])
		# for p in self.POSITIONS_LIST:
		# 	if p in ngrams:
		# 		params['title'] = p
		# for e in self.ENTITIES_LIST:
		# 	if e['name'] in ngrams:
		# 		params['entity'] = Entity.objects.get(pk=e['id'])
		if params['entity'] is not None:
			# ensure different from original position
			if self._is_orig_pos(params):
				return None
			self.MATCHED_POS_COUNT += 1
			if params['title'] == 'Unknown':
				self.MISSSED_POSITIONS.append(pos)
			else:
				self.HIT_POSITIONS.append(params['title'])
			print "@ parselib -- entity id: " + str(params['entity'].id)
			print "@ parselib -- added position: " + params['title'] + " at " + str(params['entity']) + ", " + str(params['start_date']) + " - " + str(params['end_date'])
			# position = Position(params)
			# position.save()

	def _is_orig_pos(self,params):
		if params['entity'] == self.ORIG_POS['entity']:
			if params['start_date'] == self.ORIG_POS['start_date'] and params['end_date'] == self.ORIG_POS['end_date']:
				return True
		else:
			return False


	def _is_irrel(self,data):
		"""
		tests for irrelevant data, e.g., "Born in ..." "Died on ..."
		"""
		triggers = [
			"born",
			"died",
			"interment"
		]
		found_triggers = [t for t in triggers if t in data]
		if found_triggers:
			return True
		return False

	def parse_positions(self,soup,person):
		# get text of biography
		text = soup.find_all('table')[1].p.get_text()
		# clean up text and split into array
		positions = text.replace('\r','').replace('\n','').split('; ')
		for p in positions:
			p = p.strip()
		# loop through positions
		for p in positions:
			# test for irrelevant entry
			if self._is_irrel(p):
				continue
			# increment counter
			self.ALL_POS_COUNT += 1
			if self._is_ed_degree(p.replace('.','')):
				self.add_ed(p.replace('.',''),person)
			else:
				self.add_pos(p,person)

	def add_person(self,soup):
		# init dict
		params = {}
		names = soup.find_all('table')[1].table.a.get_text().split(',')
		first_name = names[1].title()
		last_name = names[0].strip().title()
		username = first_name + last_name + "_bioguide"
		# add person
		person = ''
		# person = User(username=username[:30],first_name=first_name,last_name=last_name)
		# personn.save()
		# # add profile
		# person.profile.first_name = first_name
		# person.profile.last_name = last_name
		# person.profile.status = "bioguide"
		# person.profile.save()
		print "@ parselib -- added " + first_name + " " + last_name
		# check for Senate or House
		params = {}
		text = soup.find_all('table')[1].find_all('td')[1].get_text()
		m = re.search('(?<=:\s)(\d+)-(\d+)',text)
		if m:
			# it's a senate position
			self.TYPE = 'sen'
			params = {
				'entity': self.SENATE,
				'title': "U.S. Senator",
				'start_date': int(m.group(1)),
				'end_date': None
			}
			try:
				params['end_date'] = int(m.group(2))
			except:
				params['end_date'] = None
		else:
			# it's a house position
			self.TYPE = 'house'
			params = {
				'entity': self.HOUSE,
				'title': "U.S. Representative",
				'start_date': None,
				'end_date': None
			}
			
			try:
				m1 = re.search('(?<=\().+(\d+)',text)
				m2 = re.findall('([\d]{4})',m.group(0))
			except:
				m1 = None
				m2 = None
			if m2:
				if len(m2) == 1:
					params['start_date'] = int(m2[0])
					params['end_date'] = None
				elif len(m2) == 2:
					params['start_date'] = int(m2[0])
					params['end_date'] = int(m2[1])
				else:
					params['start_date'] = None
					params['end_date'] = None
		# set original position
		self.ORIG_POS = {
			'entity': params['entity'],
			'start_date': params['start_date'],
			'end_date': params['end_date']
		}
		# add position
		# position = Position(params)
		# position.save()
		print "@ parselib -- added position at " + params['entity'].name
		self.PERSON = person
		return person

	def parse_person(self,index):
		# reset all values
		self._reset_orig_values()
		# fetch page
		soup = self.get_soup(self._full_url(index))
		# check to see if end of letter
		if self.end_of_letter(soup):
			return None, "end"
		# check timeframe
		if self.is_past(soup):
			return None, "old"
		# parse data into person
		person = self.add_person(soup)
		self.parse_positions(soup,person)
		return "Success",None

	def parse_people(self):
		full = "000000"
		for a in self.abc:
			# reset counter
			i = 1
			stop = False
			while not stop:
				# compile record number
				index = a + full[:-len(str(i))] + str(i)
				# retrieve and store person details
				res, status = self.parse_person(index)
				# check to see if reached end of letter
				if status == "end":
					stop = True
				# increment i
				i += 1
		# print all missed positions
		self._log_missed_positions()

class ParseFJC(ParseBase):

	# init global variables

	NGRAMS = []

	def parse_positions(self,soup,person):
		data = str(soup.find_all('table')[2].dd)
		splits = data_bio.split('\n')
		for s in splits:
			# check for empty splits
			if s is not '':
				self.NGRAMS = self._extract_ngrams(self._tokenize(pos))
				entity = self._match_entity(self.NGRAMS)
				title = self._match_position(self.NGRAMS)
				degree = self._match_degree(self.NGRAMS)
				datas = self._extract_dates(self.NGRAMS)
				if entity:
					params = {
						'entity':entity,
						'title':title
					}
					if degree:
						params['type'] = 'education'
						params['degree'] = degree
					self.add_position(params)

	def add_person(self,soup):
		# init dictionary for profile data
		# params = dict()
		data = soup.find_all('table')[2]
		raw_names = " ".split(data.font.get_text())
		if len(raw_names) > 1:
			first_name = raw_names[1]
			last_name = raw_names[0]
		username = "%s%s_%s" % (first_name,last_name,'fjc')
		person = ''
		# person = User(username=username[:30],first_name=first_name,last_name=last_name)
		# personn.save()
		# # add profile
		# person.profile.first_name = first_name
		# person.profile.last_name = last_name
		# person.profile.status = "bioguide"
		# person.profile.save()
		print "@ parselib -- added " + first_name + " " + last_name
		return person
	


	def parse_person(self,url):
		# get data
		soup = self.get_soup(url)
		# check for empty page
		if self._is_end(soup):
			return None, "False"
		# parse data into person
		person = self.add_person(soup)
		self.parse_positions(soup,person)
		return "Success",None

	def parse_people(self):
		# init base url
		base_search_url = "http://www.fjc.gov/servlet/nAsearch?lname="
		base_url = "http://www.fjc.gov/servlet/nGetInfo?jid="
		# cycle through search results
		i = 1
		stop_first = False
		stop = False
		while not stop:
			# compile full url
			full_url = "http://www.fjc.gov/servlet/nGetInfo?jid=%d" % (i,)
			# retrieve and store person details
			res, status = self.parse_person(full_url)
			# check to see if res was false twice in a row
			if status = "false" and not stop_first:
				stop_first = True
			elif status = "false" and stop_first:
				stop = True
