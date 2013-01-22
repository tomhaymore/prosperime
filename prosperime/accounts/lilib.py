# from Python
import oauth2 as oauth
import cgi
from datetime import datetime, time
import urllib
import urllib2
import os
import re
from math import ceil
from optparse import make_option
import urlparse
from bs4 import BeautifulSoup
# from _retry import retry
from utilities.helpers import retry
import dateutil

# from Django
from django.utils import simplejson
from django.contrib.auth.models import User
from accounts.models import Account, Profile, Connection, Picture
from entities.models import Position, Entity, Image, Industry, Office
from django.core.files import File
from django.conf import settings



class LIBase():

	# LinkedIn API credentials
	linkedin_key = '8yb72i9g4zhm'
	linkedin_secret = 'rp6ac7dUxsvJjQpS'

	# components for LI API
	co_fields = "(id,name,universal-name,company-type,ticker,website-url,industries,status,logo-url,blog-rss-url,twitter-id,employee-count-range,locations:(description,address:(street1,street2,city,state,country-code,postal-code)),description,stock-exchange)"
	co_api_url = "http://api.linkedin.com/v1/companies/"

	# initialize variable for account
	acct = None

	def get_access_token(self,acct_id=None):

		if self.acct is None:
			# get account
			self.acct = Account.objects.get(pk=acct_id,service="linkedin")

		# check to make sure token is current; if not, re-authorize
		if self.acct.expires_on <= datetime.now():
			# set expired flag to true
			self.acct.status = "expired"
			self.acct.save()
			# need to raise exception here
			# TODO refresh token
		elif self.acct.status == "expired":
			pass
			# need to raise exception here
			# TODO refresh token

		# assign token to dictionary
		access_token = {
			'oauth_token_secret':self.acct.token_secret,
			'oauth_token':self.acct.access_token,
			'last_scanned':self.acct.last_scanned
		}

		return access_token

	def fetch_data_oauth(self,acct_id,api_url):

		if self.acct is None:
			# get account
			self.acct = Account.objects.get(pk=acct_id,service="linkedin")

		# get oauth credentials from account
		access_token = self.get_access_token(self.acct.id)

		# construct oauth client
		consumer = oauth.Consumer(self.linkedin_key, self.linkedin_secret)
 
		token = oauth.Token(
			key=access_token['oauth_token'], 
			secret=access_token['oauth_token_secret'])

		client = oauth.Client(consumer, token)

		# construct api url 
		if access_token['last_scanned']:
			unix_time = access_token['last_scanned'].strftime("%s") # convert datetime to unix timestamp
			api_url = api_url + "&modified-since=%s" % (unix_time,)
		else:
			api_url = api_url

		# self.stdout.write(api_url)

		resp, content = client.request(api_url)
		
		# convert connections to JSON
		content = simplejson.loads(content)

		return content

	def get_company(self,id=None,name=None):
		co = None
		if id:
			try:
				co = Entity.objects.get(li_uniq_id=id)
			except:
				# if company doesn't exist, return None
				return None
		elif name:
			try:
				co = Entity.objects.get(li_univ_name=id)
			except:
				# if company doesn't exist, return None
				return None
		# return company
		return co

	def add_company(self,id=None,name=None):
		# get company profile from LinkedIn
		if name is not None:
			data = self.fetch_co_li_profile(name=name)
		elif id is not None:
			data = self.fetch_co_li_profile(co_id=id)
		# if nothing returned from LI, return None
		if data is None:
			# TODO add company
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
		if 'websiteUrl' in data:
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

	def fetch_co_li_profile(self,co_id=None,name=None):
		"""
		returns raw data of company profile from LI api
		"""
		# construct api url 
		if name:
			co_api_url = self.co_api_url + "universal-name=" + str(name) + ":"  + self.co_fields + "?format=json"
		else:
			co_api_url = self.co_api_url + str(co_id) + ":"  + self.co_fields + "?format=json"

		print co_api_url

		content = self.fetch_data_oauth(self.acct.id,co_api_url)

		# check for erros
		if 'errorCode' in content:
			return None
		return content

	def get_industry(self,name,code):
		"""
		tries to find, and return, matching industry from local db based on LI params
		"""
		try:
			industry = Industry.objects.get(Q(name=name) | Q(li_code=code))
		except:
			# no such industry, return None
			return None
		# return industry object
		return industry

	def save_li_image(self,co,img_url):
		"""
		fetches LI image, saves locally
		"""
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

		officeValues = {'description':'description','is-hq':'isHeadquarters'}
		# check to see if there is a description for the office
		if 'description' in office:
			o.description = office['description']
		# check to see if the office has an headquarters value
		if 'isHeadquarters' in office:
			o.is_hq = office['isHeadquarters']
		
		addressValues = {'addr_1':'street1','addr_2':'street2','city':'city','state_code':'state','postal_code':'postalCode','country_code':'countryCode'}
		# check to see if there is an address value
		if 'address' in office:
			for k,v in addressValues.iteritems(): 
				if v in office['address']:
					setattr(o,k,office['address'][v])
		# relate back to company
		o.entity = co
		o.save()

	def add_position(self,user,co,data):
		# dectionary of values to test for and then add if present
		positionValues = {'title':'title','description':'summary','current':'isCurrent'}
		
		pos = Position()
		pos.entity = co
		pos.person = user

		for k,v in positionValues.iteritems():
			if v in data:
				setattr(pos,k,data[v])
		
		# check for start date
		if 'startDate' in data:
			pos.start_date = self.format_dates(data['startDate'])
		# check for end date
		if 'endDate' in data:
			pos.end_date = self.format_dates(data['endDate'])
		pos.save()

	def get_position(self,user,co,data,**kwargs):
		if kwargs.get('type') == 'ed':
			pos = Position.objects.filter(entity=co,person=user,degree=data['degree'])
		else:
			pos = Position.objects.filter(entity=co,person=user,title=data['title'])
		if pos:
			# if position exists, return it
			return pos
		# new position, return None
		return None

	def update_position(self,user,co,data):
		# selets po
		try:
			pos = Position.objects.get(entity=co,person=user,title=data['title'])
		except:
			return None
		pos.summary = data['headline']
		pos.description = data['summary']
		pos.start_date = data['startDate']
		pos.end_date = data['endDate']
		pos.current = data['isCurrent']
		pos.save()

		return pos

	def get_institution(self,name=None,type="school"):
		try:
			school = Entity.objects.get(li_type="school",name=name)			
		except:
			return None
		# return school
		return school

	def add_institution(self,data):
		ed = Entity()
		ed.name = data['inst_name']
		# ed.li_uniq_id = data['inst_uniq_id']
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
		if 'degree' in data:
			pos.degree = data['degree']
		if 'fieldOfStudy' in data:
			pos.field = data['fieldOfStudy']
		
		# check for start date
		if 'startDate' in data:
			pos.start_date = self.format_dates(data['startDate'])
		# check for end date
		if 'endDate' in data:
			pos.end_date = self.format_dates(data['endDate'])
		
		pos.save()

	def format_dates(self,date):
		"""
		converts string to Python datetime object according to structure of string
		"""
		if date is None:
			return None

		if 'month' in date:
			formatted_date = datetime.strptime(str(date['month'])+"/"+str(date['year']),"%m/%Y")
		elif 'year' in date:
			formatted_date = datetime.strptime(str(date['year']),"%Y")
		else:
			# start date comes from public profile, in Y-m-d format
			try:
				formatted_date = datetime.strptime(date,"%Y-%m-%d")
			except:
				formatted_date = dateutil.parser.parse(date)
		return formatted_date

	def add_profile_pic(self,user,img_url):
		"""
		fetches LI profile pic and uploads to db
		"""
		img = None
		
		img_filename = user.profile.std_name() + ".jpg"
		
		try:
			img = urllib2.urlopen(img_url)
		except urllib2.HTTPError, e:
			self.stdout.write(str(e.code))
		if img:
			pic = Picture()
			pic.person = user.profile
			pic.source = 'linkedin'
			pic.description = 'linkedin profile pic'
			pic.save()
			with open('tmp_img','wb') as f:
				f.write(img.read())
			with open('tmp_img','r') as f:
				img_file = File(f)
				pic.pic.save(img_filename,img_file,True)
			os.remove('tmp_img')

	def mark_as_scanning(self):
		"""
		marks account as currently being last_scanned
		"""
		# set scanning to true
		self.acct.scanning_now = True
		# save changes
		self.acct.save()

	def record_scan(self):
		"""
		marks account scan as finished, records time
		"""
		# finish scan and record time
		self.acct.last_scanned = datetime.now()
		self.acct.scanning_now = False
		# save changes
		self.acct.save()

