# Python imports
import urllib
import urllib2
import simplejson
from datetime import datetime

# Django imports
from django.core.management.base import BaseCommand, CommandError
from entities.models import Entity, Relationship, Financing, Office

class Command(BaseCommand):

	CB_KEY = "jwyw2d2vx63k3z6336yzpd4h"

	CB_BASE_URL = "http://api.crunchbase.com/v/1/"

	ENTITY_TYPES = (
		{'single':'company','plural':'companies'},
		{'single':'person','plural':'people'},
		{'single':'financial-organization','plural':'financial-organizations'},
		{'single':'service-provider','plural':'service-providers'}
		)
	
	PARAMS = urllib.urlencode({'api_key':CB_KEY})

	def getEntityList(self,type):	
		""" returns list of all entities of particular type """
		entities = ()
		cb_url = CB_BASE_URL + type.plural + ".js"
		data = simplejson.load(urllib2.urlopen(cb_url,PARAMS))
		for d in data:
			entities.append({'permalink':d.permalink,'type':type.single})
		return entities
	
	def addAllEntities(self,type):
		""" adds all entities of particular type with minimum information """
		cb_url = CB_BASE_URL + type.plural + ".js"
		data = simplejson.load(urllib2.urlopen(cb_url,PARAMS))
		for d in data:
			d.type = type.single
			addEntity(d)
		return entities
	
	def addEntity(self, data):
		""" adds entity """
		e = new Entity()
		fields = getFields(data)
		e.update(fields)
		e.save()
		return e		
	
	def getFields(self,data):
		""" maps CB fields to our database """
		if data.type == 'company':
			fields = {
				'cb_permalink':data.permalink,
				'full_name':data.name,
				'type':'organization',
				'summary':data.description,
				'description':data.overview,
				'url':data.homepage_url,
				'twitter_handle':data.twitter_username,
				'aliases':data.alias_list,
				'domain':data.category_code,
				'founded_date':datetime.strptime(data.founded_month+"/"+data.founded_day+"/"+data.founded_year,"%m/%d%Y")
				'deadpooled_date':datetime.strptime(data.deadpooled_month+"/"+data.deadpooled_day+"/"+data.deadpooled_year,"%m/%d%Y")
				'cb_url':data.crunchbase_url,
				'logo':data.image.available_sizes[0],
				'logo_attribution':data.image.attribution,
				'total_money':data.total_money_raised,
				'no_employees':data.number_of_employees
				}
		elif entity_type == 'person':
			fields = {
				'cb_permalink':data.permalink,
				'first_name':data.first_name,
				'last_name':data.last_name,
				'type':data.type,
				'description':data.overview,
				'url':data.homepage_url,
				'birthplace':data.birthplace,
				'twitter_handle':data.twitter_username,
				'birth_date':datetime.strptime(data.birth_month+"/"+data.birth_day+"/"+data.birth_year,"%m/%d/%Y')
				'logo':data.image.available_sizes[0]
				'logo_attribution':data.image.attribution
			}
		return fields
	
	def entityExists(permalink):
		try:
			e = Entity.objects.get(cb_permalink=permalink)
		except:
			return None
				
	def getEntity(self,entity):
		cb_url = CB_BASE_URL + entity.type + "/" + entity.name + ".js"
		data = simplejson.load(urllib2.urlopen(cb_url,PARAMS)
		# check to see if entity exists
		if entityExists(data.permalink) is not None:
			e = updateEntity(data,entity.type) # update with relevant data but don't add new entity
		else:
			e = addEntity(data,entity.type) # add and update with relevant data
		parseRelationships(e,data)
		parseFinancings(e,data)	
		parseOffices(e,data)
			
	
	
	
		
	def updateEntity(self,data,entity_type,entity):
		e = Entity.objects.get(cb_permalink=data.permalink)
		fields = getFields(data,entity_type)
		e.update(fields)
		e.save()
		return e

	
	
	def parseRelationships(self,entity,data):
		""" loops through all relationships, adds people who don't already exist, updates and adds relationships """
		rels = data.relationships
		for r in rels:
			# check to see if person already exists
			if not entityExists(r.person.permalink):
				p = addPerson(r)
			else:
				p = Entity.objects.get(cb_permalink=r.person.permalink)
			# check to see if relationship already exists
			if relExists(entity,p):
				updateRelationship(entity,p,r)
			else:
				addRelationship(entity,p,r)
	
	def relExists(self,entity,person):
		""" determines if relationship between entity already exists """
		if person in entity.relationship_set:
			return True
		else return False
	
	def updateRelationship(self,entity,p,rel):
		""" updates existing relationship """
		r = Relationship.objects.get(entity1=entity,entity2=p)
		r.type = rel.title
		if rel.is_past is False:
			r.current = True
		else r.current = False
		r.save()
	
	def addRelationship(self,entity,person,rel):
		""" adds relationship """
		current = not rel.is_past
		r = Relationship.objects.create(entity1=entity,entity2=person,type=rel.position,current=current)
		r.save()
		
	def parseFinancings(self,entity,data):
		""" loops through all financings, adds entities that don't exist, adds and updates financings """
		fins = data.funding_rounds
		for fin in fins:
			# check to see if financing already exists
			if not FinancingExists(entity,f):
				f = addFinancing(entity,f)
			else:
				f = updateFinancing(entity,f)
	
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
				cbEntity = getEntity({"name":i_sub.name,"permalink":i_sub.permalink,"type":type})
				e = addEntity(cbEntity,type)
			fin.investors.add(e)
		fin.save()
	
	def parseOffices(self,entity,data):
		""" loops through all offices, adds them and connects them to entities """
		offices = data.offices
		for o in offices:
			if officeExists(entity,o):
				udateOffice(entity,o)
				
if __name__ == "__main__":
    main()