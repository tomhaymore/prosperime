# Python imports
import os
import urllib
import urllib2
import json
import sys
from urlparse import urlparse
from datetime import datetime
from utilities.helpers import retry
from optparse import make_option

# Django imports
from django.contrib.auth.models import User
from django.core.files import File
from django.db.models import Q

# ProsperMe imports
from entities.models import Entity, Image, Financing, Office, Investment
from careers.models import Position
from accounts.models import Picture, Account

class CBBase():
		
	CB_KEY = "jwyw2d2vx63k3z6336yzpd4h"

	CB_BASE_URL = "http://api.crunchbase.com/v/1/"
	
	CURRENT_ENTITIES = []
	
	ENTITY_TYPES = (
		{'single':'company','plural':'companies'},
		{'single':'person','plural':'people'},
		{'single':'financial-organization','plural':'financial-organizations'},
		{'single':'service-provider','plural':'service-providers'}
	)
	
	ENTITY_TYPES_DICT = {
		"company":"companies",
		"person":"people",
		"finacial-organization":"financial-organizations",
		"service-provider":"service-providers"
	}
	
	PARAMS = urllib.urlencode({'api_key':CB_KEY})
	
	def init(self):
		option_list = (
			make_option('-u',
						action="store_true",
						dest="update"),
			make_option('-c',
						action="store_true",
						dest="clean"),
		)

	def get_cb_url(self,mode,cb_type,**opts):
		"""constructs URL for accessing CB, based on mode and entity"""
		if mode == "list":
			# get list of all entities of a specific type
			cb_type = self.get_cb_plural(cb_type)
			cb_url = self.CB_BASE_URL + cb_type + ".js?" + self.PARAMS
		elif mode == "info":
			# get info for single entity
			cb_url = self.CB_BASE_URL + cb_type + "/" + opts['permalink'] + ".js?" + self.PARAMS
		return cb_url
		
	def get_cb_plural(self,cb_type):
		"""returns correct plural version of entity type for CB API"""
		return self.ENTITY_TYPES_DICT[cb_type]
	
	@retry(urllib2.URLError,delay=10)		
	def get_json(self,url):
		""" returns JSON file in Python-readable format from URL"""
		sys.stdout.write("fetching " + url + "\n")
		try:
			return json.load(urllib2.urlopen(url))
		except:
			return None

	def get_current_entities_cb_permalinks(self):
		"""returns CB permalinks of all entities currenty in db """
		entities = Entity.objects.filter(cb_permalink__isnull=False)
		permalinks = [e.cb_permalink for e in entities]
		# for e in entities:
		# 	permalinks.append(e.cb_permalink)
		return permalinks

	def add_entity(self,data):
		""" adds entity """
		e = Entity()
		fields = self.get_fields_quick(data)
		for k,v in fields.iteritems():
			setattr(e,k,v)
		e.save()
		sys.stdout.write(e.name.encode("utf8") + " added\n")
		return e

	def entity_exists(self,permalink):
		""" checks to see if a CB entity has already been added to db """
		if permalink in self.CURRENT_ENTITIES:
			return True
		else:
			return False
	
	def get_cb_entity_list(self,cb_type):	
		""" returns list of all entities of particular type """
		entities = []
		cb_url = self.get_cb_url('list',cb_type)
		try:
			data = self.get_json(cb_url)
		except urllib2.HTTPError, e:
			sys.stdout.write(str(e.code))
		except urllib2.URLError, e:
			sys.stdout.write(str(e.args))
		for d in data:
			entities.append({'permalink':d['permalink'],'type':cb_type})
		return data
	
	def get_all_cb_entities(self,cb_type):
		""" adds all entities of particular type with minimum information """
		data = self.get_cb_entity_list(cb_type['single'])

		for d in data:
			d['type'] = cb_type['single']
			# check to see if entity exists
			if not self.entity_exists(d['permalink']):
				# add it to list of current entitites for any possible duplicate entries
				self.CURRENT_ENTITIES.append(d['permalink'])
				self.add_entity(d)
	
	def get_fields_quick(self,data):
		""" maps CB permalink, name, and type to db """
		# checks to see what type of entity
		if data['type'] == 'person':
			# if person, add separate name fields and combine for "full_name"
			fields = {
				'cb_permalink':data['permalink'],
				'full_name':data['first_name'] + " " + data['last_name'],
				'first_name':data['first_name'],
				'last_name':data['last_name'],
				'type':data['type'],
				'cb_type':data['type']
			}
		else:
			# if not person, just full_name field gets filled
			fields = {
				'cb_permalink':data['permalink'],
				'name':data['name'],
				'type':'organization',
				'subtype':data['type'],
				'cb_type':data['type']
				}
		return fields
	
	def update_all_entities(self):
		""" grabs all entities from db, updates them based on CB """
		# fetch all entities from db
		entities = Entity.objects.filter(cb_permalink__isnull=False)
		for e in entities:
			# make sure it has a CB entry
			data = self.get_entity_cb_info(e)
			# make sure API returned valid JSON
			if data:
				# only update if information has changed since last update
				if not e.cb_updated or datetime.strptime(data['updated_at'],"%a %b %d %H:%M:%S UTC %Y") > e.cb_updated:
					self.add_all_details(e,data)
					sys.stdout.write("Added details for " + e.name.encode("utf8","ignore") + "\n")
	
	def add_all_details(self,entity,data):
		""" adds remainder of details from CB to db """
		fields = self.get_fields(data,entity.cb_type)
		for k,v in fields.iteritems():
			setattr(entity,k,v)
		entity.save()
		# add logo
		if data['image']:
			self.get_cb_image(entity,data['image']['available_sizes'][2][1])
			# entity.logo_cb_attribution = data['image']['attribution']
			# entity.save()
		# adds relationships, financings, offices
		# self.parse_relationships(entity,data)
		if entity.cb_type == "company":
			self.parse_offices(entity,data)
			self.parse_financings(entity,data)
		elif entity.cb_type == 'financial-organization' or entity.cb_type == 'service-provider':
			self.parse_offices(entity,data)
		# report 
		sys.stdout.write(entity.name.encode("utf8","ignore") + " updated\n")
	
	def get_cb_image(self,entity,url):
		
		img_url = "http://www.crunchbase.com/" + url
		img_filename = urlparse(img_url).path.split('/')[-1]
		img = None
		try:
			img = urllib2.urlopen(img_url)
		except urllib2.HTTPError, e:
			sys.stdout.write(str(e.code))
		if img:
			logo = Image()
			logo.entity = entity
			logo.source = 'crunchbase'
			logo.type = 'logo'
			logo.save()
			with open('tmp_img','wb') as f:
				f.write(img.read())
			with open('tmp_img','r') as f:
				img_file = File(f)
				logo.logo.save(img_filename,img_file,True)
			os.remove('tmp_img')
		sys.stdout.write("Added image for " + entity.name.encode('utf8','ignore') + "\n")

	def get_entity_cb_info(self,entity):
		""" fetches full profile of entity from CB """
		cb_url = self.get_cb_url('info',entity.cb_type,entity=entity)
		data = self.get_json(cb_url)
		if data:
			data['cb_type'] = entity.cb_type
			return data
	
	def get_fields(self,data,type):
		""" maps CB fields to db """
		if type == 'company':
			fields = {
				'cb_permalink':data['permalink'],
				'name':data['name'],
				'type':'organization',
				'subtype':'company',
				'summary':data['description'],
				'description':data['overview'],
				'web_url':data['homepage_url'],
				'twitter_handle':data['twitter_username'],
				'aliases':data['alias_list'],
				'domain':data['category_code'],
				'cb_url':data['crunchbase_url'],
				'total_money':data['total_money_raised'],
				'no_employees':data['number_of_employees']
				}
			# convert dates to datetime objects or empty strings
			founded_date = str(data['founded_month'])+"/"+str(data['founded_day'])+"/"+str(data['founded_year'])
			try:
				founded_date = datetime.strptime(founded_date,"%m/%d/%Y")
			except:
				founded_date = None
			fields['founded_date'] = founded_date
			deadpooled_date = str(data['deadpooled_month'])+"/"+str(data['deadpooled_day'])+"/"+str(data['deadpooled_year'])
			try:
				deadpooled_date = datetime.strptime(deadpooled_date,"%m/%d/%Y")
			except:
				deadpooled_date = None
			fields['deadpooled_date'] = deadpooled_date
		elif type == 'person':
			fields = {
				'cb_permalink':data['permalink'],
				'full_name':data['first_name'] + " " + data['last_name'],
				'first_name':data['first_name'],
				'last_name':data['last_name'],
				'type':'person',
				'description':data['overview'],
				'url':data['homepage_url'],
				'birthplace':data['birthplace'],
				'twitter_handle':data['twitter_username'],
				}
				# convert dates to datetime objects
			birth_date = str(data['born_month'])+"/"+str(data['born_day'])+"/"+str(data['born_year'])
			try:
				birth_date = datetime.strptime(birth_date,"%m/%d/%Y")
			except:
				birth_date = None
			fields['birth_date'] = birth_date
		elif type == 'financial-organization':
			fields = {
				'cb_permalink':data['permalink'],
				'name':data['name'],
				'type':'organization',
				'subtype':'financial-organization',
				'summary':data['description'],
				'description':data['overview'],
				'web_url':data['homepage_url'],
				'twitter_handle':data['twitter_username'],
				'aliases':data['alias_list'],
				'cb_url':data['crunchbase_url'],
				'no_employees':data['number_of_employees']
				}
				# convert dates to datetime objects
			founded_date = str(data['founded_month'])+"/"+str(data['founded_day'])+"/"+str(data['founded_year'])
			try:
				founded_date = datetime.strptime(founded_date,"%m/%d/%Y")
			except:
				founded_date = None
			fields['founded_date'] = founded_date
		elif type == 'service-provider':
			fields = {
				'cb_permalink':data['permalink'],
				'name':data['name'],
				'type':'service-provider',
				'subtype':'service-provider',
				'description':data['overview'],
				'web_url':data['homepage_url'],
				'aliases':data['alias_list'],
				'cb_url':data['crunchbase_url'],
				}
		fields['cb_updated'] = datetime.now()
		return fields	
	
	def parse_relationships(self,entity,data):
		""" loops through all relationships, adds people who don't already exist, updates and adds relationships """
		rels = data['relationships']
		for r in rels:
			if entity.cb_type == "person":
				permalink = r['firm']['permalink']
			else:
				permalink = r['person']['permalink']
			# check to see if person already exists
			if not self.entity_exists(permalink):
				if entity.cb_type == 'person':
					data = {'type':r['firm']['type_of_entity'],'name':r['firm']['name'],'permalink':r['firm']['permalink']}
				else:
					data = {'type':'person','first_name':r['person']['first_name'],'last_name':r['person']['last_name'],'permalink':r['person']['permalink']}
				e = self.add_entity(data)
				self.add_relationship(entity,e,r)
			else:
				e = Entity.objects.get(cb_permalink=permalink)
				# check to see if relationship already exists
				if self.rel_exists(entity,e):
					self.update_relationship(entity,e,r)
				else:
					self.add_relationship(entity,e,r)
	
	def rel_exists(self,entity1,entity2):
		""" determines if relationship between entity already exists """
		if entity2 in entity1.rels.all():
			return True
		else:
			return False
	
	def add_relationship(self,entity,person,rel):
		""" adds relationship """
		current = not rel['is_past']
		r = Relationship.objects.create(entity1=entity,entity2=person,description=rel['title'],current=current)
		r.save()
	
	def update_relationship(self,entity,person,rel):
		""" updates existing relationship """
		#sys.stdout.write(entity.name().encode("utf8","ignore") + " " + person.name().encode('utf8',"ignore") + " " + rel['title'])
		r = Relationship.objects.get(entity1=entity,entity2=person)
		r.description = rel['title']
		r.current = not rel['is_past']
		r.save()
		
	def parse_financings(self,entity,data):
		""" loops through all financings, adds entities that don't exist, adds and updates financings """
		financings = data['funding_rounds']
		for fin in financings:
			# check to see if financing already exists
			if not self.financing_exists(entity,fin):
				f = self.add_financing(entity,fin)
			else:
				f = self.update_financing(entity,fin)
	
	def financing_exists(self,entity,financing):
		try:
			fin = Financing.objects.get(round_code=financing['round_code'],target=entity)
		except:
			return False
		return fin

	def add_financing(self,entity,f):
		""" adds financing """
		# gets datetime object from cb dates
		fin_date = self.construct_date(f['funded_month'],f['funded_day'],f['funded_year'])
		if f['raised_amount'] is not None:
			f['raised_amount'] = str(f['raised_amount'])
		fin = Financing.objects.create(target=entity,round_code=f['round_code'],amount=f['raised_amount'],currency=f['raised_currency_code'],date=fin_date)
		fin.save()
		# loop through each individual investment
		for i in f['investments']:
			# check to see what type of investor
			if i['company'] is not "null":
				i_sub = i['company']
				cb_type = 'company'
			elif i['financial_org'] is not "null":
				i_sub = i['financial_org']
				cb_type = 'financial_org'
			elif i['person'] is not "null":
				i_sub = i['person']
				cb_type = 'person'
			# skip persons
			if i_sub and cb_type != 'person':
				# check to see if this entity already exists
				if self.entity_exists(i_sub['permalink']):
					# retrieve entity
					e = Entity.objects.get(cb_permalink=i_sub['permalink'])
				else:
					# add entity to db
					if cb_type == 'person':
						e = self.add_entity({'first_name':i_sub['first_name'],'last_name':i_sub['last_name'],"permalink":i_sub['permalink'],"cb_type":cb_type,'type':'person'})
					else:
						#e = self.add_entity({"name":i_sub['name'],"permalink":i_sub['permalink'],"cb_type":cb_type,'type':'organization'})
						e = self.add_entity({"name":i_sub['name'],"permalink":i_sub['permalink'],'type':cb_type})
					# get full CB info
					data = self.get_entity_cb_info(e)
					# add remainder of CB data to db
					self.add_all_details(e,data)
				# now that financing and all parties are created, add investment relationship
				inv = Investment.objects.create(investor=e,financing=fin)
				inv.save()
		fin.save()
	
	def update_financing(self,entity,cb_financing):
		# fetch financing
		fin = Financing.objects.get(round_code=cb_financing['round_code'],target=entity)
		# fetch investments, see if they exist already
		for i in cb_financing['investments']:
			if i['company'] is not None:
				i_sub = i['company']
				i['cb_type'] = 'company'
			elif i['financial_org'] is not None:
				i_sub = i['financial_org']
				i['cb_type'] = 'financial_org'
			elif i['person'] is not None:
				i_sub = i['person']
				i['cb_type'] = 'person'
			if not self.investment_exists(fin,i_sub['permalink']):
				if i['cb_type'] == 'person':
					# it's a personal investor
					# full_name = i_sub['first_name'] + " " + i_sub['last_name']
					# e = self.add_entity({'first_name':i_sub['first_name'],'last_name':i_sub['last_name'],'full_name':full_name,'permalink':i_sub['permalink'],'type':"person",'cb_type':i['cb_type']},False)
					pass
				else:
					# it's an organizational investor
					# e = self.add_entity({'name':i_sub['name'],'permalink':i_sub['permalink'],'type':"organization",'cb_type':i['cb_type']},False)
					e = self.add_entity({'name':i_sub['name'],'permalink':i_sub['permalink'],'type':i['cb_type']})
					investment = Investment.objects.create(financing=fin,investor=e)

	def construct_date(self,year,month,day):
		""" takes three values, checks which are none and returns date value or none """
		if isinstance(year,int):
			year = str(year)
		if isinstance(month,int):
			month = str(month)
		if isinstance(day,int):
			day = str(day)
		# check to see what values are null
		if month is None and day is None and year is None:
			# all values are None, return None
			return None
		elif month is None and day is None:
			# only year has a value
			date = datetime.strptime(year,"%Y")
		elif day is None:
			date = datetime.strptime(str(month)+"/"+str(year),"%m/%Y")
		else:
			date = datetime.strptime(str(month)+"/"+str(day)+"/"+str(year),"%m/%d/%Y")
		return date

	def investment_exists(self,financing,cb_permalink):
		try:
			investor = Entity.objects.get(cb_permalink=cb_permalink)
		except:
			return False
		if investor in financing.investors.all():
			return True
		return False

	def parse_offices(self,entity,data):
		""" loops through all offices, adds them and connects them to entities """
		offices = data['offices']
		for o in offices:
			if self.office_exists(entity,o):
				self.update_office(entity,o)
			else:
				self.add_office(entity,o)
	
	def office_exists(self,entity,office):
		""" checks whether office exists """
		o = Office.objects.filter(entity=entity,description=office['description'])
		if o:
			return True
		else:
			return False
			
	def add_office(self,entity,office):
		""" adds office and links it to entity """
		o = Office()
		o.entity = entity
		o.description = office['description']
		o.addr_1 = office['address1']
		o.addr_2 = office['address2']
		o.zip_code = office['zip_code']
		o.city = office['city']
		o.state_code = office['state_code']
		o.country_code = office['country_code']
		if o.latitude:
			o.latitude = str(office['latitude'])
		if o.longitude:
			o.longitude = str(office['longitude'])
		o.save()
		sys.stdout.write(o.name().encode('utf8','ignore') + " added\n")
		
	def update_office(self,entity,office):
		""" updates office details """
		o = Office.objects.get(entity=entity,description=office['description'])
		o.entity = entity
		o.description = office['description']
		o.addr_1 = office['address1']
		o.addr_2 = office['address2']
		o.zip_code = office['zip_code']
		o.city = office['city']
		o.state_code = office['state_code']
		o.country_code = office['country_code']
		if o.latitude:
			o.latitude = str(office['latitude'])
		if o.longitude:
			o.longitude = str(office['longitude'])
		o.save()
		sys.stdout.write(o.name().encode('utf8','ignore') + " updated\n")

	def add_org(self,permalink,cb_type):
		if cb_type == "financial_org":
			cb_type = "financial-organization"
		cb_url = self.get_cb_url('info',cb_type,permalink=permalink)
		data = self.get_json(cb_url)

		# ensure data was returned
		if data:
			founded_date = self.construct_date(data['founded_year'],data['founded_month'],data['founded_day'])
			org = Entity(name=data['name'],cb_permalink=data['permalink'],description=data['description'],web_url=data['homepage_url'],blog_url=data['blog_url'],twitter_handle=data['twitter_username'],founded_date=founded_date)
			org.save()
			return org

