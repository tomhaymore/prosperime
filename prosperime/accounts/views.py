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
from django.contrib import messages
from lilib import LIProfile
from accounts.tasks import process_li_profile, process_li_connections

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

	return render_to_response('accounts/login.html',{'form':form},context_instance=RequestContext(request))

@login_required
def logout(request):
	auth_logout(request)
	return HttpResponseRedirect('/')

def linkedin_authorize(request):
	
	# # set scope
	# scope = 'r_fullprofile+r_emailaddress+r_network'

	# # set callback
	# callback = 'http://127.0.0.1:8000/account/authenticate/'

	# # set urls
	# request_token_url	= 'https://api.linkedin.com/uas/oauth/requestToken'
	# # access_token_url	= 'https://api.linkedin.com/uas/oauth/accessToken'
	# authorize_url		= 'https://www.linkedin.com/uas/oauth/authenticate'

	# # setup OAuth
	# consumer = oauth.Consumer(linkedin_key, linkedin_secret)
	# client = oauth.Client(consumer)

	# request_token_url = "%s?scope=%s" % (request_token_url, scope, )

	# # get request token
	# resp, content = client.request(request_token_url,"POST")
	# if resp['status'] != '200':
	# 	raise Exception(content)
	
	liparser = LIProfile()

	redirect_url, request_token = liparser.authorize()

	# parse out request token

	# request.session['request_token'] = dict(cgi.parse_qsl(content))
	request.session['request_token'] = request_token

	# redirect_url = "%s?oauth_token=%s" % (authorize_url, request.session['request_token']['oauth_token'], )

	# print url

	return HttpResponseRedirect(redirect_url)
  
# @login_required
def linkedin_authenticate(request):  
	# consumer = oauth.Consumer(linkedin_key, linkedin_secret)
	
	# access_token_url = 'https://api.linkedin.com/uas/oauth/accessToken'

	# token = oauth.Token(request.session['request_token']['oauth_token'],request.session['request_token']['oauth_token_secret'])
	# token.set_verifier(request.GET['oauth_verifier'])
	# client = oauth.Client(consumer, token)

	# resp, content = client.request(access_token_url, "POST")

	# access_token = dict(cgi.parse_qsl(content))
	
	# # print access_token
	
	# fields = "(headline,id,first-name,last-name,picture-url)"

	# api_url = "http://api.linkedin.com/v1/people/~:" + fields + "?format=json"
	 
	# token = oauth.Token(
	# 	key=access_token['oauth_token'], 
	# 	secret=access_token['oauth_token_secret'])

	# client = oauth.Client(consumer, token)

	# resp, content = client.request(api_url)

	# linkedin_user_info = simplejson.loads(content)
	liparser = LIProfile()

	access_token, linkedin_user_info = liparser.authenticate(request.session['request_token'],request.GET['oauth_verifier'])
	# print linkedin_user_info
	
	# check if user is already logged on

	request.session['linkedin_user_info'] = linkedin_user_info
	request.session['access_token'] = access_token
	
	if request.user.is_authenticated():
		# if loged in, link accounts and return
		return HttpResponseRedirect('/account/link')

	request.session['_auth_user_backend'] = 'prosperime.accounts.backends.LinkedinBackend'
	
	user = authenticate(acct_id=linkedin_user_info['id'])
	# print user
	# print linkedin_user_info['id']
	if user is not None:
		auth_login(request,user)
		return HttpResponseRedirect('/')
	else:
		# store information in a cookie
		request.session['linkedin_user_info'] = linkedin_user_info
		request.session['access_token'] = access_token

	# check to see if user is currently logged in
	if request.user.is_authenticated():
		# if loged in, link accounts and return
		return HttpResponseRedirect('/account/link')
	else:
		# if not logged in, ask to finish user registration process
		return HttpResponseRedirect('/account/finish')


def finish_login(request):
	# TODO: redirect if not not authenticated through LinkedIn already
	
	if request.POST:
		# form submitted

		linkedin_user_info = request.session['linkedin_user_info']
		access_token = request.session['access_token']

		form = FinishAuthForm(request.POST)
		
		if form.is_valid():
			username = form.cleaned_data['username']
			email = form.cleaned_data['email']
			password = form.cleaned_data['password']

			# check to see if dormant user already exists
			try: 
				user = User.objects.get(status="dormant",account__uniq_id=linkedin_user_info['id'])
				existing = True
			except:
				# create user
				user = User.objects.create_user(username,email,password)
				user.save()
				existing = False

			# make sure using right backend
			request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
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

			# add pofile picture
			if 'pictureUrl' in linkedin_user_info:
				_add_profile_pic(user,linkedin_user_info['pictureUrl'])


			
			if existing:
				# get existing LI account
				acct = Account.objects.get(owner=user,service="linkedin")
			else:
				# create LinkedIn account
				acct = Account()
			acct.owner = user
			acct.access_token = access_token['oauth_token']
			acct.token_secret = access_token['oauth_token_secret']
			acct.service = 'linkedin'
			acct.expires_on = datetime.now() + timedelta(seconds=int(access_token['oauth_authorization_expires_in']))
			acct.uniq_id = linkedin_user_info['id']
			acct.status = "active"
			acct.save()

			# finish processing LI profile
			process_li_profile.delay(user.id,acct.id)

			# start processing connections
			process_li_connections.delay(user.id,acct.id)

			return HttpResponseRedirect('/account/success')
	else:
		form = FinishAuthForm()

	return render_to_response('accounts/finish_login.html',{'form':form},context_instance=RequestContext(request))


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

	# finish processing LI profile
	process_li_profile.delay(request.user.id,acct.id)

	# start processing connections
	process_li_connections.delay(request.user.id,acct.id)

	messages.success(request, 'Your LinkedIn account has been successfully linked.')

	return HttpResponseRedirect('/search')

def success(request):
	return render_to_response('accounts/success.html',context_instance=RequestContext(request))

def _add_profile_pic(user,img_url):
	img = None
	img_ext = urlparse.urlparse(img_url).path.split('/')[-1].split('.')[1]
	img_filename = user.profile.std_name() + "." + img_ext
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
	

	
