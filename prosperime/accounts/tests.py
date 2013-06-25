# from prospere
from accounts.models import Account
# from Django
from django.test import TestCase
from django.utils import unittest
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.conf import settings
from django.utils.importlib import import_module

LI_CO_DATA = {u'industries': {u'_total': 1, u'values': [{u'code': u'6', u'name': u'Internet'}]}, u'status': {u'code': u'OPR', u'name': u'Operating'}, u'description': u'LinkedIn takes your professional network online, giving you access to people, jobs and opportunities like never before. Built upon trusted connections and relationships, LinkedIn has established the world\u2019s largest and most powerful professional network. Currently, more than 187 million professionals are on LinkedIn, including executives from all five hundred of the Fortune 500 companies, as well as a wide range of household names in technology, financial services, media, consumer packaged goods, entertainment, and numerous other industries. The company is publicly held and has a diversified business model with revenues coming from user subscriptions, advertising sales and hiring solutions.', u'twitterId': u'linkedin', u'locations': {u'_total': 4, u'values': [{u'description': u'', u'address': {u'postalCode': u'94043'}}, {u'description': u'Customer Service Office', u'address': {u'postalCode': u'68114'}}, {u'description': u'', u'address': {u'postalCode': u'02478'}}, {u'description': u'Post Montgomery Center', u'address': {u'postalCode': u'94104'}}]}, u'employeeCountRange': {u'code': u'G', u'name': u'1001-5000'}, u'websiteUrl': u'http://www.linkedin.com', u'logoUrl': u'http://m3.licdn.com/mpr/mpr/p/3/000/124/1a6/089a29a.png', u'stockExchange': {u'code': u'NYS', u'name': u'New York Stock Exchange'}, u'universalName': u'linkedin', u'ticker': u'LNKD', u'id': 1337, u'companyType': {u'code': u'C', u'name': u'Public Company'}, u'name': u'LinkedIn'}

class SessionTestCase(TestCase):
	# modifications for 
	def setUp(self):
		# http://code.djangoproject.com/ticket/10899
		settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
		engine = import_module(settings.SESSION_ENGINE)
		store = engine.SessionStore()
		store.save()
		self.session = store
		self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

class AuthTest(SessionTestCase):
	from django.test.client import Client
	# instantiate client
	c = Client()

	def test_standard_auth(self):
		# create new user
		default_user = User.objects.create_user(username="ahamilton",password="aburr")
		# test login 
		result = self.c.login(username=default_user.username,password=default_user.password)
		if result is not None:
			result = True
		self.assertEqual(result,True)

	def test_linkedin_auth(self):
		# create new user
		default_user = User.objects.create_user(username="ahamilton",password="aburr")
		# add LI info
		acct = Account(owner=default_user,service="linkedin",uniq_id="1e3r5y78i!")
		acct.save()
		# test auth
		result = self.c.login(acct_id=acct.uniq_id)
		if result is not None:
			result = True
		self.assertEqual(result,True)

	def test_auth_form(self):
		# create new user
		default_user = User.objects.create_user(username="ahamilton",password="aburr")
		# setup session variables
		s = self.session
		
		# init session variables
		s['linkedin_user_info'] = {
			'emailAddress': 'n/a'
		}
		s['access_token'] = -1
		s.save()

		# ensure that empty form is rejected
		resp = self.client.post('/account/finish/')
		self.assertEqual(resp.status_code,200)
		self.assertEqual(resp.context['form']['username'].errors,['This field is required.'])

		# ensure duplicate users are rejected
		resp = self.client.post('/account/finish',{'username':'ahamilton','email':'ahamilton@columbia.edu','password':'federalist','confirm_password':'federalist'})
		self.assertEqual(resp.status_code,200)
		self.assertEqual(resp.context['form']['username'].errors,['That username is already taken. Please choose another.'])

		# ensure that bad email gets rejected
		resp = self.client.post('/account/finish',{'username':'ahamilton','email':'truck'})
		self.assertEqual(resp.status_code,200)
		self.assertEqual(resp.context['form']['email'].errors,['Enter a valid e-mail address.'])

		# ensure passwords match
		resp = self.client.post('/account/finish',{'username':'ahamilaton','email':'ahamilton@colubmia.edu','password':'federalist','confirm_password':'anti-federalist'})
		self.assertEqual(resp.status_code,200)
		self.assertEqual(resp.context['form']['confirm_password'].errors,['Passwords must match. Please try re-entering your password.'])

		# ensure that terms / privacy policy must be checked
		resp = self.client.post('/account/finish',{'username':'troysmith','email':'troy@smith.com','password':'helen','confirm_password':'helen','terms':False})
		self.assertEqual(resp.status_code,200)
		self.assertEqual(resp.context['form']['terms'].errors,['You must agree to the Terms of Service and Privacy Policy to use Prospr.me.'])

	def test_reg_form(self):
		# create new user
		default_user = User.objects.create_user(username="ahamilton",password="aburr")

		# init session variables
		s = self.session
		s['linkedin_user_info'] = {
			'emailAddress': 'n/a'
		}
		s['access_token'] = -1
		s.save()
		# ensure that empty form is rejected
		resp = self.client.post('/account/finish/')
		self.assertEqual(resp.status_code,200)
		self.assertEqual(resp.context['form']['username'].errors,['This field is required.'])

	def test_login_form(self):
		# create new user
		default_user = User.objects.create_user(username="ahamilton",password="aburr")

		# ensure that empty form is rejected
		resp = self.client.post('/account/login')
		self.assertEqual(resp.status_code,200)
		self.assertEqual(resp.context['form']['username'].errors,['This field is required.'])

		# ensure that incorrect username gets rejected
		resp = self.client.post('/account/login',{'username':'ball','password':'aburr'})
		self.assertEqual(resp.status_code,200)
		self.assertEqual(resp.context['form'].errors['__all__'],['Please enter a correct username and password. Note that both fields are case-sensitive.'])

		# ensure that incorrect password gets rejected
		resp = self.client.post('/account/login',{'username':'ahamilton','password':'ball'})
		self.assertEqual(resp.status_code,200)
		self.assertEqual(resp.context['form'].errors['__all__'],['Please enter a correct username and password. Note that both fields are case-sensitive.'])

		# ensure that correct combination results in login
		resp = self.client.post('/account/login',{'username':'ahamilton','password':'aburr'},follow=True)
		self.assertEqual(resp.status_code,200) # redirects to home page
		self.assertEqual(resp.context['user'].is_authenticated(),True)

class LITest(SessionTestCase):
	import lilib 

	def test_unlinked_process_connections(self):
		# create new user
		default_user = User.objects.create_user(username="ahamilton",password="aburr")
		# add bogus LI account
		acct = Account(service="linkedin",status="unlinked",owner=default_user)
		acct.save()

		# ensure that lilib won't process connections
		li_cxn_parser = self.lilib.LIConnections(default_user.id,acct.id)
		res = li_cxn_parser.process_connections()
		self.assertEqual(res,"Error: LI accont is not active, aborting")

	def test_user_refused(self):
		# create new user
		default_user = User.objects.create_user(username="ahamilton",password="aburr")

		resp = self.client.get("/account/authenticate/?oauth_problem=user_refused",follow=True)
		self.assertEqual(resp.status_code,200) # 
		self.assertEqual(resp.redirect_chain[0][0],'http://testserver/account/refused')
