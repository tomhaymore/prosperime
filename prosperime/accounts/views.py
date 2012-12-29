# from Python
import oauth2 as oauth
import cgi
from datetime import datetime, timedelta

# from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout as auth_logout, login as auth_login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.decorators import login_required
from accounts.models import Account
from django.contrib.auth.models import User
from django.utils import simplejson
from accounts.forms import FinishAuthForm, AuthForm
from django.core.management import call_command
from django.contrib import messages

linkedin_key = '8yb72i9g4zhm'
linkedin_secret = 'rp6ac7dUxsvJjQpS'

def login(request):
	
	# print request.session['_auth_user_backend']
	if request.user.is_authenticated():
		return HttpResponseRedirect('/')
	if request.method == "POST":
		# make sure using proper authentication backend
		request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
		form = AuthForm(request.POST)

		if form.is_valid():
			user = authenticate(username=form.cleaned_data['username'],password=form.cleaned_data['password'])
			if user is not None:
				auth_login(request,user)
				messages.success(request, 'You have successfully logged in.')
				return HttpResponseRedirect('/')
			
	else:
		form = AuthForm()

	return render_to_response('accounts/login.html',{'form':form,'msg':msg},context_instance=RequestContext(request))

@login_required
def logout(request):
	auth_logout(request)
	return HttpResponseRedirect('/')

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
	# print request.session['request_token']

	url = "%s?oauth_token=%s" % (authorize_url, request.session['request_token']['oauth_token'], )

	# print url

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
	
	# print access_token
	
	fields = "(headline,id,firstName,lastName)"

	api_url = "http://api.linkedin.com/v1/people/~:" + fields + "?format=json"
	 
	token = oauth.Token(
		key=access_token['oauth_token'], 
		secret=access_token['oauth_token_secret'])


	client = oauth.Client(consumer, token)

	resp, content = client.request(api_url)

	# linkedin_user_info = dict(cgi.parse_qsl(content))
	linkedin_user_info = simplejson.loads(content)
	# print linkedin_user_info
	# check to see if user already registered (maybe went through registration process again by mistake

	# li_user = user_already_registered_li(linkedin_user_info['id'])
	# try:
		# login and redirect to search page
		# print linkedin_user_info['id']
	request.session['_auth_user_backend'] = 'prosperime.accounts.backends.LinkedinBackend'
	user = authenticate(acct_id=linkedin_user_info['id'])
	
	if user is not None:
		auth_login(request,user)
		return HttpResponseRedirect('/')
	else:
	# except:
		# store information in a cookie
		request.session['linkedin_user_info'] = linkedin_user_info
		request.session['access_token'] = access_token

		# print request.session['linkedin_user_info']
	# check to see if user is currently logged in
	if request.user.is_authenticated():
		# if loged in, link accounts and return
		return HttpResponseRedirect('/account/link')
	else:
		# if not logged in, ask to finish user registration process
		return HttpResponseRedirect('/account/finish')

def finish_link(request):
	# get info for creating an account
	linkedin_user_info = request.session['linkedin_user_info']
	access_token = request.session['access_token']

	# create LinkedIn account
	acct = Account()
	acct.owner = request.user
	acct.access_token = access_token['oauth_token']
	acct.token_secret = access_token['oauth_token_secret']
	acct.service = 'linkedin'
	acct.expires_on = datetime.now() + timedelta(seconds=int(access_token['oauth_authorization_expires_in']))
	acct.uniq_id = linkedin_user_info['id']
	acct.save()

	messages.success(request, 'Your LinkedIn account has been successfully linked.')

	return HttpResponseRedirect('/search')

def finish_login(request):
	# TODO: redirect if not not authenticated through LinkedIn already
	# print request.session['access_token']
	# print request.session['linkedin_user_info']
	
	if request.POST:
		
		# print request.session['access_token']
		# print request.session['linkedin_user_info']
		linkedin_user_info = request.session['linkedin_user_info']
		access_token = request.session['access_token']
		# form submitted

		form = FinishAuthForm(request.POST)
		
		if form.is_valid():
			username = form.cleaned_data['username']
			email = form.cleaned_data['email']
			password = form.cleaned_data['password']

			# save user
			user = User.objects.create_user(username,email,password)
			user.save()

			# make sure using right backend
			request.session['_auth_user_backend'] = 'prosperime.accounts.backends.LinkedinBackend'
			# log user in
			user = authenticate(username=username,password=password)
			# make sure authentication worked
			if user is not None:
				auth_login(request,user)
			else:
				# somehow authentication failed, redirect with error message
				messages.error(request, 'Something went wrong. Please try again.')
				return render_to_response('accounts/finish_login.html',{'form':form,'error_message':error_message},context_instance=RequestContext(request))


			# update user profile
			# user.profile.full_name = request.session['linkedin_user_info']['firstName'] + " " + request.session['linkedin_user_info']['lastName']
			
			user.profile.first_name = linkedin_user_info['firstName']
			user.profile.last_name = linkedin_user_info['lastName']
			user.profile.headline = linkedin_user_info['headline']
			user.profile.save()

			# create LinkedIn account
			acct = Account()
			acct.owner = user
			acct.access_token = access_token['oauth_token']
			acct.token_secret = access_token['oauth_token_secret']
			acct.service = 'linkedin'
			acct.expires_on = datetime.now() + timedelta(seconds=int(access_token['oauth_authorization_expires_in']))
			acct.uniq_id = linkedin_user_info['id']
			acct.save()

			# start processing connections

			call_command("liparse",acct_id=acct.id,user_id=user.id)

			return HttpResponseRedirect('/account/success')
	else:
		form = FinishAuthForm()

	return render_to_response('accounts/finish_login.html',{'form':form},context_instance=RequestContext(request))

def success(request):
	return render_to_response('accounts/success.html',context_instance=RequestContext(request))

	

	
