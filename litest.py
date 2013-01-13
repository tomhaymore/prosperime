# from Python
import oauth2 as oauth
import cgi
from optparse import OptionParser, make_option

# from Django
from django.utils import simplejson

linkedin_key = '8yb72i9g4zhm'
linkedin_secret = 'rp6ac7dUxsvJjQpS'

access_token = {
	'oauth_token_secret': '485e5fc6-3087-4a9a-8eb9-62def3cb0894', 
	'oauth_token': '4ac2be32-32b8-4555-bbee-ee365039e55f'
	}

def test_profile():

	fields = "(picture-url,email-address,headline,id,firstName,lastName,positions:(id,title),api-standard-profile-request:(url),public-profile-url,educations:(school-name,field-of-study,degree,start-date,end-date))"

	api_url = "http://api.linkedin.com/v1/people/~:" + fields + "?format=json"

	consumer = oauth.Consumer(linkedin_key, linkedin_secret)
	 
	token = oauth.Token(
		key=access_token['oauth_token'], 
		secret=access_token['oauth_token_secret'])

	client = oauth.Client(consumer, token)

	resp, content = client.request(api_url)

	print content

def test_connections():

	fields = "(public-profile-url,picture-url,educations:(id,school-name,field-of-study,start-date,end-date,degree),id,headline,firstName,lastName,positions:(start-date,end-date,title,is-current,summary,company:(id)))"

	api_url = "http://api.linkedin.com/v1/people/~/connections:" + fields + "?count=20&format=json"

	consumer = oauth.Consumer(linkedin_key, linkedin_secret)
	 
	token = oauth.Token(
		key=access_token['oauth_token'], 
		secret=access_token['oauth_token_secret'])

	client = oauth.Client(consumer, token)

	resp, content = client.request(api_url)

	content = simplejson.loads(content)

	print content

def test_company_profile():

	fields = "(id,name,universal-name,company-type,ticker,website-url,industries,status,logo-url,blog-rss-url,twitter-id,employee-count-range,locations:(description,address:(street1,street2,city,state,country-code,postal-code)),description,stock-exchange)"

	api_url = "http://api.linkedin.com/v1/companies/1337:" + fields + "?format=json"


	consumer = oauth.Consumer(linkedin_key, linkedin_secret)
	 
	token = oauth.Token(
		key=access_token['oauth_token'], 
		secret=access_token['oauth_token_secret'])

	client = oauth.Client(consumer, token)

	resp, content = client.request(api_url)

	# content = simplejson.loads(content)



	print content

def test_education():

	fields = "(educations:(id,school-name,field-of-study,start-date,end-date,degree))"

	api_url = "http://api.linkedin.com/v1/people/~/connections:" + fields + "?format=json"

	consumer = oauth.Consumer(linkedin_key, linkedin_secret)
	 
	token = oauth.Token(
		key=access_token['oauth_token'], 
		secret=access_token['oauth_token_secret'])

	client = oauth.Client(consumer, token)

	resp, content = client.request(api_url)

	print content

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-p", "--profile", action="store_true", dest="profile")
	parser.add_option("-x", "--connections",action="store_true", dest="connections")
	parser.add_option("-c", "--company",action="store_true", dest="company")
	parser.add_option("-e","--education",action="store_true",dest="education")
	(options, args) = parser.parse_args()
	if options.profile is True:
		test_profile()
	elif options.connections is True:
		test_connections()
	elif options.company is True:
		test_company_profile()
	elif options.education is True:
		test_education()
	else:
		test_profile()
		test_connections()
		test_company_profile()

