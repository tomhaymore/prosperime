# from Django
from django import forms
from django.contrib.auth.models import User

# from prosperime
from social.models import Conversation,Tag

class RecruiterInterestForm(forms.Form):

	email = forms.EmailField(label="Email",required=True)

class ConversationForm(forms.Form):

	name = forms.CharField(label="Title")
	summary = forms.CharField(label="Summary")
	tags = forms.ModelMultipleChoiceField(required=False,queryset=Tag.objects.all())

class AskAdvisorForm(forms.Form):

	user = forms.ModelChoiceField(queryset=User.objects.filter(profile__status="active"))
	advisor = forms.ModelChoiceField(queryset=User.objects.filter(profile__status="active"))
	subject = forms.CharField(label="Subject")
	body = forms.CharField(label="Body")
	method = forms.CharField(label="Method")
	question = forms.ModelChoiceField(queryset=Conversation.objects.all())

