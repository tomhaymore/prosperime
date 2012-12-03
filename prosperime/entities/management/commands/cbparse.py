# Python imports
import os
import urllib
import urllib2
from urlparse import urlparse
# import pkg_resources
# pkg_resources.require('simplejson') # not sure why this is necessary
# import simplejson
from datetime import datetime
from _retry import retry
from optparse import make_option

# Django imports
from django.core.management.base import BaseCommand, CommandError
from entities.models import Entity, Relationship, Financing, Office, Investment
from django.core.files import File
from django.utils import simplejson

class Command(BaseCommand):
	
	option_list = BaseCommand.option_list + (
			make_option('-u',
						action="store_true",
						dest="update"),
			make_option('-c',
						action="store_true",
						dest="clean"),
		)
		
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
	
	def getCBURL(self,mode,cb_type,**kwargs):
		"""constructs URL for accessing CB, based on mode and entity"""
		if mode == "list":
			# get list of all entities of a specific type
			cb_type = self.getCBPlural(cb_type)
			cb_url = self.CB_BASE_URL + cb_type + ".js?" + self.PARAMS
		elif mode == "info":
			# get info for single entity
			cb_url = self.CB_BASE_URL + cb_type + "/" + kwargs['entity'].cb_permalink + ".js?" + self.PARAMS
		return cb_url
		
	def getCBPlural(self,cb_type):
		"""returns correct plural version of entity type for CB API"""
		return self.ENTITY_TYPES_DICT[cb_type]
	
	@retry(urllib2.URLError,delay=10)		
	def getJSON(self,url):
		""" returns JSON file in Python-readable format from URL"""
		self.stdout.write("fetching " + url + "\n")
		try:
			return simplejson.load(urllib2.urlopen(url))
		except simplejson.JSONDecodeError, e:
			self.stdout.write(str(e.args))
			return None

	def getCurrentEntitiesCBPermalinks(self):
		"""returns CB permalinks of all entities currenty in db """
		entities = Entity.objects.filter(cb_permalink__isnull=False)
		permalinks = []
		for e in entities:
			permalinks.append(e.cb_permalink)
		return permalinks
	
	def getCBEntityList(self,cb_type):	
		""" returns list of all entities of particular type """
		entities = []
		cb_url = self.getCBURL('list',cb_type)
		try:
			data = self.getJSON(cb_url)
		except urllib2.HTTPError, e:
			self.stdout.write(str(e.code))
		except urllib2.URLError, e:
			self.stdout.write(str(e.args))
		for d in data:
			entities.append({'permalink':d['permalink'],'type':cb_type})
		return data
	
	def getAllCBEntities(self,cb_type):
		""" adds all entities of particular type with minimum information """
		data = self.getCBEntityList(cb_type['single'])
		# cb_url = self.getCBURL('list',cb_type['single'])
		# try:
		# 	data = self.getJSON(cb_url)
		# except urllib2.HTTPError, e:
		# 	self.stdout.write(e.code)
		# except urllib2.URLError, e:
		# 	self.stdout.write(e.args)

		for d in data:
			d['type'] = cb_type['single']
			# if self.entityExists((d['permalink'])) is False:
			# 	self.addEntity(d)
			# check against list of current entities to see if it already exists
			# if d['permalink'] not in self.CURRENT_ENTITIES:
			if not self.entityExists(d['permalink']):
				# add it to list of current entitites for any possible duplicate entries
				self.CURRENT_ENTITIES.append(d['permalink'])
				self.addEntity(d)
	
	def addEntity(self,data,):
		""" adds entity """
		e = Entity()
		fields = self.getFieldsQuick(data)
		for k,v in fields.iteritems():
			setattr(e,k,v)
		e.save()
		self.stdout.write(e.full_name.encode("utf8") + " added\n")
		return e
	
	def entityExists(self,permalink):
		""" checks to see if a CB entity has already been added to db """
		# e = Entity.objects.filter(cb_permalink=permalink)
		# if not e:
		# 	return False
		# else:
		# 	return True
		if permalink in self.CURRENT_ENTITIES:
			return True
		else:
			return False
	
	def getFieldsQuick(self,data):
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
				'full_name':data['name'],
				'type':'organization',
				'subtype':data['type'],
				'cb_type':data['type']
				}
		return fields
	
	def updateAllEntities(self):
		""" grabs all entities from db, updates them based on CB """
		# fetch all entities from db
		entities = Entity.objects.filter(cb_permalink__isnull=False)
		for e in entities:
			# make sure it has a CB entry
			# if e.cb_permalink is not "null":
			data = self.getEntityCBInfo(e)
			# make sure API returned valid JSON
			if data:
				#self.stdout.write('recieved data \n')
				# only update if information has changed since last update
				if not e.cb_updated or datetime.strptime(data['updated_at'],"%a %b %d %H:%M:%S UTC %Y") > e.cb_updated:
					self.addAllDetails(e,data)
					self.stdout.write("Added details for " + e.name().encode("utf8","ignore") + "\n")
	
	def addAllDetails(self,entity,data):
		""" adds remainder of details from CB to db """
		fields = self.getFields(data,entity.cb_type)
		for k,v in fields.iteritems():
			setattr(entity,k,v)
		entity.save()
		# add logo
		if data['image']:
			self.getCBImage(entity,data['image']['available_sizes'][2][1])
			entity.logo_cb_attribution = data['image']['attribution']
			entity.save()
		# adds relationships, financings, offices
		self.parseRelationships(entity,data)
		if entity.cb_type == "company":
			self.parseOffices(entity,data)
			self.parseFinancings(entity,data)
		elif entity.cb_type == 'financial-organization' or entity.cb_type == 'service-provider':
			self.parseOffices(entity,data)
		# report 
		self.stdout.write(entity.name().encode("utf8","ignore") + " updated\n")
	
	def getCBImage(self,entity,url):
		self.stdout.write("Adding image for " + entity.name().encode('utf8','ignore') + "\n")
		img_url = "http://www.crunchbase.com/" + url
		img_filename = urlparse(img_url).path.split('/')[-1]
		img = None
		try:
			img = urllib2.urlopen(img_url)
		except urllib2.HTTPError, e:
			self.stdout.write(str(e.code))
		if img:
			with open('tmp_img','wb') as f:
				f.write(img.read())
			with open('tmp_img','r') as f:
				img_file = File(f)
				entity.logo.save(img_filename,img_file,True)
			os.remove('tmp_img')

	def getEntityCBInfo(self,entity):
		""" fetches full profile of entity from CB """
		cb_url = self.getCBURL('info',entity.cb_type,entity=entity)
		data = self.getJSON(cb_url)
		if data:
			data['cb_type'] = entity.cb_type
			return data
	
	def getFields(self,data,type):
		""" maps CB fields to db """
		if type == 'company':
			fields = {
				'cb_permalink':data['permalink'],
				'full_name':data['name'],
				'type':'organization',
				'subtype':'company',
				'summary':data['description'],
				'description':data['overview'],
				'url':data['homepage_url'],
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
		elif type == 'financial-organizations':
			fields = {
				'cb_permalink':data['permalink'],
				'full_name':data['name'],
				'type':'organization',
				'subtype':'financial-organization',
				'summary':data['description'],
				'description':data['overview'],
				'url':data['homepage_url'],
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
				'full_name':data['name'],
				'type':'service-provider',
				'subtype':'service-provider',
				'description':data['overview'],
				'url':data['homepage_url'],
				'aliases':data['alias_list'],
				'cb_url':data['crunchbase_url'],
				}
		fields['cb_updated'] = datetime.now()
		return fields	
				
	# def updateEntity(self,data,entity_type,entity):
	# 	e = Entity.objects.get(cb_permalink=data['permalink'])
	# 	fields = self.getFields(data,entity_type)
	# 	for k,v in fields.iteritems():
	# 		setattr(e,k,v)
	# 	e.save()
	# 	self.stdout.write(e.name().encode("utf8") + " updated\n")
	# 	return e
	
	def parseRelationships(self,entity,data):
		""" loops through all relationships, adds people who don't already exist, updates and adds relationships """
		rels = data['relationships']
		for r in rels:
			if entity.cb_type == "person":
				permalink = r['firm']['permalink']
			else:
				permalink = r['person']['permalink']
			# check to see if person already exists
			if not self.entityExists(permalink):
				if entity.cb_type == 'person':
					data = {'type':r['firm']['type_of_entity'],'name':r['firm']['name'],'permalink':r['firm']['permalink']}
				else:
					data = {'type':'person','first_name':r['person']['first_name'],'last_name':r['person']['last_name'],'permalink':r['person']['permalink']}
				e = self.addEntity(data)
				self.addRelationship(entity,e,r)
			else:
				e = Entity.objects.get(cb_permalink=permalink)
				# check to see if relationship already exists
				if self.relExists(entity,e):
					self.updateRelationship(entity,e,r)
				else:
					self.addRelationship(entity,e,r)
	
	def relExists(self,entity1,entity2):
		""" determines if relationship between entity already exists """
		if entity2 in entity1.rels.all():
			return True
		else:
			return False
	
	def addRelationship(self,entity,person,rel):
		""" adds relationship """
		current = not rel['is_past']
		r = Relationship.objects.create(entity1=entity,entity2=person,description=rel['title'],current=current)
		r.save()
	
	def updateRelationship(self,entity,person,rel):
		""" updates existing relationship """
		#self.stdout.write(entity.name().encode("utf8","ignore") + " " + person.name().encode('utf8',"ignore") + " " + rel['title'])
		r = Relationship.objects.get(entity1=entity,entity2=person)
		r.description = rel['title']
		r.current = not rel['is_past']
		r.save()
		
	def parseFinancings(self,entity,data):
		""" loops through all financings, adds entities that don't exist, adds and updates financings """
		financings = data['funding_rounds']
		for fin in financings:
			# check to see if financing already exists
			if not self.financingExists(entity,fin):
				f = self.addFinancing(entity,fin)
			else:
				f = self.updateFinancing(entity,fin)
	
	def financingExists(self,entity,financing):
		try:
			fin = Financing.objects.get(round=financing['round_code'],target=entity)
		except:
			return False
		return True

	def addFinancing(self,entity,f):
		""" adds financing """
		# gets datetime object from cb dates
		fin_date = self.constructDate(f['funded_month'],f['funded_day'],f['funded_year'])
		if f['raised_amount'] is not None:
			f['raised_amount'] = str(f['raised_amount'])
		fin = Financing.objects.create(target=entity,round=f['round_code'],amount=f['raised_amount'],currency=f['raised_currency_code'],date=fin_date)
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
			# check to see if this entity already exists
			if i_sub:
				if self.entityExists(i_sub['permalink']):
					# retrieve entity
					e = Entity.objects.get(cb_permalink=i_sub['permalink'])
				else:
					# add entity to db
					if cb_type == 'person':
						e = self.addEntity({'first_name':i_sub['first_name'],'last_name':i_sub['last_name'],"permalink":i_sub['permalink'],"cb_type":cb_type,'type':'person'})
					else:
						e = self.addEntity({"name":i_sub['name'],"permalink":i_sub['permalink'],"cb_type":cb_type,'type':'organization'})
					# get full CB info
					data = self.getEntityCBInfo(e)
					# add remainder of CB data to db
					self.addAllDetails(e,data)
				# now that financing and all parties are created, add investment relationship
				inv = Investment.objects.create(investor=e,financing=fin)
				inv.save()
		fin.save()
	
	def updateFinancing(self,entity,cb_financing):
		# fetch financing
		fin = Financing.objects.get(round=cb_financing['round_code'],target=entity)
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
			if not self.investmentExists(fin,i_sub['permalink']):
				if i['cb_type'] == 'person':
					# it's a personal investor
					full_name = i_sub['first_name'] + " " + i_sub['last_name']
					e = self.addEntity({'first_name':i_sub['first_name'],'last_name':i_sub['last_name'],'full_name':full_name,'permalink':i_sub['permalink'],'type':"person",'cb_type':i['cb_type']},False)
				else:
					# it's an organizational investor
					e = self.addEntity({'full_name':i_sub['name'],'permalink':i_sub['permalink'],'type':"organization",'cb_type':i['cb_type']},False)
				investment = Investment.objects.create(financing=fin,investor=e)

	def constructDate(self,month,day,year):
		""" takes three values, checks which are none and returns date value or none """
		# check to see what values are null
		if month is None and day is None and year is None:
			# all values are None, return None
			return None
		elif month is None and day is None:
			date = datetime.strptime(year,"%Y")
		elif day is None:
			date = datetime.strptime(str(month)+"/"+str(year),"%m/%Y")
		else:
			date = datetime.strptime(str(month)+"/"+str(day)+"/"+str(year),"%m/%d/%Y")
		return date

	def investmentExists(self,financing,cb_permalink):
		try:
			investor = Entity.objects.get(cb_permalink=cb_permalink)
		except:
			return False
		if investor in financing.investors.all():
			return True
		return False

	def parseOffices(self,entity,data):
		""" loops through all offices, adds them and connects them to entities """
		offices = data['offices']
		for o in offices:
			if self.officeExists(entity,o):
				self.updateOffice(entity,o)
			else:
				self.addOffice(entity,o)
	
	def officeExists(self,entity,office):
		""" checks whether office exists """
		o = Office.objects.filter(entity=entity,description=office['description'])
		if o:
			return True
		else:
			return False
			
	def addOffice(self,entity,office):
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
		self.stdout.write(o.name().encode('utf8','ignore') + " office for " + entity.name().encode('utf8','ignore') + " added\n")
		
	def updateOffice(self,entity,office):
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
		self.stdout.write(o.name().encode('utf8','ignore') + " office for " + entity.name().encode('utf8','ignore') + " updated\n")

	def handle(self,*args, **options):
		""" gets basic info for all entities, then cycles through and updates information """
		
		if options['update']:
			# doesn't load any new entities from CB, just updates
			self.updateAllEntities()
		elif options['clean']:
			# assumes empty database, starts from scratch
			for t in self.ENTITY_TYPES:
				self.getAllCBEntities(t)
			self.updateAllEntities()
		else:
			# default behavior, loads a list of current entities so it only updates those 
			self.CURRENT_ENTITIES = self.getCurrentEntitiesCBPermalinks()
			for t in self.ENTITY_TYPES:
				self.getAllCBEntities(t)
			self.updateAllEntities()
		
			
			