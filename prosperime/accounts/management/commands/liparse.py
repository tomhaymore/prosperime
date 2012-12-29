# from Python
import oauth2 as oauth
import cgi
from datetime import datetime, time
import urllib2
import os
from math import ceil
from optparse import make_option
import urlparse

# from Django
from django.utils import simplejson
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from accounts.models import Account, Profile, Connection
from entities.models import Position, Entity, Image, Industry, Office
from django.core.files import File

# LinkedIn API credentials
linkedin_key = '8yb72i9g4zhm'
linkedin_secret = 'rp6ac7dUxsvJjQpS'

# fields from connections API
fields = "(id,headline,firstName,lastName,positions:(start-date,end-date,title,is-current,summary,company:(id)),public-profile-url)"
co_fields = "(id,name,universal-name,company-type,ticker,website-url,industries,status,logo-url,blog-rss-url,twitter-id,employee-count-range,locations:(description,address:(street1,street2,city,state,country-code,postal-code)),description,stock-exchange)"



class Command(BaseCommand):
	
	acct_id = ''

	# construct api url
	api_url = "http://api.linkedin.com/v1/people/~/connections:" + fields + "?format=json"
	co_api_url = "http://api.linkedin.com/v1/companies/"

	# include options for user id + account id

	option_list = BaseCommand.option_list + (
			# option for storing user id
			make_option('-u','--user_id',
						action="store",
						type="int",
						dest="user_id"),
			# option for storing acct id
			make_option('-a','--acct_id',
						action="store",
						type="int",
						dest="acct_id"),
		)

	def get_access_token(self,acct_id):

		# get account
		acct = Account.objects.get(pk=acct_id,service="linkedin")

		# check to make sure token is current; if not, re-authorize
		if acct.expires_on <= datetime.now():
			# set expired flag to true
			acct.status = "expired"
			acct.save()
			# need to raise exception here
			raise CommandError
		elif acct.status == "expired":
			# need to raise exception here
			raise CommandError

		# assign token to dictionary
		access_token = {
			'oauth_token_secret':acct.token_secret,
			'oauth_token':acct.access_token,
			'last_scanned':acct.last_scanned
		}

		return access_token

	def get_connections(self,acct_id,start=0):
		
		# get oauth credentials from account
		access_token = self.get_access_token(acct_id)

		# construct oauth client
		consumer = oauth.Consumer(linkedin_key, linkedin_secret)
 
		token = oauth.Token(
			key=access_token['oauth_token'], 
			secret=access_token['oauth_token_secret'])

		client = oauth.Client(consumer, token)

		# construct api url 
		if access_token['last_scanned']:
			unix_time = access_token['last_scanned'].strftime("%s") # convert datetime to unix timestamp
			api_url = self.api_url + "&modified-since=%s" % (unix_time,)
		else:
			api_url = self.api_url

		# self.stdout.write(api_url)

		resp, content = client.request(api_url)
		
		# convert connections to JSON
		content = simplejson.loads(content)

		connections = content['values']

		total_count = int(content['_total'])

		if total_count > 500:
			# need to paginate
			pages = ceil((total_count - 500)/ 500)
			
			for i in range(1,pages+1):
				start_num = i*500+1
				page_api_url = api_url + "start=%i&count=500" % (start_num,)
				resp, content = client.request(api_url)

				# convert connections to JSON
				content = simplejson.loads(content)

				# append additional connections
				connections.append(content['values'])

		return content

	def add_dormant_user(self,user_info):

		# create dormant user account
		temp_username = user_info['firstName'] + user_info['lastName'] + user_info['id']
		temp_username = temp_username[:30]
		# self.stdout.write(temp_username)
		user = User()
		user.username = temp_username
		user.save()

		# create user profile
		user.profile.first_name = user_info['firstName']
		user.profile.last_name = user_info['lastName']
		if 'headline' in user_info:
			user.profile.headline = user_info['headline']		
		user.profile.status = "dormant"
		user.profile.save()

		# create LinkedIn account
		acct = Account()
		acct.owner = user
		acct.service = 'linkedin'
		acct.uniq_id = user_info['id']
		acct.public_url = user_info['publicProfileUrl']
		acct.status = "unlinked"
		acct.save()

		return user


	def get_user(self,acct_id):
		try:
			acct = Account.objects.get(uniq_id=acct_id,service="linkedin")
		except:
			# if user does not exist, return None
			return None
		# if user exists return user
		return acct.owner

	def add_position(self,user,co,data):
		# dectionary of values to test for and then add if present
		positionValues = {'title':'title','description':'summary','current':'isCurrent'}
		
		pos = Position()
		pos.entity = co
		pos.person = user

		for k,v in positionValues.iteritems():
			if v in data:
				setattr(pos,k,data[v])
		
			# pos.title = data['title']
			# pos.summary = data['headline']
			# pos.description = data['summary']
			# pos.start_date = data['start-date']
			# pos.end_date = data['end-date']
			# pos.current = data['is-current']
		
		# check for start date
		if 'startDate' in data:
			# check for month value
			if 'month' in data['startDate']:
				start_date = datetime.strptime(str(data['startDate']['month'])+"/"+str(data['startDate']['year']),"%m/%Y")
			else:
				start_date = datetime.strptime(str(data['startDate']['year']),"%Y")
			pos.start_date = start_date
		# check for end date
		if 'endDate' in data:
			# check for month value
			if 'month' in data['endDate']:
				end_date = datetime.strptime(str(data['endDate']['month'])+"/"+str(data['endDate']['year']),"%m/%Y")
			else:
				end_date = datetime.strptime(str(data['endDate']['year']),"%Y")
			pos.end_date = end_date
		pos.save()

	def update_position(self,user,co,data):
		# selets po
		pos = Position.objects.get(entity=co,person=user,title=data['title'])
		pos.summary = data['headline']
		pos.description = data['summary']
		pos.start_date = data['start-date']
		pos.end_date = data['end-date']
		pos.current = data['is-current']
		pos.save()

	def get_position(self,user,co,data):
		pos = Position.objects.filter(entity=co,person=user,title=data['title'])
		if pos:
			# if position exists, return it
			return pos
		# new position, return None
		return None

	def get_company(self,id):
		try:
			co = Entity.objects.get(li_uniq_id=id)
		except:
			# if company doesn't exist, return None
			return None
		# return company
		return co

	def get_co_li_profile(self,co_id):
		# get oauth credentials from account
		access_token = self.get_access_token(self.acct_id)

		# construct oauth client
		consumer = oauth.Consumer(linkedin_key, linkedin_secret)
 
		token = oauth.Token(
			key=access_token['oauth_token'], 
			secret=access_token['oauth_token_secret'])

		client = oauth.Client(consumer, token)

		# construct api url 
		co_api_url = self.co_api_url + str(co_id) + ":"  + co_fields + "?format=json"

		print co_api_url

		resp, content = client.request(co_api_url)

		# convert connections to JSON
		content = simplejson.loads(content)

		print content
		
		if 'errorCode' in content:
			return None
		return content

	def add_company(self,id):
		# get company profile from LinkedIn
		data = self.get_co_li_profile(id)
		# if nothing returned from LI, return None
		if data is None:
			return None
		
		# add to database
		co = Entity()
		co.name = data['name']
		co.type = 'organization'
		co.li_uniq_id = id
		# coValues = {'li_univ_name':'universalName','li_type':''}
		if 'universalName' in data:
			co.li_univ_name = data['universalName']
		if 'companyType' in data:
			co.li_type = data['companyType']['code']
		if 'ticker' in data:
			co.ticker = data['ticker']
		if 'website-urlteUrl' in data:
			co.web_url = data['websiteUrl']
		# co.domain = data['industries']
		# co.li_status = data['status']
		if 'blog-url' in data:
			co.blog_url = data['blog-url']
		if 'twitterId' in data:
			co.twitter_handle = data['twitterId']
		if 'employeeCountRange' in data:
			co.size_range = data['employeeCountRange']['name']
		if 'description' in data:
			co.description = data['description']
		if 'stockExchange' in data:
			co.stock_exchange = data['stockExchange']['code']
		co.li_last_scanned = datetime.now()
		co.save()

		# add industries
		# TODO add manager that handles this any time domain is added to co
		if 'industries' in data:
			for i in data['industries']['values']:
				# check to see if industry already exists
				industry = self.get_industry(i['name'],i['code'])
				if industry:
					# add industry to domain of company
					co.domains.add(industry)
				else:
					# create new industry
					industry = Industry()
					industry.name=i['name']
					industry.li_code=i['code']
					industry.save()
					# add to domain of company
					co.domains.add(industry)

		# check to see if company has a logo url
		if 'logoUrl' in data:
			# get company logo
			self.save_li_image(co,data['logoUrl'])

		# check to see if locations in company profile
		if 'locations' in data:
			# add offices
			for l in data['locations']['values']:
				self.add_office(co,l)

		return co

	def get_industry(self,name,code):
		try:
			industry = Industry.objects.get(Q(name=name) | Q(li_code=code))
		except:
			# no such industry, return None
			return None
		# return industry object
		return industry

	def save_li_image(self,co,img_url):
		# self.stdout.write("Adding image for " + entity.name().encode('utf8','ignore') + "\n")
		# img_url = "http://www.crunchbase.com/" + url
		# img_filename = urlparse(img_url).path.split('/')[-1]
		img = None
		img_ext = urlparse.urlparse(img_url).path.split('/')[-1].split('.')[1]
		img_filename = co.name + "." + img_ext
		try:
			img = urllib2.urlopen(img_url)
		except urllib2.HTTPError, e:
			self.stdout.write(str(e.code))
		if img:
			logo = Image()
			logo.entity = co
			logo.source = 'linkedin'
			logo.type = 'logo'
			logo.save()
			with open('tmp_img','wb') as f:
				f.write(img.read())
			with open('tmp_img','r') as f:
				img_file = File(f)
				logo.logo.save(img_filename,img_file,True)
			os.remove('tmp_img')
			

	def add_office(self,co,office):
		o = Office()
		officeValues = {'description':'description','is-hq':'is-headquarters'}
		# check to see if there is a description for the office
		if 'description' in office:
			o.description = office['description']
		# check to see if the office has an headquarters value
		if 'is-headquarters' in office:
			o.is_hq = office['is-headquarters']
		
		addressValues = {'addr_1':'street1','addr_2':'street2','city':'city','state_code':'state','postal_code':'postalCode','country_code':'country-code'}
		# check to see if there is an address value
		if 'address' in office:
			for k,v in addressValues.iteritems(): 
				if v in office['address']:
					setattr(o,k,office['address'][v])
					# o.k = office['address'][v]
			# o.addr_1 = office['address']['street1']
			# o.addr_2 = office['address']['street2']
			# o.city = office['address']['city']
			# o.state_code = office['address']['state']
			# o.postal_code = office['address']['postal-code']
			# o.country_code = office['address']['country-code']
		o.entity = co
		o.save()

	def add_connection(self,user1,user2):
		"""
		Adds connections between users
		"""
		cxn = Connection()
		cxn.person1 = user1.profile
		cxn.person2 = user2.profile
		cxn.service = "linkedin"
		cxn.save()

		cxn = Connection()
		cxn.person1 = user2.profile
		cxn.person2 = user1.profile
		cxn.service = "linkedin"
		cxn.save()

	def get_entity(self,id,type="school"):
		try:
			entity = Entity.objects.get(li_type="school",li_uniq_id=id)
			return entity
		except:
			return None

	def add_institution(self,data):
		ed = Entity()
		ed.name = data['schoolName']
		ed.li_uniq_id = data['id']
		ed.type = 'organization'
		ed.sub_type = 'ed-institution'
		ed.li_type = 'school'
		ed.save()
		return ed

	def add_ed_position(self,user,ed,data):
		pos = Position()
		pos.entity = ed
		pos.person = user
		pos.type = 'education'
		pos.degree = data['degree']
		pos.field = data['fieldOfStudy']
		
		# check for start date
		if 'startDate' in data:
			# check for month value
			if 'month' in data['startDate']:
				start_date = datetime.strptime(str(data['startDate']['month'])+"/"+str(data['startDate']['year']),"%m/%Y")
			else:
				start_date = datetime.strptime(str(data['startDate']['year']),"%Y")
			pos.start_date = start_date
		# check for end date
		if 'endDate' in data:
			# check for month value
			if 'month' in data['endDate']:
				end_date = datetime.strptime(str(data['endDate']['month'])+"/"+str(data['endDate']['year']),"%m/%Y")
			else:
				end_date = datetime.strptime(str(data['endDate']['year']),"%Y")
			pos.end_date = end_date
		pos.save()

	def process_connections(self,user_id,acct_id):
		# set update flag
		update = False

		# get connections
		connections = self.get_connections(acct_id)

		# loop through connections
		for c in connections['values']:
			# self.stdout.write(str(c))
			# self.stdout.write(c['id'])

			# check to see if new user
			user = self.get_user(c['id'])
			# check to see if privacy settings prohibit getting any useful information
			if c['firstName'] == 'private' and c['lastName'] == 'private':
				pass
			else:
				if user is None:
					# # flag for only updating positions
					# if user:
					# 	update = True
					# else:
					# 	# add dormant user
					# 	user = self.add_dormant_user(c)
				
					user = self.add_dormant_user(c)
					self.add_connection(self.focal_user,user)
					# self.stdout.write(user)
					# process education
					# if 'values' in c['educations']:
					# 	for e in c['educations']['values']:
					# 		# check for institution id
					# 		if 'id' in e:
					# 			# check to see institution alreday exists
					# 			ed = self.get_entity(e['id'])
					# 			if ed is None:
					# 				# add institution
					# 				ed = self.add_institution(e)
					# 				# add position
					# 				if ed is not None:
					# 					self.add_ed_positition(user,ed,e)
					# 			else:
					# 				# add position
					# 				self.add_ed_position(user,ed,e)

					# process positions
					if 'values' in c['positions']:
						for p in c['positions']['values']:

							# some LinkedIn positions do not have a company id value
							if 'id' in p['company']:
								# check to see if new company
								co = self.get_company(p['company']['id'])
								if co is None:
									# add new company
									co = self.add_company(p['company']['id'])
									# if it's a new company, position must be new as well
									if co is not None:
										self.add_position(user,co,p)
								else:
									# TODO update company
									pos = self.get_position(user,co,p)
									if update == True and pos is None:
										self.add_position(user,co,p)
									elif update == True:
										self.update_position(pos,p)
									else:
										self.add_position(user,co,p)
				else:
					self.add_connection(self.focal_user,user)

	def mark_as_scanning(self,acct_id):
		self.acct.scanning_now = True
		self.acct.save()

	def record_scan(self,acct_id):
		acct = Account.objects.get(pk=acct_id)
		acct.last_scanned = datetime.now()
		acct.scanning_now = False
		acct.save()

	def handle(self,*args, **options):
		# assign global variables
		self.acct_id = options['acct_id']
		self.acct = Account.objects.get(pk=self.acct_id)
		self.focal_user = User.objects.get(pk=options['user_id'])
		# run main process
		self.mark_as_scanning(options['acct_id'])
		self.process_connections(options['user_id'],options["acct_id"])
		self.record_scan(options['acct_id'])