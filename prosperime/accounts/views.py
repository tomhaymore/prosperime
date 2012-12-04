# from Python
import oauth2 as oauth
import cgi
from datetime import datetime, timedelta

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
from accounts.forms import FinishAuthForm

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

	request_token_url = "%s?scope=%s" % (request_token_url, scope, )

	# get request token
	resp, content = client.request(request_token_url,"POST")
	if resp['status'] != '200':
		raise Exception(content)
	
	# parse out request token

	request.session['request_token'] = dict(cgi.parse_qsl(content))
	print request.session['request_token']

	url = "%s?oauth_token=%s" % (authorize_url, request.session['request_token']['oauth_token'], )

	print url

	return HttpResponseRedirect(url)
  
# @login_required
def linkedin_authenticate(request):  
	consumer = oauth.Consumer(linkedin_key, linkedin_secret)
	# print request.session['request_token']
	
	access_token_url	= 'https://api.linkedin.com/uas/oauth/accessToken'
	# print access_token_url

	token = oauth.Token(request.session['request_token']['oauth_token'],request.session['request_token']['oauth_token_secret'])
	token.set_verifier(request.GET['oauth_verifier'])
	client = oauth.Client(consumer, token)

	resp, content = client.request(access_token_url, "POST")
	
	# print resp
	# print content

	access_token = dict(cgi.parse_qsl(content))
	
	print access_token
	
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

	# store information in a cookie
	request.session['linkedin_user_info'] = linkedin_user_info
	request.session['access_token'] = access_token

	return HttpResponseRedirect('/account/finish')

def finish_login(request):
	# TODO: redirect if not not authenticated through LinkedIn already
	if request.POST:
	
		# form submitted

		form = FinishAuthForm(request.POST)
		
		if form.is_valid():
			username = form.cleaned_data['username']
			email = form.cleaned_data['email']
			password = form.cleaned_data['password']

			# save user
			user = User.objects.create_user(username,email,password)
			user.save()

			# update user profile
			user.profile.full_name = request.session['linkedin_user_info']['firstName'] + " " + request.session['linkedin_user_info']['lastName']
			user.profile.first_name = request.session['linkedin_user_info']['firstName']
			user.profile.last_name = request.session['linkedin_user_info']['lastName']
			user.profile.headline = request.session['linkedin_user_info']['headline']
			user.profile.save()

			# create LinkedIn account
			acct = Account()
			acct.owner = user
			acct.access_token = request.session['access_token']['oauth_token']
			acct.token_secret = request.session['access_token']['oauth_token_secret']
			acct.service = 'linkedin'
			acct.expires_on = datetime.now() + timedelta(seconds=int(request.session['access_token']['oauth_authorization_expires_in']))
			acct.save()

			return HttpResponseRedirect('/account/success')
	else:
		form = FinishAuthForm()

	return render_to_response('accounts/finish_login.html',{'form':form},context_instance=RequestContext(request))

	

	# TOOD -- add user login / authorization

	
