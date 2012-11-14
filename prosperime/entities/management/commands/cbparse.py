# Python imports
import urllib
import urllib2
import pkg_resources
pkg_resources.require('simplejson') # not sure why this is necessary
import simplejson
from datetime import datetime
from _retry import retry
from optparse import make_option

# Django imports
from django.core.management.base import BaseCommand, CommandError
from entities.models import Entity, Relationship, Financing, Office

class Command(BaseCommand):
	
	option_list = BaseCommand.option_list + (
			make_option('-u',
						action="store_true",
						dest="update"),
		)
		
	CB_KEY = "jwyw2d2vx63k3z6336yzpd4h"

	CB_BASE_URL = "http://api.crunchbase.com/v/1/"
	
	CURRENT_ENTITIES = ()
	
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
	
	def getCBURL(self,mode,type,**kwargs):
		"""constructs URL for accessing CB, based on mode and entity"""
		if mode == "list":
			# get list of all entities of a specific type
			type = self.getCBPlural(type)
			cb_url = self.CB_BASE_URL + type + ".js?" + self.PARAMS
		elif mode == "info":
			# get info for single entity
			cb_url = self.CB_BASE_URL + type + "/" + kwargs['entity'].cb_permalink + ".js?" + self.PARAMS
		return cb_url
		
	def getCBPlural(self,type):
		"""returns correct plural version of entity type for CB API"""
		return self.ENTITY_TYPES_DICT[type]
	
	def getCurrentEntitiesCBPermalinks(self):
		"""returns CB permalinks of all entities currenty in db """
		entities = Entity.objects.all()
		permalinks = []
		for e in entities:
			permalinks.append(e.cb_permalink)
		return permalinks
	
	@retry(urllib2.URLError,delay=10)		
	def getJSON(self,url):
		""" returns JSON file in Python-readable format from URL"""
		self.stdout.write("fetching " + url + "\n")
		return simplejson.load(urllib2.urlopen(url))
	
	def getEntityList(self,type):	
		""" returns list of all entities of particular type """
		entities = ()
		#cb_url = self.CB_BASE_URL + type.plural + ".js?" + self.PARAMS
		cb_url = self.getCBURL('list',type.single)
		try:
			data = self.getJSON(cb_url)
		except urllib2.HTTPError, e:
			self.stdout.write(str(e.code))
		except urllib2.URLError, e:
			self.stdout.write(str(e.args))
		for d in data:
			entities.append({'permalink':d.permalink,'type':type.single})
		return entities
	
	def getAllEntities(self,type):
		""" adds all entities of particular type with minimum information """
		#cb_url = self.CB_BASE_URL + type['plural'] + ".js?" + self.PARAMS
		cb_url = self.getCBURL('list',type['single'])
		try:
			data = self.getJSON(cb_url)
		except urllib2.HTTPError, e:
			self.stdout.write(e.code)
		except urllib2.URLError, e:
			self.stdout.write(e.args)

		for d in data:
			d['type'] = type['single']
			if self.entityExists((d['permalink'])) is False:
				self.addEntity(d)
	
	def addEntity(self, data):
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
		#if permalink in self.CURRENT_ENTITIES:
		#	return True
		#return False 
		e = Entity.objects.filter(cb_permalink=permalink)
		if not e:
			return False
		else:
			return True
	
	def getFieldsQuick(self,data):
		""" maps CB permalink, name, and type to db """
		# checks to see what type of entity
		if data['type'] == 'person':
			fields = {
				'cb_permalink':data['permalink'],
				'full_name':data['first_name'] + " " + data['last_name'],
				'first_name':data['first_name'],
				'last_name':data['last_name'],
				'type':data['type'],
				'cb_type':data['type']
			}
		else:
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
		entities = Entity.objects.all()
		for e in entities:
			# make sure it has a CB entry
			if e.cb_permalink is not "null":
				data = self.getEntityCBInfo(e)
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
		# adds relationships, financings, offices
		self.parseRelationships(entity,data)
		self.parseOffices(entity,data)
		if entity.type == "company":
			self.parseFinancings(e,data)
		# report 
		self.stdout.write(entity.name().encode("utf8","ignore") + " updated\n")
	
	
	def getEntityCBInfo(self,entity):
		""" fetches full profile of entity from CB """
		cb_url = self.getCBURL('info',entity.cb_type,entity=entity))
		try:
			data = self.getJSON(cb_url)
		except urllib2.HTTPError, e:
			self.stdout.write(e.code)
		except urllib2.URLError, e:
			self.stdout.write(e.args)
		data['cb_type'] = entity.cb_type
		return data

		# check to see if entity exists
		#if self.entityExists(data['permalink']):
		#	e = self.updateEntity(data,entity.cb_type,entity) # update with relevant data but don't add new entity
		#else:
		#	e = self.addEntity(data,entity.type) # add and update with relevant data
		#self.parseRelationships(e,data)
		#self.parseOffices(e,data)
		#if entity.type == "company":
		#	self.parseFinancings(e,data)
	
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
				#'founded_date':founded_date,
				#'deadpooled_date':deadpooled_date,
				'cb_url':data['crunchbase_url'],
				#'logo':data['image']['available_sizes'][1],
				#'logo_attribution':data['image']['attribution'],
				'total_money':data['total_money_raised'],
				'no_employees':data['number_of_employees']
				}
			# convert dates to datetime objects
			founded_date = str(data['founded_month'])+"/"+str(data['founded_day'])+"/"+str(data['founded_year'])
			try:
				founded_date = datetime.strptime(founded_date,"%m/%d/%Y")
			except:
				founded_date = ''
			if founded_date:
				fields['founded_date'] = founded_date
			deadpooled_date = str(data['deadpooled_month'])+"/"+str(data['deadpooled_day'])+"/"+str(data['deadpooled_year'])
			try:
				deadpooled_date = datetime.strptime(deadpooled_date,"%m/%d/%Y")
			except:
				deadpooled_date = ''
			if deadpooled_date:
					fields['deadpooled_date'] = deadpooled_date
		elif type == 'person':
			# convert dates to datetime objects
			birth_date = str(data['birth_month'])+"/"+str(data['birth_day'])+"/"+str(data['birth_year'])
			try:
				birth_date = datetime.strptime(birth_date,"%m/%d/%Y")
			except:
				birth_date = ''
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
				'birth_date':birth_date,
				#'logo':data['image']['available_sizes'][0][1],
				#'logo_attribution':data['image']['attribution']
			}
		elif type == 'financial-organizations':
			# convert dates to datetime objects
			founded_date = str(data['founded_month'])+"/"+str(data['founded_day'])+"/"+str(data['founded_year'])
			try:
				founded_date = datetime.strptime(founded_date,"%m/%d/%Y")
			except:
				founded_date = ''
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
				'founded_date':founded_date,
				'cb_url':data['crunchbase_url'],
				#'logo':data['image.available_sizes'][0][1],
				#'logo_attribution':data['image.attribution'],
				'no_employees':data['number_of_employees']
				}
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
				#'logo':data['image']['available_sizes'][0][1],
				#'logo_attribution':data['image.attribution'],
				}
		fields['cb_updated'] = datetime.now()
		return fields	
				
	def updateEntity(self,data,entity_type,entity):
		e = Entity.objects.get(cb_permalink=data['permalink'])
		fields = self.getFields(data,entity_type)
		for k,v in fields.iteritems():
			setattr(e,k,v)
		e.save()
		self.stdout.write(e.name().encode("utf8") + " updated\n")
		return e
	
	def parseRelationships(self,entity,data):
		""" loops through all relationships, adds people who don't already exist, updates and adds relationships """
		rels = data['relationships']
		for r in rels:
			# check to see if person already exists
			if not self.entityExists(r['person']['permalink']):
				data = {'type':'person','first_name':r['person']['first_name'],'last_name':r['person']['last_name'],'permalink':r['person']['permalink']}
				p = self.addEntity(data)
				self.addRelationship(entity,p,r)
			else:
				p = Entity.objects.get(cb_permalink=r['person']['permalink'])
				# check to see if relationship already exists
				if self.relExists(entity,p):
					self.updateRelationship(entity,p,r)
				else:
					self.addRelationship(entity,p,r)
	
	def relExists(self,entity,person):
		""" determines if relationship between entity already exists """
		if person in entity.rels.all():
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
		for fin in financingss:
			# check to see if financing already exists
			if not self.FinancingExists(entity,f):
				f = self.addFinancing(entity,f)
			else:
				f = self.updateFinancing(entity,f)
	
	def addFinancing(self,entity,f):
		""" adds financing """
		fin = Financing.objects.create(round=f.round_code,amount=f.raised_amount,currency=f.raised_currency,date=datetime.strptime(f.funded_month+"/"+f.funded_day+"/"+f.funded_year,"%m/%d/%Y"))
		fin.save()
		for i in f.investments:
			if i.company is not "null":
				i_sub = i.company
				type = 'company'
			elif i.financial_org is not "null":
				i_sub = i.financial_org
				type = 'financial_org'
			elif i.person is not "null":
				i_sub = i.person
				type = 'person'
			if entityExists(i_sub.permalink):
				e = Entity.objects.get(cb_permalink=i_sub.permalink)
			else:
				cbEntity = self.getEntity({"name":i_sub.name,"permalink":i_sub.permalink,"type":type})
				e = self.addEntity(cbEntity,type)
			fin.investors.add(e)
		fin.save()
	
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
		
	def handle(self,types=ENTITY_TYPES,*args, **options):
		""" gets basic info for all entities, then cycles through and updates information """
		
		
		if options['update']:
			self.updateAllEntities()
		else:
			self.CURRENT_ENTITIES = self.getCurrentEntitiesCBPermalinks()
			for type in types:
				self.getAllEntities(type)
			self.updateAllEntities()
		
			
			