# from python

# from Django
from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

# from prosperme

class WelcomeEmail():
	"""
	Thin wrapper around Django email classes
	"""
	msg = None

	backend = EmailBackend()

	# basic email settings
	subject = "Welcome to ProsperMe!"
	origin = "welcome@prospr.me"

	# fetch templates
	plaintext = get_template('templates/accounts/emails/welcome_email.txt')
	htmlformat    = get_template('templates/accounts/emails/welcome_email.html')



	def __init__(self,user):
		# get context for email message
		d = Context({
			'full_name':user.profile.full_name()
			})
		text_content = self.plaintext.render(d)
		html_content = self.htmlformat.render(d)
		self.msg = EmailMultiAlternatives(self.subject,text_content,self.origin,user.email)
		self.msg.attach_alternative(html_content, "text/html")
		self.backend.open()

	def send_email():
		self.backend.send_messages(self.msg)
		self.backend.close()

