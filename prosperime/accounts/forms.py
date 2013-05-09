# from Django
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.utils.safestring import mark_safe
from django.contrib.auth import authenticate

class TermsField(forms.BooleanField):
	"Check that user agreed, return custom message."

	def validate(self,value):
		if not value:
			raise forms.ValidationError('You must agree to the Terms of Service and Privacy Policy to use Prospr.me.')
		else:	 
			super(TermsField, self).validate(value)

class RegisterForm(forms.Form):
	error_css_class = 'form_error'
	required_css_class = 'form_required'

	username = forms.CharField(label="Username")
	email = forms.EmailField(label="Email")
	location = forms.CharField(label="Location",required=False)
	headline = forms.CharField(label="Headline",required=False)
	password = forms.CharField(widget=forms.PasswordInput,label="Password")
	confirm_password = forms.CharField(widget=forms.PasswordInput,label="Confirm Password")
	terms = forms.BooleanField(required=True,
								label=mark_safe("I have read and understand the <a href='/terms'>Terms of Service</a> and <a href='/privacy'>Privacy Policy</a>."),
								error_messages={'required':'You must agree to the Terms of Service and Privacy Policy to use Prospr.me.'})

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

class FinishAuthForm(forms.Form):
	error_css_class = 'form_error'
	required_css_class = 'form_required'

	username = forms.CharField(label="Username")
	email = forms.EmailField(label="Email")
	location = forms.CharField(label="Location",required=False)
	headline = forms.CharField(label="Headline",required=False)
	password = forms.CharField(widget=forms.PasswordInput,label="Password")
	confirm_password = forms.CharField(widget=forms.PasswordInput,label="Confirm Password")
	terms = forms.BooleanField(required=True,
							label=mark_safe("I have read and understand the <a href='/terms'>Terms of Service</a> and <a href='/privacy'>Privacy Policy</a>."),
							error_messages={'required':'You must agree to the Terms of Service and Privacy Policy to use Prospr.me.'})

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