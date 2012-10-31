# Python imports
import urllib
import urllib2
import simplejson
from datetime import datetime

# Django imports
from django.core.management.base import BaseCommand, CommandError
from polls.models import Poll

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
		entities = ()
		CB_URL = CB_BASE_URL + type + ".js"
		data = simplejson.load(urllib2.urlopen(cb_url,PARAMS))
		for d in data:
			entities.append({'name':d.name,'permalink':d.permalink,'type':e.single})
		return entities
				
	def getEntity(entity):
		cb_url = CB_BASE_URL + entity.type + "/" + entity.name + ".js"
		data = simplejson.load(urllib2.urlopen(cb_url,PARAMS)
		# check to see if entity exists
		if e = entityExists(data.permalink) is not None:
			updateEntity(data,entity.type,e) # update with relevant data but don't add new entity
		else:
			addEntity(data,entity.type) # add and update with relevant data
		parseRelationships(entity)
		parseFinancings(entity)	
		parseOffices(entity)e
			
	def entityExists(permalink):
		try:
			e = Entity.objects.get(cb_permalink=permalink)
			return e
		except:
			return None
	
	def addEntity(self, data, entity_type):
		fields = 
		
	def updateEntity(self,data,entity_type,entity):
		# e = Entity.objects.get(cb_permalink=data.permalink)
		fields = {
			'full_name':data.name,
			'type':entity_type,
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
			'total_money':data.total_money_raised,
			'no_employees':data.number_of_employees
			}
		entity.update(fields)
		entity.save()
