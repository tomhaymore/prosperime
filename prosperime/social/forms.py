# from Django
from django import forms

# from prosperime
from social.models import Tag

class RecruiterInterestForm(forms.Form):

	email = forms.EmailField(label="Email",required=True)

class ConversationForm(forms.Form):

	name = forms.CharField(label="Title")
	summary = forms.CharField(label="Summary")
	tags = forms.ModelMultipleChoiceField(required=False,queryset=Tag.objects.all())
