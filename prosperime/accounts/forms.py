# from Django
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.utils.safestring import mark_safe
from django.contrib.auth import authenticate

date_formats = [
		'%Y-%m-%d',       # '2006-10-25'
		'%m/%d/%Y',       # '10/25/2006'
		# '%m/%d/%y',		  # '10/25/06'
		# '%b %d %Y',      # 'Oct 25 2006'
		# '%b %d, %Y',      # 'Oct 25, 2006'
		# '%d %b %Y',       # '25 Oct 2006'
		# '%d %b, %Y',      # '25 Oct, 2006'
		# '%B %d %Y',       # 'October 25 2006'
		# '%B %d, %Y',      # 'October 25, 2006'
		# '%d %B %Y',       # '25 October 2006'
		# '%d %B, %Y'      # '25 October, 2006'
		'%Y-%m',
		'%m/%y',
		'%m/%Y',
		'%b %Y',
		'%B %Y',
		'%Y'
		]

class TermsField(forms.BooleanField):
	"Check that user agreed, return custom message."

	def validate(self,value):
		if not value:
			raise forms.ValidationError('You must agree to the Terms of Service and Privacy Policy to use Prospr.me.')
		else:	 
			super(TermsField, self).validate(value)

class EmailUnsubscribeForm(forms.Form):

	email = forms.EmailField(label="Email",required=True)

class RegisterForm(forms.Form):
	error_css_class = 'form_error'
	required_css_class = 'form_required'

	full_name = forms.CharField(label="Full name")

	username = forms.CharField(label="Username")

	email = forms.EmailField(label="Email",required=False)
	location = forms.CharField(label="Location",required=False)
	headline = forms.CharField(label="Headline",required=False)
	password = forms.CharField(widget=forms.PasswordInput,label="Password")
	confirm_password = forms.CharField(widget=forms.PasswordInput,label="Confirm Password")
	terms = forms.BooleanField(required=True,
								label=mark_safe("I have read and understand the <a href='/terms'>Terms of Service</a> and <a href='/privacy'>Privacy Policy</a>."),
								error_messages={'required':'You must agree to the Terms of Service and Privacy Policy to use ProsperMe.'})
	notification = forms.BooleanField(required=False,label=mark_safe("Please keep me updated on changes and improvements to ProsperMe."))

	def clean_username(self):
		username = self.cleaned_data['username']
		if username and User.objects.filter(username__exact=username).count():
			raise forms.ValidationError('That email is already taken. Please choose another.')
		else:
			return username

	def clean_confirm_password(self):
		password1 = self.cleaned_data['password']
		password2 = self.cleaned_data['confirm_password']

		if password1 != password2:
			raise forms.ValidationError('Passwords must match. Please try re-entering your password.')
		else:
			return password2

	def clean_terms(self):
		terms = self.cleaned_data['terms']
		if not terms:
			raise forms.ValidationError('You must agree to the Terms of Service and Privacy Policy to use Prospr.me.')
		else:
			return terms



class FinishAuthForm(forms.Form):
	error_css_class = 'form_error'
	required_css_class = 'form_required'
	username = forms.CharField(label="Username")

	email = forms.EmailField(label="Email",required=False)
	location = forms.CharField(label="Location",required=False)
	headline = forms.CharField(label="Headline",required=False)
	password = forms.CharField(widget=forms.PasswordInput,label="Password")
	confirm_password = forms.CharField(widget=forms.PasswordInput,label="Confirm Password")
	terms = forms.BooleanField(required=True,
							label=mark_safe("I have read and understand the <a href='/terms'>Terms of Service</a> and <a href='/privacy'>Privacy Policy</a>."),
							error_messages={'required':'You must agree to the Terms of Service and Privacy Policy to use Prospr.me.'})
	notification = forms.BooleanField(required=False,label=mark_safe("Please keep me updated on changes and improvements to Prosper.me."))
	
	def clean_username(self):
		username = self.cleaned_data['username']
		if username and User.objects.filter(username__exact=username).count():
			raise forms.ValidationError('That username is already taken. Please choose another.')
		else:
			return username

	def clean_confirm_password(self):
		password1 = self.cleaned_data['password']
		password2 = self.cleaned_data['confirm_password']

		if password1 != password2:
			raise forms.ValidationError('Passwords must match. Please try re-entering your password.')
		else:
			return password2

	def clean_terms(self):
		terms = self.cleaned_data['terms']
		if not terms:
			raise forms.ValidationError('You must agree to the Terms of Service and Privacy Policy to use Prospr.me.')
		else:
			return terms

class AddEducationForm(forms.Form):
	degree = forms.CharField(label="Degree")
	field = forms.CharField(label="Field of Study",required=False)
	school = forms.CharField(label="School")
	end_date = forms.DateField(label="End date",input_formats=date_formats)

class AddExperienceForm(forms.Form):
	title = forms.CharField(label="Title")
	description = forms.CharField(label="Description",required=False)
	entity = forms.CharField(label="Organization")
	start_date = forms.DateField(label="Start date",input_formats=date_formats,required=False)
	end_date = forms.DateField(label="End date",input_formats=date_formats,required=False)

class AddGeographyForm(forms.Form):
	region = forms.CharField(label="Region")

class AddGoalForm(forms.Form):
	goal = forms.CharField(label="Goal")

class AddProfilePicForm(forms.Form):
	pic = forms.FileField(label="Profile picture")

class AuthForm(AuthenticationForm):
	# error_css_class = 'form_error'
	# required_css_class = 'form_required'

	username = forms.CharField(label="Username or Email")
	password = forms.CharField(widget=forms.PasswordInput,label="Password")

	def check_for_test_cookie(self):
		return None

	# def clean(self):
	# 	username = self.cleaned_data.get('username')
	# 	password = self.cleaned_data.get('password')

	# 	if username and password:
	# 		self.user_cache = authenticate(username=username,
 #                                           password=password)
	# 		if self.user_cache is None:
	# 			raise forms.ValidationError(self.error_messages['invalid_login'] % {'username': self.username_field.verbose_name})
	# 		elif not self.user_cache.is_active:
	# 			raise forms.ValidationError(self.error_messages['inactive'])
	# 			return self.cleaned_data
	# pass