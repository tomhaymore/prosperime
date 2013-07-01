# from Django
from django import forms

class RecruiterInterestForm(forms.Form):

	email = forms.EmailField(label="Email",required=True)
