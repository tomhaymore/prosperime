# from Python
import oauth2 as oauth
import cgi
from datetime import datetime, time

# from Django
from django.utils import simplejson
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from accounts.models import Account, Profile
from entities.models import Position

# LinkedIn API credentials
linkedin_key = '8yb72i9g4zhm'
linkedin_secret = 'rp6ac7dUxsvJjQpS'

# fields from connections API
fields = "(headline,firstName,lastName)"

# construct api url
api_url = "http://api.linkedin.com/v1/people/~:" + fields + "?format=json"


class Command(BaseCommand):
	
	# include options for user id + account id

	option_list = BaseCommand.option_list + (
			# option for storing user id
			make_option('-u',
						action="store",
						type="integer",
						dest="user_id"),
			# option for storing acct id
			make_option('-a',
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

	def get_connections(self,acct_id):
		
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
		user = Account.objects.filter(uniq_id=user_id)
		if user:
			# user exists, return false
			return False
		# new user, return true
		return True

	def add_position(self,user,co,data):
		pos = Position()
		pos.entity = co
		pos.person = user
		pos.summary = data['headline']
		pos.description = data['summary']

	def is_new_position(self,user,data):
		pos = Position.objects.filter(entity=co,user=user,title=data['title'])
		if pos:
			return False
		return True

	def process_connections(self,user_id,acct_id):

		connections = self.get_connections(acct_id)

		# TODO: check for pagination

		# loop through connections
		for c in connections['values']:

			# check to see if new user
			user = self.get_user(c['id'])
			if user is False or (user is True and user.status == "dormant"):
				# flag for only updating positions
				if user:
					update = True
				else:
					# add dormant user
					user = self.add_dormant_user(c)
			
				for p in c['positions']['values']:

					# check to see if new company
					co = self.get_co(p['id'])
					if co is False:
						# add new company
						co = self.add_company(p)
						# if it's a new company, position must be new as well
						self.add_position(user,co,p)
					else:
						if self.is_new_position(user,co,data):
							self.add_position(user,co,data)

	def handle(self,*args, **options):

		# run main process
		self.process_connections(user=options['user_id'],acct=options["acct_id"])
	
	

	# make sure it only calls recently updated