class LIProfile(LIBase):
	
	# set scope
	scope = 'r_fullprofile+r_emailaddress+r_network'
	# set callback
	# callback = 'http://127.0.0.1:8000/account/authenticate/'
	callback = settings.LI_CALLBACK

	# set urls
	request_token_url	= 'https://api.linkedin.com/uas/oauth/requestToken'
	authorize_url		= 'https://www.linkedin.com/uas/oauth/authenticate'
	access_token_url = 'https://api.linkedin.com/uas/oauth/accessToken'

	consumer = oauth.Consumer(LIBase.linkedin_key, LIBase.linkedin_secret)

	user = None
	acct = None

	def authorize(self):
		# setup OAuth
		consumer = oauth.Consumer(self.linkedin_key, self.linkedin_secret)
		client = oauth.Client(consumer)

		# scope = urllib.urlencode({'scope':'r_fullprofile+r_emailaddress+r_network'})
		# request_token_url = "%s?%s" % (self.request_token_url, scope,)

		request_token_url = "%s?scope=%s" % (self.request_token_url, self.scope,)
		print request_token_url
		# get request token
		resp, content = client.request(self.request_token_url,"POST",body=urllib.urlencode({'oauth_callback':self.callback,'scope':'r_fullprofile r_emailaddress r_network'}))
		# resp, content = client.request(self.request_token_url,"POST")
		if resp['status'] != '200':
			raise Exception(content)

		request_token = dict(cgi.parse_qsl(content))

		print request_token
		redirect_url = "%s?oauth_token=%s" % (self.authorize_url, request_token['oauth_token'], )

		return (redirect_url, request_token,)

	def authenticate(self,request_token,oauth_verifier):
		# construct oauth client
		

		token = oauth.Token(request_token['oauth_token'],request_token['oauth_token_secret'])
		token.set_verifier(oauth_verifier)
		client = oauth.Client(self.consumer, token)

		resp, content = client.request(self.access_token_url, "POST")

		access_token = dict(cgi.parse_qsl(content))
		
		# print access_token
		
		fields = "(headline,id,first-name,last-name,picture-url)"

		api_url = "http://api.linkedin.com/v1/people/~:" + fields + "?format=json"
		 
		token = oauth.Token(
			key=access_token['oauth_token'], 
			secret=access_token['oauth_token_secret'])

		client = oauth.Client(self.consumer, token)

		resp, content = client.request(api_url)

		return (access_token,simplejson.loads(content),)

	def process_profile(self,user_id=None,acct_id=None):

		# get user and account objects
		if user_id is not None:
			self.user = User.objects.get(pk=user_id)
			self.acct = Account.objects.get(owner=self.user,service="linkedin")
		elif acct_id is not None:
			self.acct = Account.objects.get(pk=acct_id,service="linkedin")
			self.user = self.acct.owner

		# fetch profile data from LinkedIn
		profile = self.fetch_profile()

		# make sure positions are present
		if 'positions' in profile:
			for p in profile['positions']['values']:
				# some LinkedIn positions do not have a company id value
				if 'id' in p['company']:
					# check to see if new company
					co = self.get_company(id=p['company']['id'])
					if co is None:
						# add new company
						co = self.add_company(id=p['company']['id'])
						# if it's a new company, position must be new as well
						if co is not None:
							self.add_position(self.user,co,p)
					else:
						# TODO update company
						pos = self.get_position(self.user,co,p)
						if pos is None:
							self.add_position(self.user,co,p)
		if 'educations' in profile:
			for e in profile['educations']['values']:
				inst = self.get_institution(name=p['schoolName'])
				if inst is None:
					# add new company
					inst = self.add_institution(p)
					# if it's a new company, position must be new as well
					if inst is not None:
						self.add_position(self.user,inst,p)
				else:
					# TODO update company
					pos = self.get_position(self.user,inst,p)
					if pos is None:
						self.add_ed_position(self.user,inst,p)

	def fetch_profile(self):

		# set fields to fetch from API
		fields = "(headline,id,first-name,last-name,picture-url,positions:(start-date,end-date,title,is-current,summary,company:(id)),public-profile-url),educations:(school-name,field-of-study,degree,start-date,end-date))"
		
		# construct url
		api_url = "http://api.linkedin.com/v1/people/id=%s:%s?format=json" % (self.acct.uniq_id,fields,)
		 
		# ready oauth client
		token = oauth.Token(
			key=self.acct.access_token, 
			secret=self.acct.token_secret)

		client = oauth.Client(self.consumer, token)

		resp, content = client.request(api_url)

		return simplejson.loads(content)

	# def add_profile_pic(self,user,url):
	# 	img = None
	# 	img_ext = urlparse.urlparse(img_url).path.split('/')[-1].split('.')[1]
	# 	img_filename = user.profile.std_name() + "." + img_ext
	# 	try:
	# 		img = urllib2.urlopen(img_url)
	# 	except urllib2.HTTPError, e:
	# 		self.stdout.write(str(e.code))
	# 	if img:
	# 		pic = Picture()
	# 		pic.person = user.profile
	# 		pic.source = 'linkedin'
	# 		pic.description = 'linkedin profile pic'
	# 		pic.save()
	# 		with open('tmp_img','wb') as f:
	# 			f.write(img.read())
	# 		with open('tmp_img','r') as f:
	# 			img_file = File(f)
	# 			pic.pic.save(img_filename,img_file,True)
	# 		os.remove('tmp_img')

