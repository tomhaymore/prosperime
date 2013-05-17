# from Python
import bs4
import urllib2
import json
import re
import sys

# from Django

# from prospr
from utilities.helpers import _get_json 
from careers.models import Career, Position
from entities.models import Entity


class ParseBase():

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

class ParseBG(ParseBase):

	ENTITIES_LIST = []

	POSITIONS_LIST = []

	DEGREES = [
		'BA',
		'BS',
		'AB',
		'LLM',
		'JD',
		'MBA',
		'MD',
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
		'MPA'
	]

	DEGREES_REGEX = [{'string':d,'regex':re.compile(d)} for d in DEGREES]

	BASE_URL = "http://bioguide.congress.gov/scripts/biodisplay.pl?index="

	DOB_BOUNDARY = 1930

	soup = bs4.BeautifulSoup

	abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

	def __init__(self):
		self._init_entity_list()
		self._init_position_list()

	def _init_entity_list(self):
		self.ENTITIES_LIST = [{'name':e.name,'id':e.id} for e in Entity.objects.all()]

	def _init_position_list(self):
		self.POSITIONS_LIST = [p.title for p in Position.objects.exclude(title=None)]

	def full_url(self,stub):
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
		dob = int(m.group(0))
		if dob < self.DOB_BOUNDARY:
			print "@ parselib -- too old, skipping"
			return True
		return False

	def add_ed(self,pos,person):
		# init array for saving to model
		params = {
			'type':'education',
			'person':person
		}
		for reg in self.DEGREES_REGEX:
			if re.search(reg['regex'],pos):
				degree = reg['string']
		date = re.findall("[0-9]+(?:\.[0-9]*)?",pos)
		# try to get start and end dates
		if len(date) == 1:
			params['end_date'] = date[0]
		elif len(date) == 2:
			params['start_date'] = date[0]
			params['end_date'] = date[1]
		for e in self.ENTITIES_LIST:
			if e['name'] in pos.lower():
				params['entity'] = Entity.objects.get(pk=e['id'])
		if params['entity'] is not None:
			print "@ parselib -- added education " + str(params['entity'].name)
			# position = Position(params)
			# position.save()


	def is_ed_degree(self,pos):
		if any(reg['regex'].search(pos) for reg in self.DEGREES_REGEX):
			return True

	def add_pos(self,pos,person):
		# init array for saving to model
		
		params = {
			'type':'education',
			'person':person,
			'title':'Unknown',
			'entity':None
		}
		date = re.findall("[0-9]+(?:\.[0-9]*)?",pos)
		# try to get start and end dates
		if len(date) == 1:
			params['end_date'] = date[0]
		elif len(date) == 2:
			params['start_date'] = date[0]
			params['end_date'] = date[1]

		for p in self.POSITIONS_LIST:
			if p in pos.lower():
				params['title'] = p
		for e in self.ENTITIES_LIST:
			if e['name'] in pos.lower():
				params['entity'] = Entity.objects.get(pk=e['id'])
		if params['entity'] is not None:
			print "@ parselib -- added position at " + str(params['entity'].name)
			# position = Position(params)
			# position.save()

	def parse_positions(self,soup,person):
		# get text of biography
		text = soup.find_all('table')[1].p.get_text()
		# clean up text and split into array
		positions = text.replace('\r','').replace('\n','').split(';')
		for p in positions:
			p = p.strip()
		# loop through positions
		for p in positions:
			if 'graduated' in p or self.is_ed_degree(p.replace('.','')):
				self.add_ed(p,person)
			else:
				self.add_pos(p,person)

	def add_person(self,soup):
		# init dict
		params = {}
		names = soup.find_all('table')[1].table.a.get_text().split(',')
		first_name = names[1].title()
		last_name = names[0].strip()
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
		return person

	def parse_person(self,index):
		# fetch page
		soup = self.get_soup(self.full_url(index))
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
