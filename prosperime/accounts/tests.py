# from Django
from django.test import TestCase
from django.utils import unittest
from django.contrib.auth.models import User
from django.db.utils import IntegrityError

LI_CO_DATA = {u'industries': {u'_total': 1, u'values': [{u'code': u'6', u'name': u'Internet'}]}, u'status': {u'code': u'OPR', u'name': u'Operating'}, u'description': u'LinkedIn takes your professional network online, giving you access to people, jobs and opportunities like never before. Built upon trusted connections and relationships, LinkedIn has established the world\u2019s largest and most powerful professional network. Currently, more than 187 million professionals are on LinkedIn, including executives from all five hundred of the Fortune 500 companies, as well as a wide range of household names in technology, financial services, media, consumer packaged goods, entertainment, and numerous other industries. The company is publicly held and has a diversified business model with revenues coming from user subscriptions, advertising sales and hiring solutions.', u'twitterId': u'linkedin', u'locations': {u'_total': 4, u'values': [{u'description': u'', u'address': {u'postalCode': u'94043'}}, {u'description': u'Customer Service Office', u'address': {u'postalCode': u'68114'}}, {u'description': u'', u'address': {u'postalCode': u'02478'}}, {u'description': u'Post Montgomery Center', u'address': {u'postalCode': u'94104'}}]}, u'employeeCountRange': {u'code': u'G', u'name': u'1001-5000'}, u'websiteUrl': u'http://www.linkedin.com', u'logoUrl': u'http://m3.licdn.com/mpr/mpr/p/3/000/124/1a6/089a29a.png', u'stockExchange': {u'code': u'NYS', u'name': u'New York Stock Exchange'}, u'universalName': u'linkedin', u'ticker': u'LNKD', u'id': 1337, u'companyType': {u'code': u'C', u'name': u'Public Company'}, u'name': u'LinkedIn'}

class AuthTest(TestCase):
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

	# def test_dup_usernames(self):
	# 	# set flag to false
	# 	error_ocurred = False
	# 	# create new user with duplicate username
	# 	try:
	# 		result = User.objects.create_user(username="ahamilton",password="gwashington")
	# 	except IntegrityError:
	# 		error_ocurred = True
	# 	self.assertTrue(error_ocurred)

	def test_auth_form(self):
		# create new user
		default_user = User.objects.create_user(username="ahamilton",password="aburr")
		
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


		

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
