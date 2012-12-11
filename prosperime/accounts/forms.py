# from Django
from django import forms

class FinishAuthForm(forms.Form):
	username = forms.CharField(label="Username")
	email = forms.EmailField(label="Email")
	password = forms.CharField(widget=forms.PasswordInput,label="Password")
	confirm_password = forms.CharField(widget=forms.PasswordInput,label="Confirm Password")

class AuthForm(forms.Form):
	username = forms.CharField(label="Username")
	password = forms.CharField(widget=forms.PasswordInput,label="Password")