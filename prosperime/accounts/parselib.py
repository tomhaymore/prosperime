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

	# set max size of ngram
	NGRAM_MAX = 10

	# set min size of ngram
	NGRAM_MIN = 1

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

class ParseBG(ParseBase):

	ALL_POS_COUNT = 0

	MATCHED_POS_COUNT = 0

	ENTITIES_LIST = []

	POSITIONS_LIST = []

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
		'Juris Doctor'
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

	abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

	SENATE = Entity.objects.get(name="U.S. Senate")

	HOUSE = Entity.objects.get(name="U.S. House of Representatives")

	def __init__(self):
		self._init_entity_list()
		self._init_position_list()

	def _init_entity_list(self):
		self.ENTITIES_LIST = [{'name':self._standardize_names(e.name),'id':e.id} for e in Entity.objects.all()]

	def _init_position_list(self):
		pos_list = [self._standardize_names(p.title) for p in Position.objects.exclude(Q(title=None) | Q(title=""))]
		ideal_pos_list = [self._standardize_names(p.title) for p in IdealPosition.objects.exclude(title=None)]
		full_list = pos_list + ideal_pos_list
		self.POSITIONS_LIST = list(set(full_list))

	def _full_url(self,stub):
		return self.BASE_URL+stub

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
		ngrams = self._extract_ngrams(self._tokenize(pos))
		degree = None
		matched_degrees = [d for d in self.DEGREES if d in ngrams]
		if matched_degrees:
			degree = matched_degrees[0]
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

	def is_ed_degree(self,pos):
		if 'graduated' in pos or 'attended' in pos or 'graduate' in pos:
			return True
		# get ngrams from text
		ngrams = self._extract_ngrams(self._tokenize(pos))
		matched_degrees = [d for d in self.DEGREES if d in ngrams]
		if matched_degrees:
			return True
		# if any(reg['regex'].search(pos) for reg in self.DEGREES_REGEX):
		# 	return True

	def add_pos(self,pos,person):
		# init array for saving to model
		
		params = {
			'type':'education',
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
		ngrams = self._extract_ngrams(self._tokenize(pos))
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
			params['title'] = sorted_matched_pos[0]
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
			self.MATCHED_POS_COUNT += 1
			if params['title'] == 'Unknown':
				self.MISSSED_POSITIONS.append(pos)
			else:
				self.HIT_POSITIONS.append(params['title'])
			print "@ parselib -- entity id: " + str(params['entity'].id)
			print "@ parselib -- added position: " + params['title'] + " at " + str(params['entity']) + ", " + str(params['start_date']) + " - " + str(params['end_date'])
			# position = Position(params)
			# position.save()

	def is_irrel(self,data):
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
			if self.is_irrel(p):
				continue
			# increment counter
			self.ALL_POS_COUNT += 1
			if self.is_ed_degree(p.replace('.','')):
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
			params['entity'] = self.SENATE
			params['title'] = "U.S. Senator"
			params['start_date'] = int(m.group(1))
			try:
				params['end_date'] = int(m.group(2))
			except:
				params['end_date'] = None
		else:
			# it's a house position
			params['entity'] = self.HOUSE
			params['title'] = "U.S. Representative"
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
		# add position
		# position = Position(params)
		# position.save()
		print "@ parselib -- added position at " + params['entity'].name
		return person

	def parse_person(self,index):
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

	def _log_missed_positions(self):
		import datetime
		filename = "parselib_missed_positions_" + str(datetime.datetime.now()).replace(" ","_")
		f = open(filename,'w')
		f.write(json.dumps(self.MISSSED_POSITIONS))
		f.close()

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
