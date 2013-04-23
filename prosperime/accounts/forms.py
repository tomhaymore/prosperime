# from Django
from django import forms

class FinishAuthForm(forms.Form):
	username = forms.CharField(label="Username")
	email = forms.EmailField(label="Email")
	location = forms.CharField(label="Location")
	headline = forms.CharField(label="Headline")
	password = forms.CharField(widget=forms.PasswordInput,label="Password")
	confirm_password = forms.CharField(widget=forms.PasswordInput,label="Confirm Password")

	def clean_username():
		username = self.cleaned_data['username']
		if username and User.objects.get(username__exact=username).count():
			raise forms.ValidationError(u'That username is already taken. Please choose another.')
		except:
			return username


class AuthForm(forms.Form):
	username = forms.CharField(label="Username or Email")
	password = forms.CharField(widget=forms.PasswordInput,label="Password")

class UsernameField