class CBPeople(CBBase):

	def update_person(self,person):
		return None

	def add_pic(self,person,data):
		# make sure there 
		if data is not None:
			for i in data['available_sizes']:
				# compile url
				url = "http://www.crunchbase.com/" + i[1]
				self.upload_pic(person,url)

	def upload_pic(self,person,url):
		img_filename = urlparse(url).path.split('/')[-1]
		img = None
		try:
			img = urllib2.urlopen(url)
		except urllib2.HTTPError, e:
			print str(e.code)
		if img:
			pic = Picture()
			pic.person = person.profile
			pic.source = 'crunchbase'
			with open('tmp_img','wb') as f:
				f.write(img.read())
			with open('tmp_img','r') as f:
				img_file = File(f)
				pic.pic.save(img_filename,img_file,True)
			os.remove('tmp_img')

	def add_person(self,data):
		cb_url = self.get_cb_url('info','person',permalink=data['permalink'])
		data = self.get_json(cb_url)
		## uncomment to debug data
		# print data
		# return None
		if data:
			username = data['first_name'] + data['last_name'] + "_crunchbase"
			try:
				p = User.objects.get(username=username)
			except:
				p = User()
				p.username = username[:30]
			
			p.is_active = False
			p.first_name = data['first_name'][:30]
			p.last_name = data['last_name'][:30]
			p.save()

			## Create Profile
			p.profile.first_name = data['first_name']
			p.profile.last_name = data['last_name']
			
			p.profile.status = "crunchbase"
			p.profile.save()

			## Create account
			acct = Account(service="crunchbase",owner=p,uniq_id=data['permalink'],linked_on=datetime.now(),last_scanned=datetime.now())
			acct.save()

			self.add_educations(p,data['degrees'])
			self.add_positions(p,data['relationships'])
			self.add_pic(p,data['image'])

			print "Added: " + username

	def add_educations(self,person,educations):
		for e in educations:
			# check to see if institution already exists
			inst = Entity.objects.filter(name=e['institution'])
			if not inst.exists():
				inst = self.add_institution(e['institution'])
			else:
				inst = inst[0]
			# check to see if education already exists
			ed = Position.objects.filter(degree=e['degree_type'],entity=inst)
			if not ed.exists():
				end_date = self.construct_date(e['graduated_year'],e['graduated_month'],e['graduated_day'])
				ed = Position(entity=inst,person=person,degree=e['degree_type'],field=e['subject'],end_date=end_date,current=True)
				ed.save()

	def add_positions(self,person,rels):
		for r in rels:
			# check if current position
			if r['is_past'] == False:
				current = True
			else:
				current = False
			# check to see if position already exists
			org = Entity.objects.filter(Q(cb_permalink=r['firm']['permalink']) | Q(name=r['firm']['name']))
			if not org.exists():
				org = self.add_org(r['firm']['permalink'],r['firm']['type_of_entity'])
			else:
				org = org[0]
			pos = Position.objects.filter(title=r['title'],entity=org)
			if not pos.exists():
				# create new position
				try:
					pos = Position(title=r['title'][:150],entity=org,person=person,current=current)
					pos.save()
				except ValueError, e:
					print str(e)

	def add_or_update_person(self,person):
		# check to see if person already exists\
		username = person['first_name'] + person['last_name'] + "_crunchbase"
		p = User.objects.filter(Q(account__service="crunchbase",account__uniq_id=person['permalink']) | Q(username=username[:30]))
		if p.exists():
			p = p[0]
			self.update_person(p)
		else:
			## Create User
			self.add_person(person)

	def add_institution(self,name):
		inst = Entity(type="school",name=name)
		inst.save()
		return inst

	def parse_people(self):
		cb_url = self.get_cb_url('list','person')
		env = os.environ.get("PROSPR_ENV")
		try:
			if env == "production":
				f = open("/app/prosperime/cb_people_list.json","rU")
			else:
				f = open('cb_people_list.json','rU')
			people_list = json.loads(f.read())
		except:
			people_list = self.get_json(cb_url)
			f = open('cb_people_list.json','w')
			f.write(json.dumps(people_list))
			f.close()
		for p in people_list:
			# print p['first_name'] + " " + p['last_name']
			self.add_or_update_person(p)
		
			
			