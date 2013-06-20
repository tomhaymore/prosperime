# from Django
from django import forms

# from ProsperMe
import careers.careerlib as careerlib

class DegreeField(forms.CharField):
	"""
	Checks that user entered valid degree, returns standardized format
	"""
	def validate(self,value):
		if not careerlib.is_valid_degree(value):
			raise forms.ValidationError("Please enter a valid degree.")
		else:
			super(DegreeField, self).validate(value)


class AddProgressDetailsForm(forms.Form):
	
	# date formats for date fields
	date_formats = [
		# '%Y-%m-%d',       # '2006-10-25'
		# '%m/%d/%Y',       # '10/25/2006'
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

	title = forms.CharField(label="Position title",required=False)
	type = forms.CharField()
	degree = forms.CharField(label="Degree",required=False)
	field = forms.CharField(label="Field of study",required=False)
	entity = forms.CharField(label="Entity")
	start_date = forms.DateField(label="Start date",input_formats=date_formats,required=False)
	end_date = forms.DateField(label="End date",input_formats=date_formats)

	# def clean(self):
	# 	# get cleaned data
	# 	form_data = self.cleaned_data
	# 	# see what type of info has been submitted
	# 	if form_data['type'] == "education":
	# 		# validate degree
	# 		idealdegree = careerlib.match_degree(form_data['degree'])
	# 		if idealdegree:
	# 			form_data['degree'] = idealdegree.title
	# 			form_data['ideal_id'] = ideal.id
	# 		else:
	# 			# add an error
	# 			self._errors['degree'] = "Sorry, we don't recognize that degree."
	# 	# validate entity
	# 	entity = Entity.objects.filter(name__icontains=form_data['entity']).extra(order_by=[len("-name")])
	# 	if entity.exists():
	# 		form_data['entity'] = entity[0].id
	# 		# no visible error here because of low confidence in matching entities
	# 	# return data
	# 	return form_data


