# from prosperme
from accounts.models import Account
from entities.models import Entity
from careers.models import Position, Career

# from Django
from django.test import TestCase
from django.utils import unittest
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.conf import settings
from django.utils.importlib import import_module
from django.core.exceptions import ObjectDoesNotExist


# from python
import datetime


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
			'id': 1234567,
			'emailAddress': 'n/a',
			'firstName': 'Alexander',
			'lastName': 'Hamilton',
			'headline': 'Postal'
		}
		s['access_token'] = {
			'oauth_token': 'monkey',
			'oauth_token_secret': 'pelvis',
			'oauth_authorization_expires_in': 123456789
		}
		s.save()
		
		# ensure that empty form is rejected
		resp = self.client.post('/account/finish/')
		self.assertEqual(resp.status_code,200)
		self.assertEqual(resp.context['form']['username'].errors,['This field is required.'])

		# check that log usernames / email are accepted
		resp = self.client.post('/account/finish/',{'username':'alexanderalexanderalexanderalexander@gmail.com','password':'pass1234','confirm_password':'pass1234','terms':True},follow=True)
		self.assertEqual(resp.status_code,200)
		self.assertEqual(resp.redirect_chain[0][0],'http://testserver/majors/')

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

class LITest(TestCase):

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

class LI2Test(SessionTestCase):
	import lilib

	API_clayton_profile = {
		u'firstName': u'Clayton', u'headline': u'Learning by Doing', u'lastName': u'Holz',
		u'educations': {u'_total': 1, u'values': [{u'startDate': {u'year': 2008}, u'endDate': {u'year': 2012}, u'fieldOfStudy': u'English, Focus: Literary Theory', u'degree': u'BA', u'schoolName': u'Stanford University'}]},
		u'pictureUrls': {u'_total': 1, u'values': [u'http://m.c.lnkd.licdn.com/mpr/mprx/0_fobGOEWIsqMHmkLuEVL2gwId4keoDnWuwdJ74wRLrldWoBRGdV6asSprDA1']},
		u'positions': {u'_total': 5, u'values':
			[{u'startDate': {u'year': 2008, u'month': 9}, u'company': {u'id': 1792}, u'title': u'Student', u'isCurrent': True, u'summary': u'Mayfield Fellow, Stanford Technology Ventures Program (2012-2013)'},
			 {u'startDate': {u'year': 2012, u'month': 9}, u'endDate': {u'year': 2012, u'month': 12}, u'title': u'Web Development Intern', u'company': {u'id': 227495}, u'summary': u"- Working with a team of 3 to build web applications using Kaazing's websocket product offering\n- Writing in Javascript/JQuery, Java for HTML5", u'isCurrent': False},
			 {u'startDate': {u'year': 2012, u'month': 6}, u'endDate': {u'year': 2012, u'month': 9}, u'title': u'Product Management Intern through the Mayfield Fellows Program', u'company': {}, u'summary': u'- Built out analytics platform using MixPanel: identified core metrics indicating product-market fit\n- Managed early customer development cycle: frequently interacted and received feedback from early users\n- Defined early brand presence through marketing material\n- Prototyped future iPad application based on extensive competitive research', u'isCurrent': False},
			 {u'startDate': {u'year': 2011, u'month': 1}, u'endDate': {u'year': 2011, u'month': 4}, u'title': u'Intern - la Fundaci\xf3n de la Innovaci\xf3n - Marketing', u'company': {u'id': 11697}, u'summary': u'', u'isCurrent': False},
			 {u'startDate': {u'year': 2010, u'month': 6}, u'endDate': {u'year': 2010, u'month': 8}, u'title': u'Marketing and Investment Intern', u'company': {u'id': 236925}, u'summary': u'', u'isCurrent': False}]},
		u'publicProfileUrl': u'http://www.linkedin.com/pub/clayton-holz/22/3b4/21a', u'id': u'MmD6vhOwE-'
	}

	API_monty_profile = {
		u'firstName': u'Ian', u'headline': u'Umm... at Chubbies Shorts', u'lastName': u'Montgomery',
		u'educations': {u'_total': 1, u'values': [{u'startDate': {u'year': 2008}, u'endDate': {u'year': 2012}, u'degree': u'B.S. Earth Systems', u'schoolName': u'Stanford University'}]},
		u'pictureUrls': {u'_total': 1, u'values': [u'http://m.c.lnkd.licdn.com/mpr/mprx/0_Gm1_3EtcYIiqkC6RbOtS3IOcRdDN_tERQSSaFI7U1puckP4vXYt75SdAber']},
		u'positions': {u'_total': 4, u'values': [
			{u'startDate': {u'year': 2013, u'month': 3}, u'company': {u'id': 2998025}, u'isCurrent': True, u'title': u'Designer'},
			{u'startDate': {u'year': 2011, u'month': 9}, u'endDate': {u'year': 2012, u'month': 6}, u'title': u'Student Advisor', u'company': {}, u'summary': u'Aided students with curriculum selection\nDesigned outreach materials\nCoordinated events to bring faculty and students together', u'isCurrent': False},
			{u'startDate': {u'year': 2011, u'month': 6}, u'endDate': {u'year': 2011, u'month': 8}, u'title': u'Data Logger/ Deckhand', u'company': {}, u'summary': u'Explored Black Sea aboard E/V Nautilus, ship of oceanographer Bob Ballard\nConducted sonar scans for ancient shipwrecks and undersea volcanoes\nCompiled dive reports, mapped findings using ArcGIS, communicated data to public', u'isCurrent': False},
			{u'startDate': {u'year': 2010, u'month': 6}, u'endDate': {u'year': 2010, u'month': 8}, u'title': u'Kayak Journalist', u'company': {}, u'summary': u'Dreamed up and implemented environmental journalism project\nKayaked from Monterey to San Diego interviewing scientists, fishermen\nAwarded Maverick Grant for Innovative Research in the American West', u'isCurrent': False}]},
		u'publicProfileUrl': u'http://www.linkedin.com/pub/ian-montgomery/64/a09/414', u'id': u'Z9zho4g9Cq'
	}
	
	def test_full_connections_parse(self):

		# All of my connections from get_connections(), 8/7
		clayton_cxns = [{u'lastName': u'A', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_OEI5XqRRXebSWEOsO2WVXnokXECGIE7sKa0VXBsRR2n-qaZVtuRWEcazobGjeSmn0WdUIrHM5XxS', u'id': u'Ulu9MR0uAV', u'firstName': u'Ashley', u'publicProfileUrl': u'http://www.linkedin.com/pub/ashley-a/1b/51/b78'}, {u'lastName': u'Abraham', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_527Sxefdqq0U6bhf5w0OxomWnreU6XrfFmU-xIuWWnywJ8F7doxTAw4bZjHk5iAikfSPKuY-WILQ', u'id': u'5Ms6P3G8o5', u'firstName': u'Claire', u'publicProfileUrl': u'http://www.linkedin.com/pub/claire-abraham/54/377/871'}, {u'lastName': u'Adam', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_tK6jMz1DO8TljlUfrtcaMnTmy_kxjqUfK--CMBig_LK7GKu7On9AccBPtmX8Y1siPPXinrAn-vcr', u'id': u'720kxy7d5N', u'firstName': u'Elizabeth', u'publicProfileUrl': u'http://www.linkedin.com/pub/elizabeth-adam/58/251/732'}, {u'lastName': u'Adaya', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_-HOmp-UZzNQCbCAitemjpKpLc-Nt53AiKfoAplgLHN8Cs56_YaaCtAdIJ0qS66rf1IpK19i61Jua', u'id': u'-ajtqw9cXZ', u'firstName': u'Tahira (Taida)', u'publicProfileUrl': u'http://www.linkedin.com/pub/tahira-taida-adaya/37/363/a58'}, {u'lastName': u'Adiseshan', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_zdfeRCmokXgY5fy3U7aUR3Szk3RKbdj3BHRcR3YoUXf8ZSoTMf0kvToXE7U7XapDqoDnqQ20k9Mg', u'id': u'uNPTPU5564', u'firstName': u'Tara', u'publicProfileUrl': u'http://www.linkedin.com/in/taraadiseshan'}, {u'lastName': u'Aguilar', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_OYjMBn9so8FmGEZpyySEBq59H3imCuJppVd6BqbFcbcYgHaytZDvJN1d62_l3w4r0g0bZPvm_jB0', u'id': u'9hfJwA6GmB', u'firstName': u'Gabriel', u'publicProfileUrl': u'http://www.linkedin.com/pub/gabriel-aguilar/34/8a6/917'}, {u'lastName': u'Amajoyi', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_ZSvRnLwe25dmIgIYVWtXnbwvuTD7WORYVuTknbWvPkJxns2Oqw5c4FjUCfSKoJVtMmBLMhcorPxM', u'id': u'eC9rFpc1hk', u'firstName': u'Chike', u'publicProfileUrl': u'http://www.linkedin.com/pub/chike-amajoyi/21/738/99b'}, {u'lastName': u'Amman', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_ByD7XFCcnWHmiiaVcp7pXkGNqf7O3QxVzUJrX58IIoUaOGesRsj_ELqLVTf3CTY9nxflIGtIPII5', u'id': u'FSnjpXFfiW', u'firstName': u'Taylor', u'publicProfileUrl': u'http://www.linkedin.com/pub/taylor-amman/25/292/36'}, {u'lastName': u'Amoils', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_T_Ic9YpuWF5zs7s1TTSX9pDCdX-ZsoI1i30e9pDY9C6e5mpPD5RRZyMKFdtbJDo088ddJU0wcmUy', u'id': u'LJO0BP3HOR', u'firstName': u'Maya', u'publicProfileUrl': u'http://www.linkedin.com/pub/maya-amoils/24/8b0/74b'}, {u'lastName': u'Anderson', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_Y5gdzlRtwiQCqmO-YQm9z-WlbhKinDO-pkWnz-ZCZLk1WWdt-_SLUt2uWmrpzo0OxQxcVvQTM7BE', u'id': u'vt6Xg3OBjA', u'firstName': u'Eric', u'publicProfileUrl': u'http://www.linkedin.com/pub/eric-anderson/2b/860/559'}, {u'lastName': u'Arnstein', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_hC1YLg7Ktfz4NnoqGQhSLOu-Y2rRq1UqC_F3L0ShTdXIIBuNukitwxJaKCKXBqs43TA8oZx12Yx9', u'id': u'nI5Vvp5Dfr', u'firstName': u'Ben', u'publicProfileUrl': u'http://www.linkedin.com/pub/ben-arnstein/38/16b/314'}, {u'lastName': u'Aroeste', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_WfMGODeoBtYRd3lhw7ZlO7WLc1JIwChhIHSgOmI9HrDRN6c8LdWaKax4JUMqH532e2UpAdJj0Tpi', u'id': u'TIU8BOueKE', u'firstName': u'Alberto', u'publicProfileUrl': u'http://www.linkedin.com/pub/alberto-aroeste/26/591/931'}, {u'lastName': u'Averbuch', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_9NypJGTgM8Hpt6WCZKViJ8h3MhUAt_MCNPe_J8lTQQ73SFmGsturBhL7BDRaAkZmcBYG9F_3nLuA', u'id': u'_jR952izdl', u'firstName': u'Shira', u'publicProfileUrl': u'http://www.linkedin.com/pub/shira-averbuch/53/a9a/a69'}, {u'lastName': u'Avery', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_9fXpRTmIObY1wqdTnenfRiEbpkVjwBJTNHr_RiDsibaDN1a3sdqrv_MN-2sGHK4Sc26Gqk0uHTGe', u'id': u'hGABeOzfv6', u'firstName': u'Alex', u'publicProfileUrl': u'http://www.linkedin.com/pub/alex-avery/24/1a4/52a'}, {u'lastName': u'Awadallah', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_dtjoYmbjLvaWKW-3I1UvY2cP51REt2P3wrdvYDX3s9fsSekT5ND6rSKfwgUvAItDHl0qlEsgWEVK', u'id': u'DC-TpRbgI9', u'firstName': u'Amr', u'publicProfileUrl': u'http://www.linkedin.com/in/awadallah'}, {u'lastName': u'Badr-El-Din', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_WfMGODSdzAf6I3hhwDRgO7WkczJIwChhIaSgOmI9HrDRN6c8LdWaKax4JUMqH532e2UpAdznsbSi', u'id': u'm92ZRTpo4f', u'firstName': u'Leen', u'publicProfileUrl': u'http://www.linkedin.com/pub/leen-badr-el-din/31/a37/8b2'}, {u'lastName': u'Balassone', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_5P24ioAOIJJUye64FqYbiW8-IpuRKe94Ft4bie3aqsZI723ZdvpqSHvhLA2X17cqkKa62f09ElGP', u'id': u'nXBWJZwGVg', u'firstName': u'James', u'publicProfileUrl': u'http://www.linkedin.com/pub/james-balassone/46/456/a23'}, {u'lastName': u'Ballas', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_gnYAT9FjUgFSA_nVgv7CTvvPJZ_GlhFV0qEmTvn86OB-mkrsAKmjfzGmcvij-F69yvyfm-HAy-yC', u'id': u'QZJi6RohNt', u'firstName': u'Elie', u'publicProfileUrl': u'http://www.linkedin.com/pub/elie-ballas/24/211/95'}, {u'lastName': u'Barboza', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_9G8uJTfpx8SSc9OGNC_0Jip0P6VjzvOGNLN1JiSauLaDoAdCsXK8B_JhgmsGnt0ac3Ct9kxPJEyx', u'id': u'Khs94k5gz6', u'firstName': u'Cynthia', u'publicProfileUrl': u'http://www.linkedin.com/pub/cynthia-barboza/11/9a8/8ab'}, {u'lastName': u'Barnett', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_8LXTPsaCKnbBMqTxGhL-P4mTK9_nUBhxCTrOPJYy7KBQk1c02iqSjMotYRiW4K3PT66xyY8M-H5q', u'id': u'BtfKEoloo3', u'firstName': u'Connor', u'publicProfileUrl': u'http://www.linkedin.com/in/connorbarnett'}, {u'lastName': u'Barry', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_T8jL9V03HkFVzfmxTCSV9Z0lXX_4cumxibds9Mu3RCBHHHM0DQDdZJ4fodiFNw7P8_0RJOY6qrs3', u'id': u'Qpk0YY74sN', u'firstName': u'Evan', u'publicProfileUrl': u'http://www.linkedin.com/pub/evan-barry/27/a46/a75'}, {u'lastName': u'Basilico', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_UQF0ZCZ2O6e2MzM3zC9uZhUCOQUGRn43JT18Zhsj357-X-fTc8c198a1raRjZlJDs5L3BbkPJ2BR', u'id': u'cJuwalH2Dq', u'firstName': u'Simon', u'publicProfileUrl': u'http://www.linkedin.com/pub/simon-basilico/31/481/718'}, {u'lastName': u'Baumbach', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_JqFQXFzu_DHGgMxVJrbzXkXi_df80VaVRK1JXkqYy7RKhYJsv-cEEX8KSX7xyjf94cLZIioLmPmR', u'id': u'mlgu_iAHug', u'firstName': u'Bret', u'publicProfileUrl': u'http://www.linkedin.com/pub/bret-baumbach/51/37b/76a'}, {u'lastName': u'Bennett-Smith', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_eOkdZaGLh_fWfyO3eV99ZSq5GQRd7sO3o0KnZSXJj5fJKOdTX4NL9DKc2aU92g0DWjQcBosxdJn5', u'id': u'U9DeWtK_X8', u'firstName': u'Miles', u'publicProfileUrl': u'http://www.linkedin.com/pub/miles-bennett-smith/69/774/140'}, {u'lastName': u'Bergstedt', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_vJv4J_hLS8pPTjoCRYzIJh-WDhRASYVCcOTbJ3A9-Qf3tVDGJ05qBT54iDUaaMRmNVB69QfNN7CG', u'id': u'aF3HU6SNni', u'firstName': u'Shannon', u'publicProfileUrl': u'http://www.linkedin.com/in/sbergstedt'}, {u'lastName': u'Binnie', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_3Puunx3mz5qMKh0ti-p1np8avGlJK5YticZ1npCaEk5d73W-Svy84y9hUfA61CxYhKmtMUptS3oh', u'id': u'1sEbZ2jvyv', u'firstName': u'Alexander', u'publicProfileUrl': u'http://www.linkedin.com/pub/alexander-binnie/24/667/7b9'}, {u'lastName': u'Blue', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_IdV5b2xLbfRbWeY9dmy9b7UkbmxLImf9dHaVb7ZBZSwzqo4nbfoWdf2MW60VeWaVoo4UeHQk3JcO', u'id': u'ynNeZJCDA7', u'firstName': u'Kyler', u'publicProfileUrl': u'http://www.linkedin.com/pub/kyler-blue/76/880/7a5'}, {u'lastName': u'Boeri', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_FIUn3WOwo4UvHSLRLERW3IaIojSveSkRLW7d3oxczOM5BdPUwDws7EIJXvDEIE5c6HMeaSSOAyt9', u'id': u'PCQPGBlGOA', u'firstName': u'Anna', u'publicProfileUrl': u'http://www.linkedin.com/in/annaboeri'}, {u'lastName': u'Bollaidlaw', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_mLnj-OHi0t5IR9BKmFba-yU701tLRPBKuXCC-gZlhvQzXc8rGiQAyj2xAO-VZNny76NijVQ6hxiE', u'id': u'FxD06gudO9', u'firstName': u'Alie', u'publicProfileUrl': u'http://www.linkedin.com/pub/alie-bollaidlaw/11/822/856'}, {u'lastName': u'Breslow', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_DBwsjZ5GH1rd0HLDfrZLjVzuotb50wNDfnxLjVvYzqPvhf_STlUnPs3KXxFsyuv32NWk-gIp-eVO', u'id': u'baH3Qf3b3z', u'firstName': u'Ryan', u'publicProfileUrl': u'http://www.linkedin.com/in/rbres'}, {u'lastName': u'Bromberg', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_QoM0AHpQMzZNE3Lj6w08Awm5UtS9oCNjXIS8AE0vkqM6z6_go2W1xowUvxDdW5vAbdU3ODTsH5pc', u'id': u'wZxd7q5SAW', u'firstName': u'Andy', u'publicProfileUrl': u'http://www.linkedin.com/in/andybromberg'}, {u'lastName': u'Brown', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_MC0eb_4pkSD8nuynRi7cb3dOkmYDqfjnRhIcb3whUHEjIwo9zkfkdT0aE_O-BHpsZTjneQMG-eKR', u'id': u'SZ24F3lDZ7', u'firstName': u'Ryan', u'publicProfileUrl': u'http://www.linkedin.com/pub/ryan-brown/53/ba2/148'}, {u'lastName': u'Bruce', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_N-oHBblY5GR-1IypNrRcBXl_F3f00eypnnOBBXGO4bRfh2wy4qVXJknrd27hy7grvAH9Z_KzXyhy', u'id': u'DHzEvlpaV-', u'firstName': u'Jamie', u'publicProfileUrl': u'http://www.linkedin.com/pub/jamie-bruce/36/512/562'}, {u'lastName': u'Buehler', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_vrCZ-380m9otKy6rRBlI-_1xm10grsBrctnF-C8flvISfO8KJ9tNyGq38OxCPgnpN18QjL-Bx3Ut', u'id': u'mPtikWDtoU', u'firstName': u'Anna', u'publicProfileUrl': u'http://www.linkedin.com/pub/anna-buehler/40/309/a65'}, {u'lastName': u'Byrne', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_gxkFOABFfNlfmVrhgg_4OPN5izvm2VThxRKZOPFJpPTY1Yn8AMNIK1PcD4zl7j82yyQJAqMEhfwU', u'id': u'vPQALzOv4k', u'firstName': u'Stephanie', u'publicProfileUrl': u'http://www.linkedin.com/in/stephaniebyrne'}, {u'lastName': u'Caligiuri', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_OPQTE1ciP73iYPjky1BYEKcO1wcmyvukyNtOElFO2DiY_AUXtvnSXAPrjQBl0tSe0Kkx59JFqA3X', u'id': u'fL6Ok_cDNs', u'firstName': u'Marie', u'publicProfileUrl': u'http://www.linkedin.com/pub/marie-caligiuri/54/6ab/b76'}, {u'lastName': u'Calleja', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_sMe3tGzezvR_m5hAqOMtt866zzg826TA4YyYt8NJoPWK1Cnl9xZDphhcR4jx738jUsE0gFob24en', u'id': u'K7Bx6Yhxjw', u'firstName': u'Catherine', u'publicProfileUrl': u'http://www.linkedin.com/pub/catherine-calleja/7/1aa/ba8'}, {u'lastName': u'Campos', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_-OwaAzhXzKNaSFKjKRegAB1wcA3YfFKjKyxlABTZHBzmr_bgY4UGxcznJpTTuhlA1jWrOr1Y0ak7', u'id': u'CUvgf17VY0', u'firstName': u'Perla', u'publicProfileUrl': u'http://www.linkedin.com/pub/perla-campos/57/a68/a3'}, {u'lastName': u'Case', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_1C0R3ceOIUkyNWcUgQpk3NWjdY8yq7cUA6Ik3Nah94NuIIhRxkfc7qsaFPh_Be9B-TjLa1rmtAUa', u'id': u'hf8qMYRrAo', u'firstName': u'Annie', u'publicProfileUrl': u'http://www.linkedin.com/pub/annie-case/53/bb7/44'}, {u'lastName': u'Cerf', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_sMe3tiN5zvEmh5rAZsWtt8FWzzg826TA4RyYt8NJoPWK1Cnl9xZDphhcR4jx738jUsE0gFQR-HJn', u'id': u'aTRPsd_uMU', u'firstName': u'Jake', u'publicProfileUrl': u'http://www.linkedin.com/pub/jake-cerf/37/3bb/8a6'}, {u'lastName': u'Cha', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_FiVC9mfDvkUzR3D1W6Rj9DO_cXOJRCD15Taj92mlHCodX6VPwLomZuVxJdY6Z5206h4yJwp4yvCP', u'id': u'pA_HjeLuf3', u'firstName': u'Alicia', u'publicProfileUrl': u'http://www.linkedin.com/pub/alicia-cha/45/2a4/a73'}, {u'lastName': u'Chehabi', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_JqFQXF6O_msKjpaVBPqzXk-O_df80VaVU11JXkqYy7RKhYJsv-cEEX8KSX7xyjf94cLZIiEHI_ZR', u'id': u'2Rp56FU1uj', u'firstName': u'Omar', u'publicProfileUrl': u'http://www.linkedin.com/pub/omar-chehabi/46/b97/85'}, {u'lastName': u'Clapper', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_5P24iICOW0EntD94bBybiWAxIMuRKe94Ft4bie3aqsZI723ZdvpqSHvhLA2X17cqkKa62f0u-uqP', u'id': u'eUMH-y2ouq', u'firstName': u'Eric', u'publicProfileUrl': u'http://www.linkedin.com/in/ericclapper'}, {u'lastName': u'Cook', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_UiHHf6dhLUDTBIlHz6JRfkRuFMomUIrHMTpBf5Iy4sOYk7FecL4XTLxtdAEl42AXsho9hGzFiYll', u'id': u'EivznIQoTs', u'firstName': u'Brian', u'publicProfileUrl': u'http://www.linkedin.com/in/briancook5'}, {u'lastName': u'Cook', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_dtjoY7BjbAmEKWG3WK2MYDcY51REt2P3wvdvYDX3s9fsSekT5ND6rSKfwgUvAItDHl0qlEnRLW2K', u'id': u'-ArZ2rQw4r', u'firstName': u'Karissa', u'publicProfileUrl': u'http://www.linkedin.com/pub/karissa-cook/29/914/641'}, {u'lastName': u'culver', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_3Y7SZp_UqhTqCbgTT4mYZxPcn89JGXpTiVU-ZxGoW6Gdj8I3SZxT90nXZSn6TijShgSPB4pMROFi', u'id': u'dKgb4dKSKR', u'firstName': u'shaun', u'publicProfileUrl': u'http://www.linkedin.com/pub/shaun-culver/16/831/48'}, {u'lastName': u'Dar', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_XUxLRHlZFXjziDmD6ZYnRwPLb3Iq_mmDQywsRwr5ZG0XyoMSeg7dvIkwWWwIhW73LZgRq2GIL8Jj', u'id': u'4I0PL31t2f', u'firstName': u'Zavain', u'publicProfileUrl': u'http://www.linkedin.com/pub/zavain-dar/75/6a3/70a'}, {u'lastName': u'Davis', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_9NypJGKYJTOTY_4CNK27JTtxMhUAt_MCqve_J8lTQQ73SFmGsturBhL7BDRaAkZmcBYG9Ffw4ERA', u'id': u'DaIXyHTAPp', u'firstName': u'Victoria', u'publicProfileUrl': u'http://www.linkedin.com/in/victoriajdavis'}, {u'lastName': u'Dayton', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_WfMGO2UdcvSWIFhhw7RjOmE9c1JIwChhwaSgOmI9HrDRN6c8LdWaKax4JUMqH532e2UpAdJOGnWi', u'id': u'4X39Mkzipx', u'firstName': u'Nicole', u'publicProfileUrl': u'http://www.linkedin.com/pub/nicole-dayton/73/6b0/b20'}, {u'lastName': u'Delgado', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_FJCU17iUfBM5_xBtbZrk1DTvfrgzTV9tLUnX12tErnWLYY3-w0tBgu6k3jjoGjcY6V85pw8u8Jr7', u'id': u'p-wkD4faGD', u'firstName': u'Grant', u'publicProfileUrl': u'http://www.linkedin.com/pub/grant-delgado/2b/bb6/a02'}, {u'lastName': u'Dey, PhD, MBA', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_66VqguY-wBxVnDchXLRFgfR7INMBsmQhkFawgfy-qlSb5ol8Eho417HpLVJeJWb2FL4oteag6-df', u'id': u'gYcQya4OVP', u'firstName': u'Farouk', u'publicProfileUrl': u'http://www.linkedin.com/in/faroukdey'}, {u'lastName': u'Diaz', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_-KgZfK1rIsTllDBXrcsFf13pIxnOADBXrqWFf-83qJCaaW8kYnSNTtqfLt93tonH1PxQhv-4Ke2V', u'id': u'f_mApJuDqp', u'firstName': u'David', u'publicProfileUrl': u'http://www.linkedin.com/in/diazdavid'}, {u'lastName': u'Dillon', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_eMnW9EcWa_EdayfxHUr99H-IGXfLu00xoZC99HNqjFRzPUH0XxQ5ZehV2u7Vf4OPWsNBJ7QlTo1h', u'id': u'ZOYN3DAK5q', u'firstName': u'Natalie', u'publicProfileUrl': u'http://www.linkedin.com/pub/natalie-dillon/3b/114/946'}, {u'lastName': u'Dobbs', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_V24ZqXRHI_Hj6mwyVHZwqQdzI8aSoDUyZI2FqQEzq5VgzWupnoHNs6ORLamtWosKRfVQR3NjHriv', u'id': u'b8Md3xQhHS', u'firstName': u'Garrett', u'publicProfileUrl': u'http://www.linkedin.com/pub/garrett-dobbs/23/1b9/72a'}, {u'lastName': u'Dodson', u'id': u'1Bp4N-mva_', u'firstName': u'Jason', u'publicProfileUrl': u'http://www.linkedin.com/pub/jason-dodson/16/778/741'}, {u'lastName': u'Dolben', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_iWKW8pDkGYi6kyiq_als8YO9GOKnQ01qTIk98YYXjRkQMUXN7785aOoo2KrWL4-4GEtB7JuIXNfK', u'id': u'XuqaAKkAkR', u'firstName': u'Dave', u'publicProfileUrl': u'http://www.linkedin.com/pub/dave-dolben/2b/97/ab8'}, {u'lastName': u'Dru', u'id': u'vW0c83YfTw', u'firstName': u'Rebecca', u'publicProfileUrl': u'http://www.linkedin.com/pub/rebecca-dru/41/89a/128'}, {u'lastName': u'Dubie', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_bvDvUWc0HiDs-EJuLlgoUoKaHkHNKEduLcJoUoAmcTpk7aO2IPjMzE586oew1SH8QnfwNS_4YuRZ', u'id': u'NM23JqQn57', u'firstName': u'Jack', u'publicProfileUrl': u'http://www.linkedin.com/pub/jack-dubie/9/7bb/51'}, {u'lastName': u'Duckworth', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_I3Frdoo3gSy6ZvWHWihidWefxWoWZ9WHW617dWWj8uOMbtYebFcpbdj1lFEnRAeXoGLa6aUh1y4z', u'id': u'KRencOoTTd', u'firstName': u'Angela', u'publicProfileUrl': u'http://www.linkedin.com/pub/angela-duckworth/12/876/595'}, {u'lastName': u'Dunlevie', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_5KCgs7CyxhYsA9ICFtTmsDQp0XRUl9sCbBnGsD8uhFfwmtSGdntlqSqCAuUk-AUmkP8_vEY2HE9V', u'id': u'pB5L--x5AL', u'firstName': u'Robert', u'publicProfileUrl': u'http://www.linkedin.com/pub/robert-dunlevie/64/81/b74'}, {u'lastName': u'Durant', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_5KCgs73pgk0UAPICFc_Cs2lP0TRUl9sCF-nGsD8uhFfwmtSGdntlqSqCAuUk-AUmkP8_vEtTwt-V', u'id': u'qDhujUsFPf', u'firstName': u'Natalie', u'publicProfileUrl': u'http://www.linkedin.com/in/nataliedurant'}, {u'lastName': u'Elliott', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_WTL7meo7tMmIRzGIdhBpmoWa-yIwMzPIwLArmIoxDV0UQlkwLbz_hwYlplwNV-tFeCFlTuNDsGmi', u'id': u'QORaDdDN-2', u'firstName': u'Eric', u'publicProfileUrl': u'http://www.linkedin.com/pub/eric-elliott/49/421/149'}, {u'lastName': u'Ellis', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_DjKFeZ6nioN6CpgIfOlqeRXciubWCxSI7VkZeV5bp7PMgRswTR8I6sAWDXFn3ZuF2OtJbgR-SZCW', u'id': u'XI3pb7Vq_K', u'firstName': u'Austin "Gus"', u'publicProfileUrl': u'http://www.linkedin.com/pub/austin-%22gus%22-ellis/23/1b0/223'}, {u'lastName': u'Falc\xf3n', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_fDcXEjWF823QHsjXTH6UExVECanoeyuXSoiUEYWcgDCVB4Uk_IFHXOjJuQ9zIUSHaazV5JU1Ohv5', u'id': u'Eh2EWSsw_O', u'firstName': u'Carlos', u'publicProfileUrl': u'http://www.linkedin.com/pub/carlos-falc%C3%B3n/63/9b9/a7a'}, {u'lastName': u'Falk', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_I3FrdoZ7gaxMVvWHIb67dWE7xWoWZ9WHWh17dWWj8uOMbtYebFcpbdj1lFEnRAeXoGLa6aUBjGSz', u'id': u'ubrF8KyEvE', u'firstName': u'Allison', u'publicProfileUrl': u'http://www.linkedin.com/pub/allison-falk/23/561/697'}, {u'lastName': u'Fine', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_NArAmT-gpxHy-qBbnKtGmirTyJsxt-bb99XmmG_T_xm7SnKF4chjhCc7tqV8AzQwv--fT5lQJdgL', u'id': u'BmGT32MX2S', u'firstName': u'Jeremy', u'publicProfileUrl': u'http://www.linkedin.com/in/jrfine'}, {u'lastName': u'Fischman', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_bvDvUeGleiSJyEeuFqpQUo1tHFHNKEduLNJoUoAmcTpk7aO2IPjMzE586oew1SH8QnfwNSf_QvjZ', u'id': u'J7ObpAPsuQ', u'firstName': u'Victoria', u'publicProfileUrl': u'http://www.linkedin.com/in/victoriafischman'}, {u'lastName': u'private', u'id': u'private', u'firstName': u'private'}, {u'lastName': u'Fisher', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_W1fpi2njM04Xl65qFvaii750MMyIl5vqw-R_imF2QseRm3CNLz0rSaPGBApq-CN4erDG2dz8EsI2', u'id': u'E_j5rIDYa5', u'firstName': u'Jill', u'publicProfileUrl': u'http://www.linkedin.com/pub/jill-fisher/77/483/239'}, {u'lastName': u'Fisher', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_ndxXK8DRFv4hFm3-9ojBKGaNFqpKbm8-qawUKiY64AH8ZoBtVf7HO_oHdsy7XWTOBogVxk88I_Sd', u'id': u'x-GaRV9DYs', u'firstName': u'John', u'publicProfileUrl': u'http://www.linkedin.com/pub/john-fisher/37/901/862'}, {u'lastName': u'Flemings', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_FiVC9mjSvF2WUCj153El92ulcXOJRCD1Lbaj92mlHCodX6VPwLomZuVxJdY6Z5206h4yJwyzIWnP', u'id': u'3n-QwcL-Rd', u'firstName': u'Rey', u'publicProfileUrl': u'http://www.linkedin.com/in/reyflemings'}, {u'lastName': u'Fouts', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_tlYgplLrMP_l16n_rv2mp18AJlzxPhn_pzEGp-_i6c37ukTiOBmlttcDcyv8rFB7Pty_1vAuCo22', u'id': u'A6a7grk0rA', u'firstName': u'Matthew', u'publicProfileUrl': u'http://www.linkedin.com/in/matthewfouts'}, {u'lastName': u'Foxworth', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_mLnj-OMijt5bU9BK2ClC-gYu0ntLRPBK2XCC-gZlhvQzXc8rGiQAyj2xAO-VZNny76NijVQZgOQE', u'id': u'kRmdW-50et', u'firstName': u'Margaux', u'publicProfileUrl': u'http://www.linkedin.com/pub/margaux-foxworth/62/113/9b6'}, {u'lastName': u'Fredell', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_mB1VmUXx7MKW1VXwht-Lm4np7JQ5PxvwunF5m4v_KVtvuRCIGli9hZ3STl6srZNb7NAXTxIvO9XO', u'id': u'wfki0IyoBH', u'firstName': u'Anne', u'publicProfileUrl': u'http://www.linkedin.com/pub/anne-fredell/55/aab/560'}, {u'lastName': u'Friese', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_0hOv4P4lWh__9DW8gL0o4AorwQN29DW8gCoo4AdiNh8pdWYhP6aMnlgD5wq1voeuOipwcnUb79VW', u'id': u'3_PGzUWi2H', u'firstName': u'Mark', u'publicProfileUrl': u'http://www.linkedin.com/pub/mark-friese/23/4a8/724'}, {u'lastName': u'Fullerton', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_-FJjC-UuJjk-qhbcKG4mCKgTJ0A-4_Bcr_DCClpr6MLGFF8BY3dA2AeOc-lDUknR1XRiS9aRmHZB', u'id': u'pyYEtYxPbJ', u'firstName': u'Anastasia', u'publicProfileUrl': u'http://www.linkedin.com/pub/anastasia-fullerton/46/99a/455'}, {u'lastName': u'Gamble', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_O-y3pnqPvt-20hK7yAxYpzkgzBLm1_37yKeYpqbGotAY2F9ftquDtN12RJ5lKkh_0AY01PvsQ1VE', u'id': u'QXJyywhDcH', u'firstName': u'Meredith', u'publicProfileUrl': u'http://www.linkedin.com/pub/meredith-gamble/34/4b/6b8'}, {u'lastName': u'Gentry', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_IdV5b2IbwEe6Fmf9wmRnb7ULbexLImf9WaaVb7ZBZSwzqo4nbfoWdf2MW60VeWaVoo4UeHESzVkO', u'id': u'fi5VWeH1Mn', u'firstName': u'Tim', u'publicProfileUrl': u'http://www.linkedin.com/pub/tim-gentry/15/381/865'}, {u'lastName': u'Geoghegan', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_zVjRU_tXWX7Ou2I8B4UXUhiJd3Zr82R8BRdkU31k9Xuhxe2hMpDczTbEF74fiIVuqJ0LNQ3MJ8AH', u'id': u'bCKtLI1Z6s', u'firstName': u'Peter', u'publicProfileUrl': u'http://www.linkedin.com/pub/peter-geoghegan/24/1a8/497'}, {u'lastName': u'Gerrity', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_in1UQZi872kcAVsZ_N_XQR-tfa39lxsZTqFXQR1hrIz6mRS47KiBHUba38Td-ZUNGvA5WySMqQLZ', u'id': u'z6HiRYjND0', u'firstName': u'Cate', u'publicProfileUrl': u'http://www.linkedin.com/in/categerrity'}, {u'lastName': u'Gerson', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_3Y7SZpl9qhCcCTpT_yjtZxKZn89JGXpTiMU-ZxGoW6Gdj8I3SZxT90nXZSn6TijShgSPB4K4VQQi', u'id': u'VobRJ-pDhw', u'firstName': u'Jeffrey', u'publicProfileUrl': u'http://www.linkedin.com/in/jeffreydgerson'}, {u'lastName': u'Gharegozlou', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_tK6jMq8hYQ1Pjqof-rLCMnKjy_kxjqUfrB-CMBig_LK7GKu7On9AccBPtmX8Y1siPPXinrAU708r', u'id': u'QIuv5MLJCW', u'firstName': u'Roxana', u'publicProfileUrl': u'http://www.linkedin.com/in/roxanagharegozlou'}, {u'lastName': u'Gharpuray', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_fo2QEpeHkI8IQwfXDEyJEYJZ6Sn6QHmXTm4JEYJHJmC9MuMk_2pEXOS6HL9JLf7HadaZ5JICWDTJ', u'id': u'xWVLYbnMnG', u'firstName': u'Rishi', u'publicProfileUrl': u'http://www.linkedin.com/in/rishimgharpuray'}, {u'lastName': u'Glass', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_txz5sK_waFTr2sfG-g5Vs-8WGbn020fGrj3Vs-Cvj3Cf1U4COMLWqt9U2E9h74aaPycUvvK8E0D6', u'id': u'L1ASOlkIt3', u'firstName': u'Stephanie', u'publicProfileUrl': u'http://www.linkedin.com/pub/stephanie-glass/43/949/648'}, {u'lastName': u'Goswiller', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_gxkFOAQe_NrimMrhgJBNOt9oiKvm2VTh0ZKZOPFJpPTY1Yn8AMNIK1PcD4zl7j82yyQJAqz6XsSU', u'id': u'2poBdiJLAA', u'firstName': u'Christina', u'publicProfileUrl': u'http://www.linkedin.com/pub/christina-goswiller/11/561/130'}, {u'lastName': u'Gow', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_jbmxXPMOq7kSvLMnP_HuXrEj4f-_vQMnxQshXrMfFo6PEGm9lTYPEKD39Tty9TZspkuTIBFpdZ_h', u'id': u'rl3NImd7M1', u'firstName': u'Lawson', u'publicProfileUrl': u'http://www.linkedin.com/in/lawsongow'}, {u'lastName': u'Grafentin', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_pCD07nEOZy8fqLqWyLph7zHl4x5DNQqWO6J87zwDFJljwGidKkj13v0i9tL-cTz5jTf38tvufKV_', u'id': u'tfgCPJ0uN-', u'firstName': u'Ben', u'publicProfileUrl': u'http://www.linkedin.com/pub/ben-grafentin/25/356/800'}, {u'lastName': u'Gras', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_FiVC97mucFodRCj1LFJj9DDScTOJRCD1LXaj92mlHCodX6VPwLomZuVxJdY6Z5206h4yJwpGmYFP', u'id': u'NL8O9hhbpG', u'firstName': u'Alexander', u'publicProfileUrl': u'http://www.linkedin.com/in/alexandergras'}, {u'lastName': u'Greenberg', u'id': u'jyMVlFf8NU', u'firstName': u'Sylvie', u'publicProfileUrl': u'http://www.linkedin.com/pub/sylvie-greenberg/39/35b/536'}, {u'lastName': u'Griffen', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_uuv-7UJFgs1ebABWaIkS7JZwjx5owt6WawTS7Jd9GylVN9AdhE5O3Mg41cLzHvF5S7B28YRzvkEq', u'id': u'JoxgY0JNc8', u'firstName': u'Natalie', u'publicProfileUrl': u'http://www.linkedin.com/pub/natalie-griffen/58/13/847'}, {u'lastName': u'Grimes', u'id': u'FUKkROBSbd', u'firstName': u'Joseph', u'publicProfileUrl': u'http://www.linkedin.com/pub/joseph-grimes/23/1b6/325'}, {u'lastName': u'Grinalds', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_m8msvsMx5GkJBoWxh6SLv4UYWhiWBo4x2bsLv4dunLcMemf0GQYnRZgCbm_nqDJP7_uksxUZqwbi', u'id': u'YThucK0Ddg', u'firstName': u'Andrew', u'publicProfileUrl': u'http://www.linkedin.com/in/grinalds'}, {u'lastName': u'Gunther', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_zR-8KkPBt9ZlGqCYzJ1xK6lnrqDrGlCYBV60KFPQftJhjzvOMjGuObFeOJSfTn_tq4rYx8TL2a5K', u'id': u'y5vvGLd2pG', u'firstName': u'Garrett', u'publicProfileUrl': u'http://www.linkedin.com/pub/garrett-gunther/24/1a6/55b'}, {u'lastName': u'Gupta', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_Vu55rTVeTNdCIZCPNWzVrGHLTqxSwZiPZalVriEVYAwgNpq1nEvWY_Oq7s0tHxGxR7bU0k4xdBE9', u'id': u'QrSnRqQjFA', u'firstName': u'Nitin', u'publicProfileUrl': u'http://www.linkedin.com/in/gniting'}, {u'lastName': u'Guzman', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_vrCZ-3lAarW--JBrBl-b-CA7mn0grsBrBtnF-C8flvISfO8KJ9tNyGq38OxCPgnpN18QjLOhvrat', u'id': u'pZJSvZ3nup', u'firstName': u'Francisco', u'publicProfileUrl': u'http://www.linkedin.com/in/fguzman1'}, {u'lastName': u'Habal', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_utI7LyG29d9FYQ7qGnUyL0q2q2rEYQxqm90rL0XjIEXsTGeNhNR_wxK1V3KvjTY4SldloZ9FgnjL', u'id': u'V3L_5n9QTk', u'firstName': u'Rami', u'publicProfileUrl': u'http://www.linkedin.com/pub/rami-habal/0/48/254'}, {u'lastName': u'Hamel', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_zR-8KkGBtrdyCBCYcOC1K6rsrlDrGlCYcV60KFPQftJhjzvOMjGuObFeOJSfTn_tq4rYx8TGV-5K', u'id': u'UIUAxzzK2V', u'firstName': u'Rob', u'publicProfileUrl': u'http://www.linkedin.com/pub/rob-hamel/40/b48/21a'}, {u'lastName': u'Hanley', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_rOHwyqGJkclg7wKmYVENyniQQ-bj7wKmt0pqynTJMcPDKfbay44b-9zceyFG2ulCAjovPAPK8Md7', u'id': u'29xtZDs0Bx', u'firstName': u'Tim', u'publicProfileUrl': u'http://www.linkedin.com/pub/tim-hanley/6/946/5b5'}, {u'lastName': u'Harrington', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_mVxsC0k4opcWCSvc2yfWCg5Vo0A5haqc2RwLCgz5zMLv0EiBGp7n2jTwX-ls_dzR7JgkSVwI9LY0', u'id': u'AiRSVb1gfc', u'firstName': u'Shannon', u'publicProfileUrl': u'http://www.linkedin.com/in/shannonharrington1'}, {u'lastName': u'Harrison', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_m8msvsElwilIcWWxaC2dv4oPWhiWBo4x2bsLv4dunLcMemf0GQYnRZgCbm_nqDJP7_uksxUSW_9i', u'id': u'hdllyFSDZ4', u'firstName': u'Kelley', u'publicProfileUrl': u'http://www.linkedin.com/pub/kelley-harrison/31/b7b/544'}, {u'lastName': u'Harry', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_9fXpR82LpGOldBeTnDk7RGuop3VjwBJTNSr_RiDsibaDN1a3sdqrv_MN-2sGHK4Sc26GqkProMbe', u'id': u'ajcNPTtd_Y', u'firstName': u'Ethan', u'publicProfileUrl': u'http://www.linkedin.com/pub/ethan-harry/42/5bb/31b'}, {u'lastName': u'Hartman', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_eOkdZfNwG6S67J73HMGnZS5eGQRd7sO3oyKnZSXJj5fJKOdTX4NL9DKc2aU92g0DWjQcBo9QeM35', u'id': u'5DR32_Z_gF', u'firstName': u'Lane', u'publicProfileUrl': u'http://www.linkedin.com/pub/lane-hartman/69/bb9/890'}, {u'lastName': u'Havens', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_4dB69TjQ8keGIUfPZIKM9GZchG0CIgfPnS_M9GRc03ItqJ41NfboZC7JaExgesaxJov4J5We2tdp', u'id': u'83pNLRIEwi', u'firstName': u'David', u'publicProfileUrl': u'http://www.linkedin.com/pub/david-havens/30/49/961'}, {u'lastName': u'Haymore', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_C-W9UUrmeGhVjwd2hvRWU4_CokLJxHd2hzgWU4GxzTAd8uOuaqMVzZnlXo56pfHh_AwHNxrOnUdc', u'id': u'iPk_H2_cIk', u'firstName': u'Thomas', u'publicProfileUrl': u'http://www.linkedin.com/pub/thomas-haymore/3/548/926'}, {u'lastName': u'Hergenrader', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_-KgZflKgwsC-lD9X-tswf1_-IpnOADBXK-WFf-83qJCaaW8kYnSNTtqfLt93tonH1PxQhvOidg4V', u'id': u'q2N0zeRlna', u'firstName': u'Eric', u'publicProfileUrl': u'http://www.linkedin.com/pub/eric-hergenrader/22/665/526'}, {u'lastName': u'Herrera', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_9-HjcTr0VXoK0XElNvJCci38sFpjxbRlqzpCciT05XHD8i2Asq4AM_zAN7yGp8VgcAoi4k1MGZVD', u'id': u'JAWEc6KSRX', u'firstName': u'Erika', u'publicProfileUrl': u'http://www.linkedin.com/pub/erika-herrera/60/721/299'}, {u'lastName': u'Holz', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_R7Vm6_MwBIshHCDzJuEg63o6caOfECjzJDaA6heqHeo0v6ovBWoCe8pVJiYrd5pJVu4KdbsJ3BCj', u'id': u'Gz3tgc1Rb_', u'firstName': u'Eric', u'publicProfileUrl': u'http://www.linkedin.com/pub/eric-holz/62/655/24'}, {u'lastName': u'Hood', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0__gnH4Z1QC3lNfySu3plB4R_LC8kUf0puTJCB4Rhqg6KwrUI2fUQXnUNVuSXku4j8CYN9cy-B1YsX', u'id': u'fRYr-0cmrc', u'firstName': u'Whitney', u'publicProfileUrl': u'http://www.linkedin.com/pub/whitney-hood/30/6b8/97'}, {u'lastName': u'Hoversten', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_hW3LF0acCH_nXJmcGE_9FgDvGelcQsmcGDzsFyjeja5FMOMBu7AdWpWQ25AHLg7R3EiRHR77ApYw', u'id': u'T5JofaC7sM', u'firstName': u'Nick', u'publicProfileUrl': u'http://www.linkedin.com/pub/nick-hoversten/54/536/396'}, {u'lastName': u'private', u'id': u'private', u'firstName': u'private'}, {u'lastName': u'Huang', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_Y7bJr1dd7Pn_oYL1ySLErlIZS-tfERN1yIPQrleZtNQ0vx_P-WBzYApn_0-rdpv0xu5F099-pSc-', u'id': u'ItGTRhFOq6', u'firstName': u'Kevin', u'publicProfileUrl': u'http://www.linkedin.com/pub/kevin-huang/24/508/20'}, {u'lastName': u'Hussey', u'id': u'Ca3YzJZnpX', u'firstName': u'Caroline', u'publicProfileUrl': u'http://www.linkedin.com/pub/caroline-hussey/9/aa1/78a'}, {u'lastName': u'Hyrkin', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_MC0eb_op6aRgqujnUiSBb3VlkDYDqfjnR5Icb3whUHEjIwo9zkfkdT0aE_O-BHpsZTjneQz8FFcR', u'id': u'jfuFH04yQW', u'firstName': u'Joe', u'publicProfileUrl': u'http://www.linkedin.com/pub/joe-hyrkin/0/75/6b7'}, {u'lastName': u'Ibarra Rodriguez', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_ljrrcP6VybBPGqdAPy37cATRpklOC-dA1pX7crhbiT5agnOljRhpMKNW-oA33zHjKO-a4BOOA0Oo', u'id': u'bNR8UXRwcJ', u'firstName': u'Irene', u'publicProfileUrl': u'http://www.linkedin.com/pub/irene-ibarra-rodriguez/a/259/7ab'}, {u'lastName': u'Ipalook', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_4dB698ZBCFsadOmPsIKM9GdbhX0CIgfPsw_M9GRc03ItqJ41NfboZC7JaExgesaxJov4J5WU66Rp', u'id': u'XThv8ZMPD0', u'firstName': u'Calen', u'publicProfileUrl': u'http://www.linkedin.com/in/cjipalook'}, {u'lastName': u'Jilo', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_CHQ4Y4xkmcGsIsbDhmBbYUOLmKFzdJ9D8utbYUO4l91L9g3SaanqrRE98gboEOc3_Ik6lp8OqWC_', u'id': u'RZX_tF7xN_', u'firstName': u'Allen', u'publicProfileUrl': u'http://www.linkedin.com/in/ajilo'}, {u'lastName': u'Johnson', u'id': u'IFFSafgoY9', u'firstName': u'Jacob', u'publicProfileUrl': u'http://www.linkedin.com/pub/jacob-johnson/24/b76/6b8'}, {u'lastName': u'Jones', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_2weeFgdoQfFHWdjBuDURFOdFkDrbWEjBmuycF0VJUHXBnaoc8SZkWxmcE_KZoSpUDeEnHZXXG6x8', u'id': u'NEFa43Vnhs', u'firstName': u'Tim', u'publicProfileUrl': u'http://www.linkedin.com/in/timallenjones'}, {u'lastName': u'Joyce', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_gPLYkP3mY2_fpKwcgqBDkrFxYElmpzUcxNA3krFxTW5YiluBAvztoKPlKGAlx-sRyKF8wBMpV38D', u'id': u'c1Ps15nHk_', u'firstName': u'Will', u'publicProfileUrl': u'http://www.linkedin.com/pub/will-joyce/22/310/312'}, {u'lastName': u'Kahramaner', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_DjKFeM5s3e_XGVpI709NeRN4idbWCxSI_MkZeV5bp7PMgRswTR8I6sAWDXFn3ZuF2OtJbgc2eOzW', u'id': u'tTENFTInpT', u'firstName': u'Deniz', u'publicProfileUrl': u'http://www.linkedin.com/pub/deniz-kahramaner/3a/936/509'}, {u'lastName': u'Kalbus', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_D5pUSRwgH4tFqanoSbjeSZJGEj5Lnano7FHXSMZGvUlzWETET_2BiJ22krLVzdB62QO5COQ9GpTs', u'id': u'c2etviq1Hr', u'firstName': u'Porter', u'publicProfileUrl': u'http://www.linkedin.com/pub/porter-kalbus/52/334/bba'}, {u'lastName': u'Kaplan', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_-OwaAqGkcqPlSk3jKMRAABQEcA3YfFKjrJxlABTZHBzmr_bgY4UGxcznJpTTuhlA1jWrOr0C1IC7', u'id': u'iK1JI4xWIP', u'firstName': u'Will', u'publicProfileUrl': u'http://www.linkedin.com/in/williamhkaplan'}, {u'lastName': u'Kelley', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_uuv-7sRo0y9QwABWaDcT7JMLjV5owt6WaaTS7Jd9GylVN9AdhE5O3Mg41cLzHvF5S7B28Yc3K_Rq', u'id': u'6304QMvbBv', u'firstName': u'Katherine', u'publicProfileUrl': u'http://www.linkedin.com/in/katherinekelley'}, {u'lastName': u'Kemper', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_ndxXK8aMb9RYbDA-qmyRKGf9F-pKbm8-NawUKiY64AH8ZoBtVf7HO_oHdsy7XWTOBogVxk8p5upd', u'id': u'MjphOdxGJ_', u'firstName': u'Sean', u'publicProfileUrl': u'http://www.linkedin.com/pub/sean-kemper/64/a25/573'}, {u'lastName': u'Kent', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_DBwsjM9CEqPkxwNDfvD5jR5ioAb50wND7nxLjVvYzqPvhf_STlUnPs3KXxFsyuv32NWk-gIDvSaO', u'id': u'0NB271QMy7', u'firstName': u'Ryan', u'publicProfileUrl': u'http://www.linkedin.com/pub/ryan-kent/8/5b/63'}, {u'lastName': u'Kim', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_jE7gvrIBVGkTwbUP07uGvPJEshP_bXVPxHUGvPJo5QbPZ8D1luxlR1SXND1yXiRxpWS_sqw1fPEY', u'id': u'qy7axaDvSO', u'firstName': u'Binna', u'publicProfileUrl': u'http://www.linkedin.com/in/binnakim'}, {u'lastName': u'Kinsey', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_Wn8k2DqxGpjc1yK5INhR27cKC4JbAJ35w-NR2mnSgYDBag9LLKKeCaG_uzMZtOhWevCsidXu6FbW', u'id': u'aDkkx_Wbu5', u'firstName': u'Jocelyn', u'publicProfileUrl': u'http://www.linkedin.com/pub/jocelyn-kinsey/23/a8a/29a'}, {u'lastName': u'Klausner', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_oCf8SdR-zOSUN6tEoL7PSEwgvjHIq5CEk6R0SEw2EOpRI3voQk0uio0GUveqBC_QITDYCDzTq66m', u'id': u'KrbQBAvcO-', u'firstName': u'Greg', u'publicProfileUrl': u'http://www.linkedin.com/in/gregklausner'}, {u'lastName': u'Klein', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_jOgiHAbMcI_i_F76jZuKHPGJBuvfi3a60JWyHPXke7T0p5JQl4SfQ1KEMXzr86fopjxjFqVoxcD-', u'id': u'vBGla2Qjmq', u'firstName': u'Alex', u'publicProfileUrl': u'http://www.linkedin.com/pub/alex-klein/35/783/621'}, {u'lastName': u'Kneller', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_Vu55r8Z63NHubZtPsDz9riDbTqxSwZiPZwlVriEVYAwgNpq1nEvWY_Oq7s0tHxGxR7bU0kZJBHE9', u'id': u'9cZacnqC_C', u'firstName': u'Jake', u'publicProfileUrl': u'http://www.linkedin.com/in/jakekneller'}, {u'lastName': u'Kordic', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0__NWrbZ8iswnVpGZs3ls_bRPTVeCcOXds3Pg7bRlpLSnF38OVftMpdUL-q6GHgiHnCBwaey7Ga4n0', u'id': u'pVwLhMcRzV', u'firstName': u'Dylan', u'publicProfileUrl': u'http://www.linkedin.com/pub/dylan-kordic/19/244/648'}, {u'lastName': u'Koroleva', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_zVbmG38ejxdg2Ah9vgnjGCqbAy0rucl9BjPAGC1ZaMIhPPQnMpBCuGbn0-xffrKVqJ5KDLT16Uf1', u'id': u'2Ff9HO9kIU', u'firstName': u'Mariya', u'publicProfileUrl': u'http://www.linkedin.com/pub/mariya-koroleva/35/8a7/46'}, {u'lastName': u'Kostopoulos', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_HiYZ1HJAk1xbvf9YHkaF1wMPerDeBuBYEXEF1wI8BzJZeH8OkLmNgIxmQYSBqwntdhyQp2v_jW_u', u'id': u'Da5Vf7Ojk5', u'firstName': u'Kay', u'publicProfileUrl': u'http://www.linkedin.com/pub/kay-kostopoulos/10/795/6b5'}, {u'lastName': u'Kozachenko', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_goVSNNJH9F5-ebgj1fION9JqnLTGEGpjxIa-N9sqW6v-vQIgA2oTVnaVZS3jdLjAyd4PUlHPOJud', u'id': u'nIZ8TYqi_J', u'firstName': u'Alex', u'publicProfileUrl': u'http://www.linkedin.com/in/alexkoz11'}, {u'lastName': u'Kraemer', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_eyd5KS_HHcdWTdC-oxM9KaNbXByWSdi-E4jVKaLVRAeMtSqtXsJWOmlqospnaaGOWxIUxWc_kWAb', u'id': u'aBwBPwmPf7', u'firstName': u'Kerry', u'publicProfileUrl': u'http://www.linkedin.com/pub/kerry-kraemer/51/568/975'}, {u'lastName': u'Ladd', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_bNwbMo3CkG0nyap7L1INMeGgQ6WNYw27L9x4MWljM8gkTfRfItUwcdL1eIdwjuD_QBWMnaijAfH5', u'id': u'EdN4CpjkFF', u'firstName': u'Andrew', u'publicProfileUrl': u'http://www.linkedin.com/in/ajladd'}, {u'lastName': u'LaForge', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_54wi7etQB0UJS3_dbpDy7o3QBMecfFGdbJxy7IlZe0yFr_zWdOUf3wLnMNHHuhiLkRWj8ufA9L6z', u'id': u'NPxmPpDZcc', u'firstName': u'Andrew', u'publicProfileUrl': u'http://www.linkedin.com/pub/andrew-laforge/64/177/386'}, {u'lastName': u'Laraki', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_UQF0Z_yj-3SaJ1M3Uh98ZhjhOiUGRn43MG18Zhsj357-X-fTc8c198a1raRjZlJDs5L3BbXpKzbR', u'id': u'mb49n4EmDK', u'firstName': u'Zineb', u'publicProfileUrl': u'http://www.linkedin.com/in/zlaraki'}, {u'lastName': u'Laube', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_mbFanOwOt5XbMzuta66gngW7tTA5Jnytui1lngMYSFLv6-w-GTcG4jDKyulsslgY7kLrMVFQzSyv', u'id': u'XwIfxWZYtO', u'firstName': u'Kevin', u'publicProfileUrl': u'http://www.linkedin.com/pub/kevin-laube/37/404/369'}, {u'lastName': u'Lazarus', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_mLnj-0Wmx9hEMrbKukBm-gYu01tLRPBKuTCC-gZlhvQzXc8rGiQAyj2xAO-VZNny76NijVEPw2zE', u'id': u'j3LTxU3Eez', u'firstName': u'Michael', u'publicProfileUrl': u'http://www.linkedin.com/pub/michael-lazarus/22/b19/234'}, {u'lastName': u'Lee', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_R2NuP6wblzjuE9-xMSBxP57IPP77or-xMm81P5dzuzUxzNL0Bok8jLgRgYfKWc1PVfntyGBENJAw', u'id': u'DdAMF-NLbP', u'firstName': u'Diana', u'publicProfileUrl': u'http://www.linkedin.com/in/dianayl'}, {u'lastName': u'private', u'id': u'private', u'firstName': u'private'}, {u'lastName': u'Lehman', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_eMnW9w1ea_oE800x6gb99HQqGGfLu00xoRC99HNqjFRzPUH0XxQ5ZehV2u7Vf4OPWsNBJ7ovrtFh', u'id': u'VpKVih7NDd', u'firstName': u'Travis', u'publicProfileUrl': u'http://www.linkedin.com/pub/travis-lehman/21/27/929'}, {u'lastName': u'Leon', u'id': u'MFdo3vN2SQ', u'firstName': u'Daniel', u'publicProfileUrl': u'http://www.linkedin.com/pub/daniel-leon/44/412/5'}, {u'lastName': u'Levine', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_9G8uJTg-Ai7yv9OGn3r1JGptP6VjzvOGN8N1JiSauLaDoAdCsXK8B_JhgmsGnt0ac3Ct9k1gFxux', u'id': u'Z9zgYNcrJz', u'firstName': u'Adoni', u'publicProfileUrl': u'http://www.linkedin.com/pub/adoni-levine/63/7a/b86'}, {u'lastName': u'Levitt', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_m8msvsZpWbNXUo4xm5OWv4WPW_iWBo4x2GsLv4dunLcMemf0GQYnRZgCbm_nqDJP7_uksxBYSl_i', u'id': u'-LlrEWXV2_', u'firstName': u'Teddy', u'publicProfileUrl': u'http://www.linkedin.com/pub/teddy-levitt/22/797/11'}, {u'lastName': u'Lin', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_RSNOt_VeYrW7w19AvebDthRIY1g7WK9AME8TthWzT9Wxnq3lBwk-p8jRKgjKoBcjVmnhgbRWjdVA', u'id': u'D9MH7_jI7B', u'firstName': u'Amanda', u'publicProfileUrl': u'http://www.linkedin.com/pub/amanda-lin/22/42a/793'}, {u'lastName': u'Lindemann', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_fsPnURzVuX9HT4J2fY8dUZ-q2FL6TOe2SgbdUZz61GA9Ysxu_y_sz4THGW5JGJWhaMleN0IZnVyg', u'id': u'wSqcHZ2RJt', u'firstName': u'William', u'publicProfileUrl': u'http://www.linkedin.com/pub/william-lindemann/27/225/332'}, {u'lastName': u'Linn', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_G13YmJirYxzZjz9ICrlDmsltY0FZAnBI8lz3mU3DTM1ea-8wmzAthRviK-bbtlnFiri8Tp0TzP8a', u'id': u'vWS5kdvAbq', u'firstName': u'Sam', u'publicProfileUrl': u'http://www.linkedin.com/pub/sam-linn/59/3b8/153'}, {u'lastName': u'Liu', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_txz5sKt5G_1fusfGr05Vs-AXGbn020fGKR3Vs-Cvj3Cf1U4COMLWqt9U2E9h74aaPycUvvpNH3Z6', u'id': u'gOuodw4Vv0', u'firstName': u'Elliott', u'publicProfileUrl': u'http://www.linkedin.com/in/elliottliu'}, {u'lastName': u'London', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_SLdsnxoGd3iQUoet7hHdnpM_WblkUWZt7bjLnpRpnk5NkD7-3iJn4y7-bfAU4mMYu6IkMU5nh5g6', u'id': u'jnQM0pz-lN', u'firstName': u'Alyssa', u'publicProfileUrl': u'http://www.linkedin.com/pub/alyssa-london/36/759/787'}, {u'lastName': u'Longyear', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_N-oHBb-7bTy0xDDp9rZcBX3hF3f00eypnzOBBXGO4bRfh2wy4qVXJknrd27hy7grvAH9Z_Kq0dby', u'id': u'lNFyCQGlFX', u'firstName': u'CJ', u'publicProfileUrl': u'http://www.linkedin.com/in/cjlongyear'}, {u'lastName': u'Lorentzen IV', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_tpExEzCHqDC72QJep4VuEn3e4HFxuLJepZYhEBi4FI17PTaHOVsPXcB998b8fG4kP0eT5rjeyR1z', u'id': u'59inNZ85Zx', u'firstName': u'Oivind', u'publicProfileUrl': u'http://www.linkedin.com/pub/oivind-lorentzen-iv/32/990/230'}, {u'lastName': u'Luczak', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_zVjRUCtkwGS1C7E8zOSXU31Xd3Zr82R8BZdkU31k9Xuhxe2hMpDczTbEF74fiIVuqJ0LNQTEPrLH', u'id': u'xJSgzjlo31', u'firstName': u'Grace', u'publicProfileUrl': u'http://www.linkedin.com/in/graceluczak'}, {u'lastName': u'Madsen', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_Ow-uHBRBr2n-W-OoY210Hzw5rfLG5lOoyu61HqVLfWA-szdEtSG8QNmIOG5j6n060ertFPHfNijt', u'id': u'83PSHrikpP', u'firstName': u'Arden', u'publicProfileUrl': u'http://www.linkedin.com/in/ardenmadsen'}, {u'lastName': u'Maler', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_imOA6RgBVeK96bIMSEym6ZDJsHisXTIMT2om6ZaQ5mcERLpJ7eaje4seNL_5bQovGSpfd0pFMuFs', u'id': u'aI4vPER43V', u'firstName': u'Paul', u'publicProfileUrl': u'http://www.linkedin.com/pub/paul-maler/3a/5b6/965'}, {u'lastName': u'Maliwal', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_bvDvUe1OebR9rddu5-wEUIPAHFHNKEduLtJoUoAmcTpk7aO2IPjMzE586oew1SH8QnfwNSi-fQEZ', u'id': u'PVuMMjLdfg', u'firstName': u'Aditi', u'publicProfileUrl': u'http://www.linkedin.com/pub/aditi-maliwal/2a/540/5b4'}, {u'lastName': u'Mandelbaum', u'id': u'UU4InmFyQ6', u'firstName': u'Fern', u'publicProfileUrl': u'http://www.linkedin.com/pub/fern-mandelbaum/1/585/a48'}, {u'lastName': u'Mandiga', u'id': u'Jtam3CH4b7', u'firstName': u'Rahul'}, {u'lastName': u'Marks', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_sMe3tGz5zteCm6lA4OMtt8bwzng826TA4RyYt8NJoPWK1Cnl9xZDphhcR4jx738jUsE0gFo5UOdn', u'id': u'4iO1nSV-UH', u'firstName': u'Caroline', u'publicProfileUrl': u'http://www.linkedin.com/pub/caroline-marks/25/1b1/8b6'}, {u'lastName': u'McCann', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_CHQ4Y4xHur-RWsBDC7XwYsm6m1FzdJ9DhEtbYUO4l91L9g3SaanqrRE98gboEOc3_Ik6lphn_4A_', u'id': u'Q4gEnLNSo4', u'firstName': u'Allison', u'publicProfileUrl': u'http://www.linkedin.com/in/allisontmccann'}, {u'lastName': u'Meyer', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_3rnHNjCGG_FnO0plilbRNxAmC8rMy0pliNCBNxi-g6XW_UIAS9QXV0BpuSKQ04jgh1N9U4AAr0Ba', u'id': u'-FX_9-rVuw', u'firstName': u'Austin', u'publicProfileUrl': u'http://www.linkedin.com/pub/austin-meyer/26/765/57a'}, {u'lastName': u'Miller', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_yHCbiz4W_gBhFMrZOWh4inwJixT85VhZYEn4in4dpyvKsYc4ratwS9uFDc3x6j3NgI8M2AoXALuE', u'id': u'UVJiOgU1L4', u'firstName': u'Brogan', u'publicProfileUrl': u'http://www.linkedin.com/pub/brogan-miller/47/b3/8b2'}, {u'lastName': u'Miller', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_mB1VmU51fMrQPVvw2vGLm4cA7yQ5PxvwuKF5m4v_KVtvuRCIGli9hZ3STl6srZNb7NAXTxI3FGTO', u'id': u'dO16g0sXfj', u'firstName': u'Danielle', u'publicProfileUrl': u'http://www.linkedin.com/pub/danielle-miller/36/139/228'}, {u'lastName': u'Mischel', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_xtJM_N8fH4FhpE5JAn4o_cciHpCDOfvJjrD6_cbrcsnj3wCM1NdvDB1O6AG-gHNzYlRbuKzu6vyu', u'id': u'Fb6KjIbqaS', u'firstName': u'Brandon', u'publicProfileUrl': u'http://www.linkedin.com/pub/brandon-mischel/29/aab/138'}, {u'lastName': u'Montgomery', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_jOgiHAL9co6C3Fx6jMYKHtNsBdvfi3a6x0WyHPXke7T0p5JQl4SfQ1KEMXzr86fopjxjFqsM13R-', u'id': u'Z9zho4g9Cq', u'firstName': u'Ian', u'publicProfileUrl': u'http://www.linkedin.com/pub/ian-montgomery/64/a09/414'}, {u'lastName': u'Montgomery', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_iWKW8jfvGYLBQ0tqSa_98YJkGgKnQ01qTIk98YYXjRkQMUXN7785aOoo2KrWL4-4GEtB7J2IBWYK', u'id': u'UzGmqcgOk5', u'firstName': u'Tom', u'publicProfileUrl': u'http://www.linkedin.com/pub/tom-montgomery/9/100/b3a'}, {u'lastName': u'Moore', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_ZgfI5iq4Ffsx37SzZV2q58vdL2Y7_WgzV0RN5T5WVdExyDEvqU0FI3AbICOKhmyJMYDzE6cc1GxZ', u'id': u'5XB0wj6pwb', u'firstName': u'John'}, {u'lastName': u'Morgan', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_Fl0jZWhPUFOWAhVDF9MCZoXYJ8wMP_UD5nICZo__65xWuFuSwBfA9EcScaIQrks36tjiBSAW1dQm', u'id': u'rj089P5kjA', u'firstName': u'Evan', u'publicProfileUrl': u'http://www.linkedin.com/in/evanmorganpub'}, {u'lastName': u'Mosbacher', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_U-ft0kNjNBaC1i9mUAOT06NgZ9wmPLbmJKRD06b7b1xYuTKacq0YlQ1TnZIlrGQCsADurTMK2yi6', u'id': u'AOEs-404NX', u'firstName': u'Jack', u'publicProfileUrl': u'http://www.linkedin.com/pub/jack-mosbacher/37/784/524'}, {u'lastName': u'Moskovits', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_Pk_hA9Sjr1ngN-ig1X3PANpgrN8AqqigA5BxANg2flN3IKqj0CP2xqdGOVhaB1GltbTOO1i8Yr7B', u'id': u'FL2ft2hqGE', u'firstName': u'Peter', u'publicProfileUrl': u'http://www.linkedin.com/pub/peter-moskovits/0/815/853'}, {u'lastName': u'Mulloy', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_gPLYkPF_yoz2yKUcj-vDkr9uYElmpzUcxNA3krFxTW5YiluBAvztoKPlKGAlx-sRyKF8wBMc23kD', u'id': u'YOnOqRxVq-', u'firstName': u'Shannon', u'publicProfileUrl': u'http://www.linkedin.com/pub/shannon-mulloy/6b/890/194'}, {u'lastName': u'Muthuraman', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_9Nf_3QBuNUs1Ki1U9KSy3LKPqY2A-LiUN9Rp3Ll2Ig43DTqRst0775LGV9ualGGBcBDgaC7E0qLN', u'id': u'Cn_uSRurrO', u'firstName': u'Raja', u'publicProfileUrl': u'http://www.linkedin.com/in/rajamuthuraman'}, {u'lastName': u'Naifeh', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_2AaKEUBAVW1kKbdHulY7E4FxVH6w-beHm9VfEJ6uLm-UDixe8cOyXMtCqLQNl8WXD-2m5YZKxaWq', u'id': u'BosrCp8lnk', u'firstName': u'Greg', u'publicProfileUrl': u'http://www.linkedin.com/in/gregnaifeh'}, {u'lastName': u'Nakhostin', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_EBP1Xf1AjmRXPAHnetKuXuq1guO6PtHnHnbuXuv_C7o9u9096l_0E23SPXYJrvdswNlDIIb-dVBj', u'id': u'bMw3PDP9cO', u'firstName': u'Amir', u'publicProfileUrl': u'http://www.linkedin.com/in/amirnakhostin'}, {u'lastName': u'Nelson', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_jE7gvrRoniQuFbVP02Ymvtozs_P_bXVPxSUGvPJo5QbPZ8D1luxlR1SXND1yXiRxpWS_sqw-bZyY', u'id': u'qOXJJ_dmtJ', u'firstName': u'Katie', u'publicProfileUrl': u'http://www.linkedin.com/pub/katie-nelson/36/281/85a'}, {u'lastName': u'Nesbit', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_9r8JGibl2xZYrJvnZBl6GT3aa0OgKJqnNcNQG88aAMoS7gi9s9Kzuhqhh-YC1Ozsc1CFDFOJnt5w', u'id': u'Ggtbmk6-KS', u'firstName': u'Josh', u'publicProfileUrl': u'http://www.linkedin.com/in/joshnesbit'}, {u'lastName': u'Niculcea', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_6X3m4fOmK_wbJz28kFGg4SpOti4czng8kizA4ugmS52Fo-EhEGACn2d8yaZHnlyuFFiKcI7s324n', u'id': u'oebBQ0Yz8S', u'firstName': u'Andreea', u'publicProfileUrl': u'http://www.linkedin.com/in/andreeaniculcea'}, {u'lastName': u'Noguerol', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_vrCZ-hK1u9oYtJ9rzlTb-_lKm10grsBrcAnF-C8flvISfO8KJ9tNyGq38OxCPgnpN18QjLYrC3St', u'id': u'zsw3WI2RNa', u'firstName': u'Felipe', u'publicProfileUrl': u'http://www.linkedin.com/in/felipenoguerol'}, {u'lastName': u'Noll', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_yHCbiqVzTstCbxhZO7GZiBV4iVT85VhZYun4in4dpyvKsYc4ratwS9uFDc3x6j3NgI8M2AQwA8mE', u'id': u'QQ4siZ-rTe', u'firstName': u'Travis', u'publicProfileUrl': u'http://www.linkedin.com/in/travisalexandernoll'}, {u'lastName': u'Norton', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_gnYAT9XxJsvfA_nV0N2mTNcyJZ_GlhFV0qEmTvn86OB-mkrsAKmjfzGmcvij-F69yvyfm-H-dn0C', u'id': u'dB2svGggLk', u'firstName': u'Timothy', u'publicProfileUrl': u'http://www.linkedin.com/in/tjnorton'}, {u'lastName': u'Novak', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_jE7gvrenni8S5TVPgemCvPsRshP_bXVP0aUGvPJo5QbPZ8D1luxlR1SXND1yXiRxpWS_sqIuHe0Y', u'id': u'omLmNgoX0-', u'firstName': u'TJ', u'publicProfileUrl': u'http://www.linkedin.com/pub/tj-novak/9/733/ba2'}, {u'lastName': u"O'Leary", u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_r4vDWnKF-u3YD-SWtjkYWzGkK75A7-gW-yTtWzlv7dl3KnEdyO53FvLUYCLa2zy5ARB1Qt7ANjZh', u'id': u'MyZSUognIx', u'firstName': u'Mary Elizabeth', u'publicProfileUrl': u'http://www.linkedin.com/pub/mary-elizabeth-o-leary/25/14/a20'}, {u'lastName': u'Operskalski', u'id': u'6scfb4c7zO', u'firstName': u'Jacob', u'publicProfileUrl': u'http://www.linkedin.com/pub/jacob-operskalski/57/5a6/87'}, {u'lastName': u'Osborne', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_5J73_m8B9UssTbhzLY0t_DTqnVYcTXTzFUUY_DAoW0EFY8nvd0xDDS5XZNOHGi8JkVS0uEiIRvyy', u'id': u'OYSVZGzt4X', u'firstName': u'Alex', u'publicProfileUrl': u'http://www.linkedin.com/pub/alex-osborne/b/694/644'}, {u'lastName': u'Oswald', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_mLnj-OIugtLWRr9KaFXa-gOa0ntLRPBK2GCC-gZlhvQzXc8rGiQAyj2xAO-VZNny76NijV6Je23E', u'id': u'YT88XSG50n', u'firstName': u'Max Cougar', u'publicProfileUrl': u'http://www.linkedin.com/in/maxcougaroswald'}, {u'lastName': u'Ottinger', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_SrapvxNYsTvk-T41S-j7vj5gV_-HrbM1ftV_vpQfLQ64fimP39OrRy-3qDtcP8Z0u12GsU4e2XYV', u'id': u'5wMkY-PMUI', u'firstName': u'Lauren', u'publicProfileUrl': u'http://www.linkedin.com/pub/lauren-ottinger/35/87a/654'}, {u'lastName': u'Ou', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_FEYCE72Nn7aJL8ykL2xAEDYUNHUvb8DkLaEjE20Qwm75ZXVXwummXuwesLREXb2e6Wyy5wTTvHRG', u'id': u'Ee_pkVC5wB', u'firstName': u'Yin Yin', u'publicProfileUrl': u'http://www.linkedin.com/pub/yin-yin-ou/28/ba9/99a'}, {u'lastName': u'Padval', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_8GEYKgu3NA6ERQn-CCVDK0YDZBrsJLc-CLY3K0aObNXE6Tht2XstOxsrn0K5sG9OT3e8xZKldFV1', u'id': u'XRlVmNvEY7', u'firstName': u'Vikram', u'publicProfileUrl': u'http://www.linkedin.com/pub/vikram-padval/35/ab6/994'}, {u'lastName': u'Paine', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0__gnH4MPWCk3R70Su_Vqc4RrLCLkUf0puTsCB4Rhqg6KwrUI2fUQXnUNVuSXku4j8CYN9cyYlnjjX', u'id': u'6U_Ew4E_VA', u'firstName': u'Raechel', u'publicProfileUrl': u'http://www.linkedin.com/in/raechelpaine'}, {u'lastName': u'Payne', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_xtJM_vqKXgv7yuXJjKOQ_cziHMCDOfvJjvD6_cbrcsnj3wCM1NdvDB1O6AG-gHNzYlRbuKMHfxfu', u'id': u'XkRpbpjdVg', u'firstName': u'Shelby', u'publicProfileUrl': u'http://www.linkedin.com/pub/shelby-payne/55/6/410'}, {u'lastName': u'Perani', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_hqAXNO8Khk9UA02AhchRNyGxCilc1y2AGzLUNylCgh5F24Rlu-3HVpLuuwAHKUDj3c1VUR_rtPdU', u'id': u'RlMXS3OjWO', u'firstName': u'Robin', u'publicProfileUrl': u'http://www.linkedin.com/pub/robin-perani/35/962/944'}, {u'lastName': u'Perkins', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_zR-8KkCZrA0hGqiYvyC0KFlsrlDrGlCYcM60KFPQftJhjzvOMjGuObFeOJSfTn_tq4rYx8D0yX-K', u'id': u'XRThBdqQAb', u'firstName': u'Galen', u'publicProfileUrl': u'http://www.linkedin.com/pub/galen-perkins/23/b6b/210'}, {u'lastName': u'Peter', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_gPLYktc7Y7b_p1oc0BbDkrz7YflmpzUc0tA3krFxTW5YiluBAvztoKPlKGAlx-sRyKF8wBMrqjQD', u'id': u'N8v-UHegRx', u'firstName': u'Jenny', u'publicProfileUrl': u'http://www.linkedin.com/in/jennypeter'}, {u'lastName': u'Pidikiti', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_7bH7ExUfB2KIR3fkf6mKEjd8BHcbMF0kSLprEjV0eIiBQ_HXiT4_XgmAM8BZVhOemkol5sXhGQ-k', u'id': u'ccxIyCmjdw', u'firstName': u'Ramesh', u'publicProfileUrl': u'http://www.linkedin.com/pub/ramesh-pidikiti/1/7b0/389'}, {u'lastName': u'Pollak', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_IdV5b2JIFHdowDY9wmZsbmIQbIxLImf9dSaVb7ZBZSwzqo4nbfoWdf2MW60VeWaVoo4UeHQMSD8O', u'id': u'BgQs924tVp', u'firstName': u'Eli', u'publicProfileUrl': u'http://www.linkedin.com/pub/eli-pollak/50/b15/6b1'}, {u'lastName': u'Porter', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_73E_PZH8nn5Xs8-0fiSrPVVgqPCwZL_0D_YpPRogIKnUbTNxiFs7jUYPVRGNRGC1mGegyyq_aYaC', u'id': u'3ZM71wF0k1', u'firstName': u'Ross', u'publicProfileUrl': u'http://www.linkedin.com/pub/ross-porter/15/101/498'}, {u'lastName': u'Pulido', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_IyKoXmzn3WVdiMOnWx_JX2LF_dOW3xxndgkvX2LbyooMORe9bs86EulWSTYnCZYsoxtqIwUxPceS', u'id': u'ft2SmpkIYq', u'firstName': u'Alex', u'publicProfileUrl': u'http://www.linkedin.com/pub/alex-pulido/24/7bb/9'}, {u'lastName': u'private', u'id': u'private', u'firstName': u'private'}, {u'lastName': u'Quarles', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_lwfCFPDBqazgLiuclWHlFrjUNIl-5LDc1dRjFrpWwa5GsTVBjS0mWKebs5AD6G2RKeDyHBmjlH94', u'id': u'FI565iVO_X', u'firstName': u'Austin', u'publicProfileUrl': u'http://www.linkedin.com/pub/austin-quarles/33/511/a31'}, {u'lastName': u'Quon', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_txz5sK1W8CitmyfGr06ns-KeGbn020fGKR3Vs-Cvj3Cf1U4COMLWqt9U2E9h74aaPycUvvrtgzu6', u'id': u'kEFLlFWYwy', u'firstName': u'Rachel', u'publicProfileUrl': u'http://www.linkedin.com/pub/rachel-quon/49/4a3/8a4'}, {u'lastName': u'Raynor', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_OYjMBBqVoQNmCddpy4pQBqBbHCimCuJpyMd6BqbFcbcYgHaytZDvJN1d62_l3w4r0g0bZPJzf0T0', u'id': u'0izqwXSrUq', u'firstName': u'Ellen', u'publicProfileUrl': u'http://www.linkedin.com/in/eraynor'}, {u'lastName': u'Reeves', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_66VqguuaIqDNVmQh6GybgafCItMBsmQhkFawgfy-qlSb5ol8Eho417HpLVJeJWb2FL4otemZFesf', u'id': u'853vrmbHpk', u'firstName': u'Zia Zelda', u'publicProfileUrl': u'http://www.linkedin.com/in/ziazeldareeves'}, {u'lastName': u'Reynolds', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_6X3m4fsg-hjvBzg8QFrl4u7OtQ4czng8XizA4ugmS52Fo-EhEGACn2d8yaZHnlyuFFiKcIiDEmSn', u'id': u'JEEKpWYgXp', u'firstName': u'Michael', u'publicProfileUrl': u'http://www.linkedin.com/in/michaelreynolds33'}, {u'lastName': u'Ridley', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_vJv4J_hd7GmgTjoCcYQIJ3_HDhRASYVCBOTbJ3A9-Qf3tVDGJ05qBT54iDUaaMRmNVB69Q_60_1G', u'id': u'jcrQ02K4Ee', u'firstName': u'Bethany', u'publicProfileUrl': u'http://www.linkedin.com/pub/bethany-ridley/36/228/242'}, {u'lastName': u'Riley', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_W1fpiDFlMgwX15qqdtS7im3uMxyIl5vqI-R_imF2QseRm3CNLz0rSaPGBApq-CN4erDG2dvuwTs2', u'id': u'R9p_2zJCfl', u'firstName': u'Katie', u'publicProfileUrl': u'http://www.linkedin.com/pub/katie-riley/2b/21a/6a9'}, {u'lastName': u'Romero', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_LNotMm3mJ8ERpCoiFKD3MDTDRhZnYkwiwrODMD-gXiuQThy_WtVYcSQPze4Wj_EfXBHunE2PVdv8', u'id': u'absQXh7bMz', u'firstName': u'Evan', u'publicProfileUrl': u'http://www.linkedin.com/pub/evan-romero/23/28a/b70'}, {u'lastName': u'Rosenkranz', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_x9J4KtkaovQTOEntjnWFKrz1elATpfntjADbKAnPBcLliwT-1rdqOlGgQylYxHBYYzR6xneIW1tn', u'id': u'Asp6C17p6U', u'firstName': u'Adrian', u'publicProfileUrl': u'http://www.linkedin.com/in/adrianrosenkranz'}, {u'lastName': u'Rosztoczy', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_iWKW8jxUCZLsEytqSf_n8Y0kGOKnQ01qTIk98YYXjRkQMUXN7785aOoo2KrWL4-4GEtB7J8fhEjK', u'id': u'wbkdJOzlk3', u'firstName': u'Ryan', u'publicProfileUrl': u'http://www.linkedin.com/pub/ryan-rosztoczy/21/478/208'}, {u'lastName': u'Rudolph', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_yq555BnDifBTjYaMptnV5z60T7_8xZ7MY1lV5zqxYuBK8pZJr-vWIv8l7FixpxmvgcbUEtQ1tPYM', u'id': u'vg0WJ1e47D', u'firstName': u'Paul', u'publicProfileUrl': u'http://www.linkedin.com/pub/paul-rudolph/4a/439/ba2'}, {u'lastName': u'Ryan', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_oivHPfdTTKdHRZh1o3QRPuu33rOIUYr1HbTBPuIrOnoRkVFPQL5Xj2xOfjYq4MA0IhB9yIJNohXD', u'id': u'u_JDRVX1Vp', u'firstName': u'Thomas', u'publicProfileUrl': u'http://www.linkedin.com/pub/thomas-ryan/25/b62/623'}, {u'lastName': u'Sa Freire', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_A8PuXtmrKmvYBlanAF3xXryyrf-xB-On1Xb1XrfhfW67end9gQ_8EKUaOGt8qz0sr_ltIBgizacp', u'id': u'gea5v7mOmA', u'firstName': u'Thiago', u'publicProfileUrl': u'http://www.linkedin.com/in/thiagosafreire'}, {u'lastName': u'Saeta', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_io443xObWOFVEIQc_SIw3pyLIZA9oDncSm2b3j0zqUL6zWTB72Hq7gwRLrldWoBRGdV6asDrsOQ1', u'id': u'euKCrYm93L', u'firstName': u'Andrew', u'publicProfileUrl': u'http://www.linkedin.com/pub/andrew-saeta/31/3a9/742'}, {u'lastName': u'Sagan', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_-RFTK-nk0ccPC98trO9tKlcW1BA-m98tKM1OKlrR2ALGltB-YjcSOAkzjslDDATY14Lxx9GMOOSG', u'id': u'FxGwUVPjLF', u'firstName': u'Benjamin', u'publicProfileUrl': u'http://www.linkedin.com/pub/benjamin-sagan/36/292/270'}, {u'lastName': u'Sanchez', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_n2b0Mby5gLUKHAW79S3hMLdZg6WpEc47qDP8MLfZCLg2vPffVoB1c5UnPmdidrJ_Bf53nCAT4I6G', u'id': u'seK4y0wMoN', u'firstName': u'Mike', u'publicProfileUrl': u'http://www.linkedin.com/in/manchez12'}, {u'lastName': u'Sandman', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_rVO-LK_BMHBphCwqYym3L-1LRWrlh3oqtjoSL1KLXuXT05jNypaOwPXIzFKm_6I4AJp2oNGKtWyF', u'id': u'7ey-s41_Ou', u'firstName': u'Jim'}, {u'lastName': u'Schmalzried', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_OMZdSB6bQy8aafCoyyVVSzkvXjLC2utoyYunSqczR4At1H5EtxeLiN_RoP5g7wP60sscCP5WfkJz', u'id': u'c_HdepqN09', u'firstName': u'Katie', u'publicProfileUrl': u'http://www.linkedin.com/pub/katie-schmalzried/22/561/870'}, {u'lastName': u'Schottenstein', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_fo2QEjRvoWhdQafX7HYMEYOV6Hn6QHmXDD4JEYJHJmC9MuMk_2pEXOS6HL9JLf7HadaZ5JF355PJ', u'id': u'7A0J9Wwe65', u'firstName': u'Julia', u'publicProfileUrl': u'http://www.linkedin.com/pub/julia-schottenstein/18/243/254'}, {u'lastName': u'Schwab', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_Y5gdzlHKFLLinDO-ybYVz-01b_KinDO-y3Wnz-ZCZLk1WWdt-_SLUt2uWmrpzo0OxQxcVvoHl19E', u'id': u'UR_Vg03LVH', u'firstName': u'Amanda', u'publicProfileUrl': u'http://www.linkedin.com/pub/amanda-schwab/18/2a1/381'}, {u'lastName': u'Scutt', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_uQ-Va4W0mMB9vUXE26C5asVP2yX6BgvEaT65asJ81Vr9eJCoh8G98VSmGlkJqsNQS5rX3jFEldQI', u'id': u'kTczo3NmH0', u'firstName': u'Helena', u'publicProfileUrl': u'http://www.linkedin.com/pub/helena-scutt/40/3ab/39a'}, {u'lastName': u'Sebastian', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_uXLP6OwCpDXEM1Jz2_bu6ys8OH-QMzdzaQA26y4x3D6nQlOvhGzxepulrQtMV-HJSFFSdRo2RxX9', u'id': u'l4llhDmjJG', u'firstName': u'Katherine', u'publicProfileUrl': u'http://www.linkedin.com/pub/katherine-sebastian/29/82/672'}, {u'lastName': u'Sefton', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_itf3qV-yJkQVrhgpiB2tqM-jzLis-5Sp39RYqZG2o_cED3sy7N0Ds4nGRH_5lCurGlD0R0pvN6w4', u'id': u'mfls-q-yAN', u'firstName': u'Peter', u'publicProfileUrl': u'http://www.linkedin.com/in/psefton'}, {u'lastName': u'SHAH', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_QoM0AHf5R-UnH3zjXwIuAEj5UtS9oCNjXDS8AE0vkqM6z6_go2W1xowUvxDdW5vAbdU3ODSZXAHc', u'id': u'1UtbhXdP7U', u'firstName': u'NILAY', u'publicProfileUrl': u'http://www.linkedin.com/pub/nilay-shah/20/396/928'}, {u'lastName': u'Shapiro', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_NFyu8T2jvjMp95Cq9XO08GxKvOyPN_tqn_e18GxTEZe_wF5N43u8aCI7U1puckP4vXYt753zV3yr', u'id': u'wnDI05p8xl', u'firstName': u'Sam', u'publicProfileUrl': u'http://www.linkedin.com/pub/sam-shapiro/24/216/57b'}, {u'lastName': u'Sharf', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_6H28iapqq4EzdX-N62y0iuYB9pgcLXGNkE40iugHd0WFV8zqEapuS2d64NjHQiiZFIaY2I7KVtOI', u'id': u'4hP_evIMXi', u'firstName': u'Michael', u'publicProfileUrl': u'http://www.linkedin.com/in/michaelgsharf'}, {u'lastName': u'Shouse', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_VoW0f8J5MUg26kqXNuJ2fG4wUxVTokqXZDg8fisMkJalzhikn2M1T_aBvtsYW_zHRdw3hkkRvLMf', u'id': u'Ix_8RKPH54', u'firstName': u'Tucker', u'publicProfileUrl': u'http://www.linkedin.com/in/tuckershouse'}, {u'lastName': u'Simmons', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_tlYgpl1rJA3Y1hF_KNSCp-G1J-zxPhn_rKEGp-_i6c37ukTiOBmlttcDcyv8rFB7Pty_1vgcXKM2', u'id': u'5jzkS18oCV', u'firstName': u'Erin', u'publicProfileUrl': u'http://www.linkedin.com/in/erinparisisimmons'}, {u'lastName': u'Smith', u'id': u'OUIdoxLTZq', u'firstName': u'Aaron', u'publicProfileUrl': u'http://www.linkedin.com/pub/aaron-smith/53/43/279'}, {u'lastName': u'Smith', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_KMzyHnqbgmhhav4o-U5_Hz-wxu5K2P4o-Z3iHztv8Wl81cfEpxLKQv6UlGL77NJ6lscCFt8UjFRN', u'id': u'5OLPcO0H_S', u'firstName': u'Will', u'publicProfileUrl': u'http://www.linkedin.com/pub/will-smith/1b/114/36b'}, {u'lastName': u'Solomon', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_U-uG039aqK0TlQrGM9gj0_5YNPVm1LhGMKZg0_bawKaY2TcCcqyali1hsRslKG3asAmprXJV8Jaj', u'id': u'fUyPYRwAIw', u'firstName': u'Audrey', u'publicProfileUrl': u'http://www.linkedin.com/pub/audrey-solomon/31/366/78b'}, {u'lastName': u'Spector', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_fquK8jnyJYc605Nq79Si8YvPMgKQ15kqD1Zf8YqaQYkn23PN_-yyaO8hBzrMKC54acmm7JQy_TBQ', u'id': u'51GWI4IvC_', u'firstName': u'Joe', u'publicProfileUrl': u'http://www.linkedin.com/in/joespector'}, {u'lastName': u'Stannard', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_6H28iaycn449bG-N62Y1iSS49MgcLXGNkd40iugHd0WFV8zqEapuS2d64NjHQiiZFIaY2I_DqOMI', u'id': u'cqcjkNTgA6', u'firstName': u'Kristin', u'publicProfileUrl': u'http://www.linkedin.com/in/kristinstannard'}, {u'lastName': u'Stevens', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_-1nutqh7AP-Axr-jrPBxtntuPn3YjP-jK-C1tB3luvzmGcLgYzQ8pcvxgOTTYN1A1rNtgrPXch3F', u'id': u'0vmPbjTxDu', u'firstName': u'Trevor', u'publicProfileUrl': u'http://www.linkedin.com/pub/trevor-stevens/27/166/582'}, {u'lastName': u'Stewart', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_r9mLMn87kT-A-fO7tz2nMzCPX65lrEa7tNssMzKfRilTfaJfyrYdcvX3oeLmPSf_AzuRntmzbHLl', u'id': u'jJ_BM3XI3W', u'firstName': u'Brent', u'publicProfileUrl': u'http://www.linkedin.com/in/brentrstewart'}, {u'lastName': u'Strickland', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_yrLwHBNa3otfOxpoYqXZHqniiu52pMpoYNAqHzLxpolpijIEr9zbQvllDTL1xYj6g1FvFtR4Jz_L', u'id': u'J8kFUBF_5P', u'firstName': u'Michael', u'publicProfileUrl': u'http://www.linkedin.com/pub/michael-strickland/14/500/45b'}, {u'lastName': u'Stutz', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_8GEYKyY3Zv5cRQF-hhHTKOO_ZBrsJLc-CiY3K0aObNXE6Tht2XstOxsrn0K5sG9OT3e8xZpBH7M1', u'id': u'cr5WJmU1Lh', u'firstName': u'Andrew', u'publicProfileUrl': u'http://www.linkedin.com/pub/andrew-stutz/67/50b/197'}, {u'lastName': u'Swanson', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_8LXTPsu3KlnvJlTxGkzYPJJDKv_nUBhxGbrOPJYy7KBQk1c02iqSjMotYRiW4K3PT66xyYuqUtGq', u'id': u'-y0iksIKeF', u'firstName': u'Catherine', u'publicProfileUrl': u'http://www.linkedin.com/pub/catherine-swanson/1a/1b8/46b'}, {u'lastName': u'Tanner', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_4dB69Tew85smWOmPZIAz9GjEhb0CIgfPVS_M9GRc03ItqJ41NfboZC7JaExgesaxJov4J5WtBeEp', u'id': u'9MC7BErEuT', u'firstName': u'Leigh', u'publicProfileUrl': u'http://www.linkedin.com/pub/leigh-tanner/39/16b/8b0'}, {u'lastName': u'Taylor', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_I3FrdoRa0dpXNvWHWQ6_dWsfxooWZ9WHd617dWWj8uOMbtYebFcpbdj1lFEnRAeXoGLa6aRzic7z', u'id': u'79XuBAooZK', u'firstName': u'Lindsay', u'publicProfileUrl': u'http://www.linkedin.com/pub/lindsay-taylor/28/a65/746'}, {u'lastName': u'Thiry', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_HiYZ1d4Yk1UFvfBYoFgw1wU0erDeBuBYEXEF1wI8BzJZeH8OkLmNgIxmQYSBqwntdhyQp2vM-GBu', u'id': u'W72Jxgqcbc', u'firstName': u'Christina', u'publicProfileUrl': u'http://www.linkedin.com/pub/christina-thiry/32/826/a5'}, {u'lastName': u'Thompson', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_sNXFMQPDubOTOgS7VniZML528hW8OUS749rZMLqyxigK30sf9tqIc58tmedxgyu_UB6JnCED4Vxr', u'id': u'zcUWon2NRQ', u'firstName': u'Madeleine', u'publicProfileUrl': u'http://www.linkedin.com/pub/madeleine-thompson/66/b56/978'}, {u'lastName': u'Travlos', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_yq555nq_Tf5SjZxMOPzs5znDTW_8xZ7MOnlV5zqxYuBK8pZJr-vWIv8l7FixpxmvgcbUEto4xEyM', u'id': u'ZBrnSEpKN6', u'firstName': u'Xanthe', u'publicProfileUrl': u'http://www.linkedin.com/pub/xanthe-travlos/11/270/b07'}, {u'lastName': u'Tublin', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_SmdaARVwNKLoHLAg7uogAZeHNAheHLKgfWjlAMwVwBqZcTbj3eJGxJ0qsp8BwGlluSIrOOzwOqvn', u'id': u'L4Zh9prGUO', u'firstName': u'Daniel', u'publicProfileUrl': u'http://www.linkedin.com/pub/daniel-tublin/62/51a/58a'}, {u'lastName': u'Tucker', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_n2b0MQY408VpEtM7Nfn8MXu4g_WpEc47qmP8MLfZCLg2vPffVoB1c5UnPmdidrJ_Bf53nCAnMcXG', u'id': u'RLTrdkmQiq', u'firstName': u'Will', u'publicProfileUrl': u'http://www.linkedin.com/pub/will-tucker/20/194/a81'}, {u'lastName': u'Vance', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_CHQ4Y4geaPlsw06D8WvFYsaZmzFzdJ9DhEtbYUO4l91L9g3SaanqrRE98gboEOc3_Ik6lp80aEz_', u'id': u'jG2M1dPk6x', u'firstName': u'Zoe', u'publicProfileUrl': u'http://www.linkedin.com/pub/zoe-vance/35/639/700'}, {u'lastName': u'Walker', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_TOAnqYKUDkksTxHK_ZrLqpiB78-ZipHKi0LdqpTkK_6epZ0rD43ssyzETHtb8Rdy8j1eRU1XxX5c', u'id': u'I6sUqy7Ntp', u'firstName': u'Alex', u'publicProfileUrl': u'http://www.linkedin.com/in/wockerwalker'}, {u'lastName': u'Wareing', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_jE7gvrwq4TXaFXoPP2uCvPeEs5P_bXVPxwUGvPJo5QbPZ8D1luxlR1SXND1yXiRxpWS_sqwy7iuY', u'id': u'Zc-ukfg3GU', u'firstName': u'John', u'publicProfileUrl': u'http://www.linkedin.com/pub/john-wareing/4a/311/581'}, {u'lastName': u'Warshaw', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_54wi7WTZUJDUf3Gd5pdp7o8EBVecfFGdFJxy7IlZe0yFr_zWdOUf3wLnMNHHuhiLkRWj8u71k6lz', u'id': u'Iq2slsBWXl', u'firstName': u'Bobby', u'publicProfileUrl': u'http://www.linkedin.com/pub/bobby-warshaw/16/832/a6b'}, {u'lastName': u'Watkins', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_utI7Ly52ndqwYiOquKSKLOqhq2rEYQxqm90rL0XjIEXsTGeNhNR_wxK1V3KvjTY4SldloZ915ZeL', u'id': u'sjO5ZLiuF0', u'firstName': u'Forrest', u'publicProfileUrl': u'http://www.linkedin.com/pub/forrest-watkins/54/447/649'}, {u'lastName': u'Wetmore', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_459zxis77qgh4Z5isXAox8E-SvZCsYXisCGExTR-t1ut5V1_N_6JA37p_Z4gJMLfJQqIK6WEsRdW', u'id': u'W_Xl8ada7i', u'firstName': u'Daniel', u'publicProfileUrl': u'http://www.linkedin.com/pub/daniel-wetmore/12/8a7/1a2'}, {u'lastName': u'Whale', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_I3Frdo7h0EJ6VrHHdXBidesCxooWZ9WHd517dWWj8uOMbtYebFcpbdj1lFEnRAeXoGLa6aR9xjpz', u'id': u'AtCLagAcym', u'firstName': u'Brandon', u'publicProfileUrl': u'http://www.linkedin.com/in/brandonwhale'}, {u'lastName': u'Wigo', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_eyd5KSC6QvwQDEi-6M49KfFsXByWSdi-oUjVKaLVRAeMtSqtXsJWOmlqospnaaGOWxIUxWckl_Nb', u'id': u'QGLnJVsNDl', u'firstName': u'Drac', u'publicProfileUrl': u'http://www.linkedin.com/pub/drac-wigo/21/87b/187'}, {u'lastName': u'Wilkey', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_vIGEzkjN8bEAXU7Yvu8zzF2Rh6DlXUOYc29zzFpE0LJTR0dOJD-QUbekamSmby0tNHhNV8mAD3bI', u'id': u'yZOop_yOdJ', u'firstName': u'Patrick', u'publicProfileUrl': u'http://www.linkedin.com/in/patrickwilkey'}, {u'lastName': u'Williamson', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_u_fFGJs-5pkHNWlsuX7ZGsarLyGE9WTsa3RZGse7Vx9sdDnVh50IuVpTIqCvvm8nS8DJDjsQ1zXM', u'id': u'iP_wSh9gls', u'firstName': u'Jordan', u'publicProfileUrl': u'http://www.linkedin.com/in/williamsonjordan'}, {u'lastName': u'Wilson', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_RNyrIkbrJaY3KhdIMBO7I69lMIwit_dIMve7I6qTQSx1SFOwBtup5Q87B6IpAkHFVBYaXTQ2x84-', u'id': u'aDck7CEbFn', u'firstName': u'Alec', u'publicProfileUrl': u'http://www.linkedin.com/in/alecfwilson'}, {u'lastName': u'Wittenberg', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_xxsvAv96eBLDudzjjsWQAcQeHt3DufLjgYmoAcFqclzjPw-g1MEMxBPV6VT-fHXAYyZwOKM9Qmau', u'id': u'Gwuxm0fabM', u'firstName': u'Alex', u'publicProfileUrl': u'http://www.linkedin.com/pub/alex-wittenberg/27/4b8/662'}, {u'lastName': u'Wittenberg', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_IUM7Se9XUguQS3CEdxIKSoPvBjH57C1EWySrSovveUpvK6XobgW_iE3UMres25-QoZUlCSIFBsd4', u'id': u'8RG0Nst9vq', u'firstName': u'Jacob', u'publicProfileUrl': u'http://www.linkedin.com/pub/jacob-wittenberg/30/248/6a8'}, {u'lastName': u'Wong', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_UQF0ZCJgO6WaczH3MCv2ZhdjOiUGRn43MG18Zhsj357-X-fTc8c198a1raRjZlJDs5L3BbHVKjPR', u'id': u'ZuhT8mYTIz', u'firstName': u'Lyon', u'publicProfileUrl': u'http://www.linkedin.com/in/lyonwong'}, {u'lastName': u'Woodburn', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_R7Vm6CWFB7sDEFyzJHZj6hmdcaOfECjzJIaA6heqHeo0v6ovBWoCe8pVJiYrd5pJVu4Kdb9Aihnj', u'id': u'HgRlE5Ss2s', u'firstName': u'Doug', u'publicProfileUrl': u'http://www.linkedin.com/pub/doug-woodburn/53/a43/632'}, {u'lastName': u'Woodward', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_W1fpiDqPvORUg6XqFcOfi750MxyIl5vqIqR_imF2QseRm3CNLz0rSaPGBApq-CN4erDG2dJ07oR2', u'id': u'Bd7Q-sQ1vY', u'firstName': u'Samantha', u'publicProfileUrl': u'http://www.linkedin.com/pub/samantha-woodward/30/74/576'}, {u'lastName': u'Wright', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_-RFTK-1L0cz-mP8tK05OKlBQ1qA-m98tKV1OKlrR2ALGltB-YjcSOAkzjslDDATY14Lxx9aygrUG', u'id': u'HqBFpCSKHs', u'firstName': u'Sage', u'publicProfileUrl': u'http://www.linkedin.com/pub/sage-wright/16/282/a7b'}, {u'lastName': u'Yanovsky', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_R7Vm6_4QBD4CEkyzJdZg634IcaOfECjzJeaA6heqHeo0v6ovBWoCe8pVJiYrd5pJVu4Kdb9Ntk3j', u'id': u'XQ7e1qgT5L', u'firstName': u'Beckie', u'publicProfileUrl': u'http://www.linkedin.com/in/beckieyanovsky'}, {u'lastName': u'Yendluri', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_bvDvUeKPXX7X-udu5lSEUo3xHFHNKEdu5AJoUoAmcTpk7aO2IPjMzE586oew1SH8QnfwNS7UaisZ', u'id': u'R0yzMRnUMJ', u'firstName': u'Vikas', u'publicProfileUrl': u'http://www.linkedin.com/in/vikasuy'}, {u'lastName': u'Youts', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_UciCehk0K2O-rKpbMB-je_9utuVG-zSbMrcje_92S7a-DlsFcA1m6iCGyXsjl-uwsq3ybXkB0hcL', u'id': u'zFZpbUXgvY', u'firstName': u'Stephen', u'publicProfileUrl': u'http://www.linkedin.com/in/stephenyouts'}, {u'lastName': u'Zeller', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_O-y3pB6Gzr1f1537KN2OpzX0zqLm1_37pneYpqbGotAY2F9ftquDtN12RJ5lKkh_0AY01PzdNcgE', u'id': u'aXeTaekLpE', u'firstName': u'Jake', u'publicProfileUrl': u'http://www.linkedin.com/pub/jake-zeller/54/234/799'}, {u'lastName': u'Zurmuhlen', u'pictureUrl': u'http://m.c.lnkd.licdn.com/mpr/mprx/0_3PuunxAPBCC9rh0tiqgxnjAavGlJK5Yt_NZ1npCaEk5d73W-Svy84y9hUfA61CxYhKmtMUKBc52h', u'id': u'aq6JsNXjo4', u'firstName': u'Kristy', u'publicProfileUrl': u'http://www.linkedin.com/pub/kristy-zurmuhlen/56/6a6/666'}]

		# create user
		user = User(username="ctholz")
		user.save()
		# create acct
		acct = Account(service="linkedin", owner=user, expires_on=datetime.datetime(2013, 6, 23, 15, 36, 51, 694994), status=unicode("active"), token_secret=u'67cbcc33-30bf-423d-b677-92bc3f775559', access_token=u'0a0d3a27-5713-439e-a57e-c2f35798b4a5')
		acct.save()
		# instantiate liConnections
		base = self.lilib.LIConnections(user.id, acct.id)	

		# CODE TAKEN DIRECTLY FROM lilib.process_connections
		for c in clayton_cxns[150:]:
			partial = False
			if c['firstName'] == 'private' and c['lastName'] == 'private':
				print "@process_connections: privacy settings set, passing on user"
				pass
			else:
				try:
					tmp = User.objects.get(account__uniq_id=c['id'],account__service="linkedin")
				except ObjectDoesNotExist:
					try:
						tmp = User.objects.get(username__icontains=c['id'])
						partial = True
					except ObjectDoesNotExist:
						tmp = None
				except:
					tmp = None

				# Partial User
				if tmp is not None and partial is True:
					print "@process_connections: user is partial, create rest" + c['firstName'] + ' ' + c['lastName']
					tmp = base.process_connection_and_finish_user(tmp,c)

				# New User
				elif tmp is None:
					tmp = base.process_connection_and_create_user(c)

				if tmp is not None: # needs to be left last to ensure that User has survived 
					base.add_connection(user, tmp)

		print "\n\n\n"
		print "User count: " + str(User.objects.all().count())
		print "Entity count: " + str(Entity.objects.all().count())

		# Verify that no "student" positions added
		print "Should = 0: " + str(Position.objects.filter(title="Student").exclude(type="education").count())
		# self.assertEqual(0, Position.objects.filter(title="Student").exclude(type="education").count())
		# Verify that no duplicate entities created
		all_entities = [e["name"] for e in Entity.objects.all().values("name")]
		import collections
		duplicates = [x for x, y in collections.Counter(all_entities).items() if y > 1]
		print "Should = 0: " + str(len(duplicates))
		if len(duplicates) > 0:
			print "Duplicates: "
			from pprint import pprint
			pprint(duplicates) 


		# self.assertEqual(len(all_ents), len(set(just_names)))
		# Verify that non "real" entities kept
		try:
			print "fetching Brogan now..."
			brogan = User.objects.get(profile__first_name="Brogan", profile__last_name="Miller")
			print brogan.positions.all().values("title", "entity__name")
		except:
			print "ERROR: Brogan not found."


	def test_get_company_name_only(self):
		base = self.lilib.LIBase()

		# (1) multiple entities, one of which is "correct"
		for i in range(4):
			e = Entity(name="foo")
			e.save()
		e = Entity(name="foo", li_univ_name="univ_foo", li_uniq_id="uniq_foo")
		e.save()
		ent = base.get_company_name_only("foo")
		self.assertIsNot(None, ent)
		self.assertIsNot(None, ent.li_univ_name)
		self.assertIsNot(None, ent.li_uniq_id)

		# (2) multiple entities, > 1 of which is "correct"
		for i in range(3):
			e = Entity(name="bar")
			e.save()
		for i in range(3):
			e = Entity(name="bar", li_uniq_id="uniq_bar", li_univ_name="univ_bar")
			e.save()
		ent = base.get_company_name_only("bar")
		self.assertIsNot(None, ent)
		self.assertIsNot(None, ent.li_univ_name)
		self.assertIsNot(None, ent.li_uniq_id)

		# (3) multiple entities, none of which are "correct"
		for i in range(8):
			e = Entity(name="baz")
			e.save()
		ent = base.get_company_name_only("baz")
		self.assertIsNot(None, ent)
		self.assertIs(None, ent.li_univ_name)
		self.assertIs(None, ent.li_uniq_id)	

		# (4) one entity, correct
		e = Entity(name="foobar", li_univ_name="univ_foo", li_uniq_id="uniq_foo")
		e.save()
		ent = base.get_company_name_only("foobar")
		self.assertIsNot(None, ent)
		self.assertIsNot(None, ent.li_univ_name)
		self.assertIsNot(None, ent.li_uniq_id)

		# (5) one entity, not correct
		e = Entity(name="foobaz")
		e.save()
		ent = base.get_company_name_only("foobaz")
		self.assertIsNot(None, ent)
		self.assertIs(None, ent.li_univ_name)
		self.assertIs(None, ent.li_uniq_id)

		# (6) no match
		ent = base.get_company_name_only("romeo & juliet")
		self.assertIs(None, ent)


	def test_add_unverified_position(self):
		base = self.lilib.LIBase()

		person = User(username="test_user")
		person.save()

		entity = base.add_unverified_company(({"entity_name":unicode("Artists of the Haight")}))

		p = base.add_unverified_position(person, entity, {"title":unicode("Artist in Residence"), "summary":None, "isCurrent":True})
		self.assertIsNotNone(entity)
		self.assertIsNotNone(p)
		self.assertIs(p.status, "unverified")
		self.assertIs(entity.status, "unverified")

	def test_process_unverified_org_position(self):
		# create user
		user = User(username="MistaFu")
		user.save()
		# create acct
		acct = Account(service="linkedin", owner=user, expires_on=datetime.datetime(2013, 6, 23, 15, 36, 51, 694994), status=unicode("active"), token_secret=u'67cbcc33-30bf-423d-b677-92bc3f775559', access_token=u'0a0d3a27-5713-439e-a57e-c2f35798b4a5')
		acct.save()
		# instantiate liConnections
		base = self.lilib.LIConnections(user.id, acct.id)	

		entity = Entity(name=unicode("FooBar, Inc."))
		entity.save()

		p1 = {
			'title':unicode("East Harlem"),
			'entity_name':unicode("FooBar, Inc."),
			'co_uniq_name':None,
			'startDate':None,
			'endDate':None,
			'summary':None,
			'isCurrent':False
			}

		p2 = {
			'title':unicode("West Harlem"),
			'entity_name':unicode("BarFoo"),
			'co_uniq_name':None,
			'startDate':None,
			'endDate':None,
			'summary':None,
			'isCurrent':False
			}

		# (1) Entity match
		base.process_unverified_org_position(p1,user)
		self.assertIsNotNone(user.positions.get(title="East Harlem"))
		self.assertEqual(1, Entity.objects.filter(name="FooBar, Inc.").count())
		self.assertEqual(unicode("FooBar, Inc."), user.positions.get(title="East Harlem").entity.name)
		self.assertEqual(unicode("unverified"), user.positions.get(title="East Harlem").status)

		# (2) New Entity
		base.process_unverified_org_position(p2,user)
		self.assertEqual(1, Entity.objects.filter(name="BarFoo").count())
		self.assertIsNotNone(user.positions.get(title="West Harlem"))
		self.assertEqual(unicode("BarFoo"), user.positions.get(title="West Harlem").entity.name)
		self.assertEqual(unicode("unverified"), user.positions.get(title="West Harlem").entity.status)
		self.assertEqual(unicode("unverified"), user.positions.get(title="West Harlem").status)


	def test_process_org_position(self):
		# create user
		user = User(username="test_user")
		user.save()
		# create acct
		acct = Account(service="linkedin", owner=user, expires_on=datetime.datetime(2013, 6, 23, 15, 36, 51, 694994), status=unicode("active"), token_secret=u'67cbcc33-30bf-423d-b677-92bc3f775559', access_token=u'0a0d3a27-5713-439e-a57e-c2f35798b4a5')
		acct.save()
		# instantiate liConnections
		base = self.lilib.LIConnections(user.id, acct.id)		


		# create "real" entity
		e_real = Entity(name=unicode("Twitter"), li_univ_name=unicode("twitter"), li_uniq_id=7)
		e_real.save()

		e_stub = Entity(name=unicode("Foobar"))
		e_stub.save()

		p_real = {
			'title':unicode("Brand Strategist"),
			'entity_name':unicode("Twitter"),
			'co_uniq_name':unicode("twitter"),
			'startDate':None,
			'endDate':None,
			'summary':None,
			'isCurrent':False
			}

		p_stub = {
			'title':unicode("DJ"),
			'entity_name':unicode("Foobar"),
			'co_uniq_name':None,
			'startDate':None,
			'endDate':None,
			'summary':None,
			'isCurrent':False
		} 

		# (1) When org exists
		base.process_org_position(p_real, user)
		self.assertEqual(1, Entity.objects.filter(name="Twitter").count())
		self.assertIsNotNone(user.positions.get(title="Brand Strategist"))
		self.assertEqual(unicode("Twitter"), user.positions.get(title="Brand Strategist").entity.name)

		# (2) When org exists & position exists
		base.process_org_position(p_real, user)
		self.assertEqual(1, Entity.objects.filter(name="Twitter").count())
		self.assertEqual(1, user.positions.all().count())
		self.assertIsNotNone(user.positions.get(title="Brand Strategist"))
		self.assertEqual(unicode("Twitter"), user.positions.get(title="Brand Strategist").entity.name)

		# (3) When no org exists	
		base.process_org_position(p_real, user)
		self.assertIsNotNone(Entity.objects.get(li_univ_name="twitter"))
		self.assertIsNotNone(user.positions.get(title="Brand Strategist"))
		self.assertEqual(unicode("Twitter"), user.positions.get(title="Brand Strategist").entity.name)

			

















