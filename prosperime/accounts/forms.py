# from Django
from django import forms
from django.contrib.auth.models import User

class FinishAuthForm(forms.Form):
	
	username = forms.CharField(label="Username")
	email = forms.EmailField(label="Email")
	location = forms.CharField(label="Location",required=False)
	headline = forms.CharField(label="Headline",required=False)
	password = forms.CharField(widget=forms.PasswordInput,label="Password")
	confirm_password = forms.CharField(widget=forms.PasswordInput,label="Confirm Password")

	def clean_username(self):
		username = self.cleaned_data['username']
		if username and User.objects.filter(username__exact=username).count():
			raise forms.ValidationError('That username is already taken. Please choose another.')
		else:
			return username


class AuthForm(forms.Form):
	username = forms.CharField(label="Username or Email")
	password = forms.CharField(widget=forms.PasswordInput,label="Password")