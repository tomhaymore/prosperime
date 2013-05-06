# from Django
from django import forms
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

class TermsField(forms.Field):
	"Check that user agreed, return custom message."

	def validate(self,value):
		if not value:
			raise forms.ValidationError('You must agree to the Terms of Service and Privacy Policy to use Prospr.me.')
		else:	 
			super(TermsField, self).validate(value)

class FinishAuthForm(forms.Form):
	
	username = forms.CharField(label="Username")
	email = forms.EmailField(label="Email")
	location = forms.CharField(label="Location",required=False)
	headline = forms.CharField(label="Headline",required=False)
	password = forms.CharField(widget=forms.PasswordInput,label="Password")
	confirm_password = forms.CharField(widget=forms.PasswordInput,label="Confirm Password")
	terms = TermsField(label=mark_safe("I have read and understand the <a href='/terms'>Terms of Service</a> and <a href='/privacy'>Privacy Policy</a>."),required=True)

	def clean_username(self):
		username = self.cleaned_data['username']
		if username and User.objects.filter(username__exact=username).count():
			raise forms.ValidationError('That username is already taken. Please choose another.')
		else:
			return username

	def clean_terms(self):
		terms = self.cleaned_data['terms']
		if not terms:
			raise forms.ValidationError('You must agree to the Terms of Service and Privacy Policy to use Prospr.me.')
		else:
			return terms

class AuthForm(forms.Form):
	username = forms.CharField(label="Username or Email")
	password = forms.CharField(widget=forms.PasswordInput,label="Password")