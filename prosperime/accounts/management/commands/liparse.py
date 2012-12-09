# from Python
import oauth2 as oauth
import cgi
from datetime import datetime, time
import urllib2
import os
from math import ceil

# from Django
from django.utils import simplejson
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from accounts.models import Account, Profile
from entities.models import Position, Entity, Image
from django.core.files import File

# LinkedIn API credentials
linkedin_key = '8yb72i9g4zhm'
linkedin_secret = 'rp6ac7dUxsvJjQpS'

# fields from connections API
fields = "(headline,firstName,lastName)"
co_fields = "(id,name,universal-name,company-type,ticker,website-url,industries,status,logo-url,blog-rss-url,twitter-id,employee-count-range,locations:(description,address:(postal-code)),description,stock-exchange)"

# construct api url
api_url = "http://api.linkedin.com/v1/people/~/connections:" + fields + "?format=json"
co_api_url = "http://api.linkedin.com/v1/companies/"

class Command(BaseCommand):
	
	acct_id = ''

	# include options for user id + account id

	option_list = BaseCommand.option_list + (
			# option for storing user id
			make_option('-u','user_id'
						action="store",
						type="integer",
						dest="user_id"),
			# option for storing acct id
			make_option('-a','acct_id'
						action="store",
						type="integer",
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
			# raise Exception
		elif acct.status == "expired":
			# need to raise exception here
			# raise Exception


		# assign token to dictionary
		access_token = {
			'oauth_token_secret' 	= acct.token_secret,
			'oauth_token'			= acct.access_token,
			'last_scanned'			= acct.last_scanned
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
		if access_token.last_scanned:
			unix_time = access_token['last_scanned'].strftime("%s") # convert datetime to unix timestamp
			api_url += "&modified-since=%s" % (unix_time,)

		resp, content = client.request(api_url)

		# convert connections to JSON
		content = simplejson.loads(content)

		connections = content['values']

		total_count = int(content['_total'])

		if total_count > 500:
			# need to paginate
			pages = ceil((total_count - 500)/ 500)
			
		for i in range(1,p+1):
			start_num = i*500+1
			page_api_url = api_url += "start=%i&count=500" % (start_num,)
			resp, content = client.request(api_url)

			# convert connections to JSON
			content = simplejson.loads(content)

			# append additional connections
			connections.append(content['values'])

		return content

	def add_dormant_user(self,user_info):

		# create dormant user account
		temp_username = user_info['firstName'] + user_info['lastName']
		user = User()
		user.username = temp_username
		user.status = "dormant"
		user.save()

		# create user profile
		user.profile.first_name = user_info['firstName']
		user.profile.last_name = user_info['lastName']
		user.profile.headline = user_info['headline']		
		user.save()

		# create LinkedIn account
		acct = Account()
		acct.owner = user
		acct.service = 'linkedin'
		acct.uniq_id = user_info['id']
		acct.status = "unlinked"
		acct.save()


	def get_user(self,user_id):
		user = Account.objects.get(uniq_id=user_id,service="linkedin")
		if user:
			# user exists, return co
			return user
		# new user, return None
		return None

	def add_position(self,user,co,data):
		pos = Position()
		pos.entity = co
		pos.person = user
		pos.title = data['title']
		pos.summary = data['headline']
		pos.description = data['summary']
		pos.start_date = data['start-date']
		pos.end_date = data['end-date']
		pos.current = data['is-current']
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

	def get_position(self,user,data):
		pos = Position.objects.filter(entity=co,user=user,title=data['title'])
		if pos:
			# if position exists, return it
			return pos
		# new position, return None
		return None

	def get_company(self,id):
		co = Entity.objects.get(li_uniq_id=id)
		if co:
			# co exists, return co
			return co
		# new co, return None
		return None

	def get_co_li_profile(self,co_id):
		# get oauth credentials from account
		access_token = self.get_access_token(acct_id)

		# construct oauth client
		consumer = oauth.Consumer(linkedin_key, linkedin_secret)
 
		token = oauth.Token(
			key=access_token['oauth_token'], 
			secret=access_token['oauth_token_secret'])

		client = oauth.Client(consumer, token)

		# construct api url 
		co_api_url += ":" + co_id + co_fields + "?format=json"

		resp, content = client.request(co_api_url)

		# convert connections to JSON
		content = simplejson.loads(content)

		return content

	def add_company(self,id):
		# get company profile from LinkedIn
		data = self.get_co_li_profile(id)

		# add to database
		co = Entity()
		co.type = 'organization'
		co.li_uniq_id = id
		co.li_univ_name = data['universalName']
		co.li_type = data['companyType']['code']
		co.ticker = data['ticker']
		co.web_url = data['websiteUrl']
		# co.domain = data['industries']
		# co.li_status = data['status']
		co.blog_url = data['blog-url']
		co.twitter_handle = data['twitterId']
		co.size_range = data['employeeCountRange']
		co.description = data['description']
		co.stock_exchange = data['stockExchange']['values'][0]['code']
		co.li_last_scanned = datetime.now()
		co.save()

		# add industries
		# TODO add manager that handles this any time domain is added to co
		for i in data['industries']['values']:
			# check to see if industry already exists
			industry = self.get_industry(Q(name=i['name'] | li_code=i['code']))
			if industry:
				# add industry to domain of company
				co.domain.add(industry)
			else:
				# create new industry
				industry = Industry()
				industry.name=i['name']
				industry.li_code=i['code']
				industry.save()
				# add to domain of company
				co.domain.add(industry)


		# get company logo
		save_li_image(co,data['logoUrl'])

		# add offices
		for l in data['locations']['values']:
			self.add_office(co,l)

	def save_li_image(self,co,img_url):
		# self.stdout.write("Adding image for " + entity.name().encode('utf8','ignore') + "\n")
		# img_url = "http://www.crunchbase.com/" + url
		# img_filename = urlparse(img_url).path.split('/')[-1]
		img = None
		img_ext = urlparse.urlparse(url).path.split('/')[-1].split('.')[1]
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
		o.description = office['description']
		o.is_hq = office['is-headquarters']
		o.addr_1 = office['address']['street1']
		o.addr_2 = office['address']['street2']
		o.city = office['address']['city']
		o.state_code = office['address']['state']
		o.postal_code = office['address']['postal-code']
		o.country_code = office['address']['country-code']
		o.save()

	def process_connections(self,user_id,acct_id):

		connections = self.get_connections(acct_id)

		# loop through connections
		for c in connections['values']:

			# check to see if new user
			user = self.get_user(c['id'])
			if user is None or (user is True and user.status == "dormant"):
				# flag for only updating positions
				if user:
					update = True
				else:
					# add dormant user
					user = self.add_dormant_user(c)
			
				for p in c['positions']['values']:

					# check to see if new company
					co = self.get_company(p['id'])
					if co is False:
						# add new company
						co = self.add_company(p['id'])
						# if it's a new company, position must be new as well
						self.add_position(user,co,p)
					else:
						# TODO update company
						pos = self.get_position(user,co,data)
						if update == True and pos is None:
							self.add_position(user,co,data)
						elif update == True:
							self.update_position(pos,data)
						else:
							self.add_position(user,co,data)

	def handle(self,*args, **options):
		# assign global variables
		acct_id = options['acct_id']
		# run main process
		self.process_connections(user=options['user_id'],acct=options["acct_id"])