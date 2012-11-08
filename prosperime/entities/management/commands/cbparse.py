# Python imports
import urllib
import urllib2
import pkg_resources
pkg_resources.require('simplejson') # not sure why this is necessary
import simplejson
from datetime import datetime
from _retry import retry

# Django imports
from django.core.management.base import BaseCommand, CommandError
from entities.models import Entity, Relationship, Financing, Office

class Command(BaseCommand):

	CB_KEY = "jwyw2d2vx63k3z6336yzpd4h"

	CB_BASE_URL = "http://api.crunchbase.com/v/1/"
	
	CURRENT_ENTITIES = ()
	
	ENTITY_TYPES = (
		{'single':'company','plural':'companies'},
		{'single':'person','plural':'people'},
		{'single':'financial-organization','plural':'financial-organizations'},
		{'single':'service-provider','plural':'service-providers'}
		)
	
	PARAMS = urllib.urlencode({'api_key':CB_KEY})
	
	def getCurrentEntities(self):
		entities = Entity.objects.all()
		permalinks = []
		for e in entities:
			permalinks.append(e.cb_permalink)
		return permalinks
	
	#@retry(tries=3)		
	def getJSON(self,url):
		return simplejson.load(urllib2.urlopen(url))
	
	def getEntityList(self,type):	
		""" returns list of all entities of particular type """
		entities = ()
		cb_url = self.CB_BASE_URL + type.plural + ".js?" + self.PARAMS
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
		# need to add some set logic her
		cb_url = self.CB_BASE_URL + type['plural'] + ".js?" + self.PARAMS
		try:
			data = self.getJSON(cb_url)
		except urllib2.HTTPError, e:
			self.stdout.write(e.code)
		except urllib2.URLError, e:
			self.stdout.write(e.args)

		for d in data:
			d['type'] = type['single']
			if not self.entityExists((d['permalink'])):
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
	
	def getFieldsQuick(self,data):
		""" maps CB permalink and name to database """
		if data['type'] == 'person':
			fields = {
				'cb_permalink':data['permalink'],
				'full_name':data['first_name'] + " " + data['last_name'],
				'first_name':data['first_name'],
				'last_name':data['last_name'],
				'type':data['type'],
			}
		else:
			fields = {
				'cb_permalink':data['permalink'],
				'full_name':data['name'],
				'type':'organization',
				}
		return fields
	
	def updateAllEntities(self):
		""" grabs all entities from db, updates them based on CB """
		entities = Entity.objects.all()
		for e in entities:
			# make sure it has a CB entry
			if e.cb_permalink is not "null":
				data = getEntityCBInfo(e.cb_permalink)
				# only update if information has changed since last update
				if datetime.strptime(data['updated_at'],"%a %b %d %H:%M:%S UTC %Y") > e.cb_updated:
					addAllDetails(e,data)
					self.stdout.write("Added details for " + e.name.encode("utf8") + "\n")
	
	def getFields(self,data):
		""" maps CB fields to our database """
		if data.type == 'company':
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
				'founded_date':datetime.strptime(data['founded_month']+"/"+data['founded_day']+"/"+data['founded_year'],"%m/%d%Y"),
				'deadpooled_date':datetime.strptime(data['deadpooled_month']+"/"+data['deadpooled_day']+"/"+data['deadpooled_year'],"%m/%d%Y"),
				'cb_url':data['crunchbase_url'],
				'logo':data['image']['available_sizes'][1],
				'logo_attribution':data['image.attribution'],
				'total_money':data['total_money_raised'],
				'no_employees':data['number_of_employees']
				}
		elif entity_type == 'person':
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
				'birth_date':datetime.strptime(data['birth_month']+"/"+data['birth_day']+"/"+data['birth_year'],"%m/%d/%Y"),
				'logo':data['image']['available_sizes'][1],
				'logo_attribution':data['image']['attribution']
			}
		elif data.type == 'financial-organizations':
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
				'founded_date':datetime.strptime(data['founded_month']+"/"+data['founded_day']+"/"+data['founded_year'],"%m/%d%Y"),
				'cb_url':data['crunchbase_url'],
				'logo':data['image.available_sizes'][1],
				'logo_attribution':data['image.attribution'],
				'no_employees':data['number_of_employees']
				}
		elif data.type == 'service-provider':
			fields = {
				'cb_permalink':data['permalink'],
				'full_name':data['name'],
				'type':'service-provider',
				'subtype':'service-provider',
				'description':data['overview'],
				'url':data['homepage_url'],
				'aliases':data['alias_list'],
				'cb_url':data['crunchbase_url'],
				'logo':data['image']['available_sizes'][1],
				'logo_attribution':data['image.attribution'],
				}
		fields['cb_updated'] = datetime.now()
		return fields
	
	def addAllDetails(self,entity,data):
		""" adds remainder of details from CB to db """
		fields = self.getFields(data)
		entity.update(fields)
		entity.save()
		# adds relationships, financings, offices
		self.parseRelationships(entity,data)
		self.parseFinancings(entity,data)
		self.parseOffices(entity,data)
		# report 
		self.stdout.write(entity.full_name.encode("utf8") + " updated\n")
			
	def entityExists(self,permalink):
		#if permalink in self.CURRENT_ENTITIES:
		#	return True
		#return False 
		try:
			e = Entity.objects.get(cb_permalink=permalink)
		except:
			return None
				
	def getEntityCBInfo(self,entity):
		cb_url = self.CB_BASE_URL + entity.type + "/" + entity.name + ".js"
		data = simplejson.load(urllib2.urlopen(cb_url,PARAMS))
		# check to see if entity exists
		if self.entityExists(data.permalink):
			e = self.updateEntity(data,entity.type) # update with relevant data but don't add new entity
		else:
			e = self.addEntity(data,entity.type) # add and update with relevant data
		self.parseRelationships(e,data)
		self.parseOffices(e,data)
		if entity.type == "company":
			self.parseFinancings(e,data)	
				
	def updateEntity(self,data,entity_type,entity):
		e = Entity.objects.get(cb_permalink=data.permalink)
		fields = self.getFields(data,entity_type)
		e.update(fields)
		e.save()
		self.stdout.write(e.full_name.encode("utf8") + " updated\n")
		return e
	
	def parseRelationships(self,entity,data):
		""" loops through all relationships, adds people who don't already exist, updates and adds relationships """
		rels = data.relationships
		for r in rels:
			# check to see if person already exists
			if not self.entityExists(r['person']['permalink']):
				data = {'first_name':r['person']['first_name'],'last_name':r['person']['last_name'],'permalink':r['person']['permalink']}
				p = addEntity(data)
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
		if person in entity.relationship_set:
			return True
		else:
			return False
	
	def addRelationship(self,entity,person,rel):
		""" adds relationship """
		current = not rel.is_past
		r = Relationship.objects.create(entity1=entity,entity2=person,type=rel.position,current=current)
		r.save()
	
	def updateRelationship(self,entity,person,rel):
		""" updates existing relationship """
		r = Relationship.objects.get(entity1=entity,entity2=p,description=rel["title"])
		r.type = rel.title
		r.current = not rel.is_past
		r.save()
		
	def parseFinancings(self,entity,data):
		""" loops through all financings, adds entities that don't exist, adds and updates financings """
		fins = data.funding_rounds
		for fin in fins:
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
		offices = data.offices
		for o in offices:
			if self.officeExists(entity,o):
				self.updateOffice(entity,o)
			else:
				self.addOffice(entity,o)
	
	def officeExists(self,entity,office):
		""" checks whether office exists """
		try:
			o = Office.objects.filter(entity=entity,description=office['description'])
			return True
		except:
			return False
	
	def addOffice(self,entity,office):
		""" adds office and links it to entity """
		o = Office.objects.create(description=office['description'],addr1=office["address1"],addr2=office["address2"],zip_code=office["zip_code"],city=office["city"],state_code=office["state_code"],country_code=office["county_code"],latitute=office["latitude"],longitude=office["longitude"])
		o.save()
		self.stdout.write(o.description + " office for " + entity.name + " added\n")
		
	def updateOffice(self,entity,office):
		""" updates office details """
		o = Office.objects.filter(entity=entity,description=office['description'])
		o.description = office['description']
		o.addr1 = office['address1']
		o.addr2 = office['address2']
		o.zip_code = office['zip_code']
		o.city = office['city']
		o.state_code = office['state_code']
		o.country_code = office['country_code']
		o.latitute = office['latitude']
		o.longitude = office['longitude']
		o.save()
		self.stdout.write(office.description + " office for " + entity.name + " updated\n")
		
	def handle(self,types=ENTITY_TYPES,*args, **options):
		""" gets basic info for all entities, then cycles through and updates information """
		self.CURRENT_ENTITIES = self.getCurrentEntities()
		for type in types:
			self.getAllEntities(type)
		self.updateAllEntities()
		
			
			