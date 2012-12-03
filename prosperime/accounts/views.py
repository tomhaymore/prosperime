# from Python
import oauth2 as oauth
import cgi

# from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.decorators import login_required
from accounts.models import Account
from django.contrib.auth.models import User
from django.utils import simplejson

linkedin_key = '8yb72i9g4zhm'
linkedin_secret = 'rp6ac7dUxsvJjQpS'

def linkedin_authorize(request):
	
	# set scope
	scope = 'r_fullprofile+r_emailaddress+r_network'

	# set callback
	callback = 'http://127.0.0.1:8000/account/authenticate/'

	# set urls
	request_token_url	= 'https://api.linkedin.com/uas/oauth/requestToken'
	# access_token_url	= 'https://api.linkedin.com/uas/oauth/accessToken'
	authorize_url		= 'https://www.linkedin.com/uas/oauth/authenticate'

	# setup OAuth
	consumer = oauth.Consumer(linkedin_key, linkedin_secret)
	client = oauth.Client(consumer)

	# get request token
	resp, content = client.request(request_token_url,"POST")
	if resp['status'] != '200':
		raise Exception(content)
	
	# parse out request token

	request.session['request_token'] = dict(cgi.parse_qsl(content))
	print request.session['request_token']

	url = "%s?oauth_token=%s&?scope=%s" % (authorize_url, request.session['request_token']['oauth_token'],scope)

	return HttpResponseRedirect(url)
  
# @login_required
def linkedin_authenticate(request):  
	consumer = oauth.Consumer(linkedin_key, linkedin_secret)
	# print request.session['request_token']
	# access_url = 'https://www.google.com/accounts/OAuthGetAccessToken?oauth_verifier=%s' % (request.GET['oauth_verifier'])
	# access_token_url = 'https://api.linkedin.com/uas/oauth/accessToken?oauth_verifier=%s' % (request.GET['oauth_verifier'])
	
	
	#token  = oauth.Token(request.session['request_token']['oauth_token'],request.session['request_token']['oauth_verifier'])
	access_token_url	= 'https://api.linkedin.com/uas/oauth/accessToken'
	# print access_token_url

	token = oauth.Token(request.session['request_token']['oauth_token'],request.session['request_token']['oauth_token_secret'])
	token.set_verifier(request.GET['oauth_verifier'])
	client = oauth.Client(consumer, token)

	resp, content = client.request(access_token_url, "POST")
	
	# print resp

	# if resp['status'] != '200':
	#     # print content
	#     raise Exception(request.session['request_token'])

	# print content

	access_token = dict(cgi.parse_qsl(content))
	print access_token
	# raise Exception(access_token)
	format = 'json'

	api_url = "http://api.linkedin.com/v1/people/~?format=json"
	 
	token = oauth.Token(
		key=access_token['oauth_token'], 
		secret=access_token['oauth_token_secret'])


	client = oauth.Client(consumer, token)

	resp, content = client.request(api_url)

	# linkedin_user_info = dict(cgi.parse_qsl(content))
	linkedin_user_info = simplejson.loads(content)
	print linkedin_user_info

	user = User.objects.create_user(linkedin_user_info['firstName']+linkedin_user_info['lastName'])
	user.save()

	profile = Account()
	profile.owner = user
	profile.access_token = access_token['oauth_token']
	profile.token_secret = access_token['oauth_token_secret']
	profile.service = 'linkedin'
	profile.save()

	return HttpResponseRedirect('/account/success')