class LIConnections(LIBase):

	# fields from connections API
	fields = "(id,picture-url,headline,first-name,last-name,positions:(start-date,end-date,title,is-current,summary,company:(id)),public-profile-url)"

	# construct api url
	api_url = "http://api.linkedin.com/v1/people/~/connections:" + fields + "?format=json"

	def __init__(self,user_id,acct_id):
		self.user = User.objects.get(pk=user_id)
		self.acct = Account.objects.get(pk=acct_id)

	def process_connections(self):
		"""
		Fetches LI connections, runs through each, adds new users, creates connections, and process connections' profiles
		"""

		# get connections
		connections = self.get_connections()

		# loop through connections
		for c in connections:

			# check to see if new user based on LI uniq id
			try:
				user = User.objects.get(account__uniq_id=c['id'],account__service="linkedin")
			except:
				user = None
			# check to see if privacy settings prohibit getting any useful information
			if c['firstName'] == 'private' and c['lastName'] == 'private':
				pass
			else:
				
				if user is None:					
					# add new dormant user
					user = self.add_dormant_user(c)
					self.add_connection(self.user,user)
				
				# process positions from API
				if 'values' in c['positions']:
					for p in c['positions']['values']:

						# some LinkedIn positions do not have a company id value
						if 'id' in p['company']:
							# check to see if new company
							co = self.get_company(id=p['company']['id'])
							if co is None:
								# add new company
								co = self.add_company(id=p['company']['id'])
								# if it's a new company, position must be new as well
								if co is not None:
									self.add_position(user,co,p)
							else:
								# TODO update company
								pos = self.get_position(user,co,p)
								if pos is None:
									self.add_position(user,co,p)
								# else:
								# 	self.add_position(user,co,p)
				# process public profile page
				if 'publicProfileUrl' in c:
					self.process_public_page(user,c['publicProfileUrl'])
				
				self.add_connection(self.user,user)

	def get_connections(self,start=0):
		
		# fetch connections data		
		content = self.fetch_data_oauth(self.acct.id,self.api_url)
		print content

		# parse out connections from returned data
		connections = content['values']

		# get count to check for pagination
		total_count = int(content['_total'])

		# check fo pagination
		if total_count > 500:
			# need to paginate
			pages = ceil((total_count - 500)/ 500)
			
			for i in range(1,pages+1):
				# construct url with pagination
				start_num = i*500+1
				page_api_url = api_url + "start=%i&count=500" % (start_num,)
				
				# fetch data with new count
				content = self.fetch_data_oauth(self.acct.id,page_api_url)

				# append additional connections
				connections.append(content['values'])

		return connections

	def add_dormant_user(self,user_info):

		# compile temporary user name
		temp_username = user_info['firstName'] + user_info['lastName'] + user_info['id']
		temp_username = temp_username[:30]
		
		# create dormant user account
		user = User()
		user.username = temp_username
		user.is_active = False
		user.save()

		# create user profile
		user.profile.first_name = user_info['firstName']
		user.profile.last_name = user_info['lastName']
		if 'headline' in user_info:
			user.profile.headline = user_info['headline']		
		user.profile.status = "dormant"
		user.profile.save()

		# add pofile picture
		if 'pictureUrl' in user_info:
			self.add_profile_pic(user,user_info['pictureUrl'])

		# create LinkedIn account
		acct = Account()
		acct.owner = user
		acct.service = 'linkedin'
		acct.uniq_id = user_info['id']
		if 'publicProfileUrl' in user_info:
			acct.public_url = user_info['publicProfileUrl']
		acct.status = "unlinked"
		acct.save()

		return user

	def add_profile_pic(self,user,img_url):
		"""
		fetches LI profile pic and uploads to db
		"""
		img = None
		
		img_filename = user.profile.std_name() + ".jpg"
		
		try:
			img = urllib2.urlopen(img_url)
		except urllib2.HTTPError, e:
			self.stdout.write(str(e.code))
		if img:
			pic = Picture()
			pic.person = user.profile
			pic.source = 'linkedin'
			pic.description = 'linkedin profile pic'
			pic.save()
			with open('tmp_img','wb') as f:
				f.write(img.read())
			with open('tmp_img','r') as f:
				img_file = File(f)
				pic.pic.save(img_filename,img_file,True)
			os.remove('tmp_img')

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

	def process_public_page(self,user,url):
		# fetch html and soup it
		
		# html = self.get_public_page(url)
		html = urllib2.urlopen(url)
		soup = BeautifulSoup(html)

		# get all profile container divs
		divs = soup.find_all("div","section",id=re.compile("^profile"))

		# loop throuh each div
		for d in divs:
			# identify type
			if d['id'] == 'profile-experience':
				# extract position data
				positions = self.extract_pos_from_public_page(d)
				for p in positions:
					# check to see if a co uniq was returned
					if p['co_uniq_name'] is not None:
						# check to see if new company
						co = self.get_company(name=p['co_uniq_name'])
						if co is None:
							# add new company
							co = self.add_company(name=p['co_uniq_name'])
							# if it's a new company, position must be new as well
							if co is not None:
								self.add_position(user,co,p)
						else:
							pos = self.get_position(user,co,p)
							if pos is None:
								self.add_position(user,co,p)
							
			elif d['id'] == 'profile-education':
				ed_positions = self.extract_ed_pos_from_public_page(d)
				for p in ed_positions:
					# check to see if new company
					inst = self.get_institution(name=p['inst_name'])
					if inst is None:
						# add new company
						inst = self.add_institution(p)
						# if it's a new company, position must be new as well
						if inst is not None:
							self.add_position(user,inst,p)
					else:
						# TODO update company
						pos = self.get_position(user,inst,p,type="ed")
						if pos is None:
							self.add_ed_position(user,inst,p)

	def extract_pos_from_public_page(self,data):
		# initialize positions array
		positions = []
		# get all position divs
		raw_positions = data.find_all("div","position")
		# loop through each position
		for p in raw_positions:
			# get title of position
			title = p.find("div","postitle").span.contents[0]
			# get unique name of company
			co_uniq_name = p.find("a","company-profile-public")
			if co_uniq_name:
				co_uniq_name = co_uniq_name.get('href')
				m = re.search("(?<=\/company\/)([\w-]*)",co_uniq_name)
				co_uniq_name = m.group(0).strip()
				print co_uniq_name
				# get start and end dates
				start_date = p.find("abbr","dtstart")
				if start_date is not None:
					start_date = start_date.get('title')
				try:
					end_date = p.find('abbr','dtstamp').get('title')
					current = True
				except:
					current = False

				try:
					end_date = p.find("abbr","dtend").get("title")
				except:
					end_date = None
				# get descriptions
				try:
					descr = p.find("p","description").contents[0]
				except:
					descr = None
				# append to main positions array
				positions.append({'title':title,'co_uniq_name':co_uniq_name,'startDate':start_date,'endDate':end_date,'summary':descr,'isCurrent':current})
		return positions

	def extract_ed_pos_from_public_page(self,data):
		# initialize positions array
		positions = []
		# get all position divs
		raw_positions = data.find_all("div","position")
		# loop through each position
		for p in raw_positions:
			inst_uniq_id = p.get('id')
			inst_name = p.h3.contents[0].strip()
			try:
				degree = p.find("span","degree").contents[0]
				
			except:
				degree = None
			try:
				major = p.find("span","major").contents[0]
			except:
				major = None
			positions.append({'inst_uniq_id':inst_uniq_id,'inst_name':inst_name,'degree':degree,'fieldofStudy':major})
		return positions



