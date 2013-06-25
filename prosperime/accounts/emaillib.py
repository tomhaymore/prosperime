# from python
import logging

# from Django
from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

# from prosperme

logger = logging.getLogger(__name__)

class WelcomeEmail():
	"""
	Thin wrapper around Django email classes
	"""
	msg = None

	backend = EmailBackend()

	# basic email settings
	subject = "Welcome to ProsperMe!"
	origin = "ProsperMe <welcome@prospr.me>"

	# fetch templates
	plaintext = get_template('emails/welcome_email.txt')
	htmlformat    = get_template('emails/welcome_email.html')



	def __init__(self,user):
		# get context for email message
		d = Context({
			'full_name':user.profile.full_name()
			})
		text_content = self.plaintext.render(d)
		html_content = self.htmlformat.render(d)
		self.msg = EmailMultiAlternatives(self.subject,text_content,self.origin,[user.email])
		self.msg.attach_alternative(html_content, "text/html")

		self.backend.open()

	def send_email(self):
		self.backend.send_messages([self.msg])
		self.backend.close()

class CareerEmail():
	msg = None

	backend = EmailBackend()

	# basic message settings
	subject = "ProsperMe -- A new tool for choosing college majors"
	origin = "ProsperMe <welcome@prospr.me>"
	sender = None
	# fetch templates
	plaintext = get_template('emails/career_services_A1.txt')
	htmlformat    = get_template('emails/career_services_A1.html')

	def __init__(self):
		# open backend
		pass
		
	def send_career_email(self,owner,name,address):
		d = Context({
				'full_name':name,
				'owner':owner
			})
		text_content = self.plaintext.render(d)
		html_content = self.htmlformat.render(d)
		self.msg = EmailMultiAlternatives(self.subject,text_content,self.origin,[address])
		self.msg.attach_alternative(html_content, "text/html")
		self.msg.attach_file('/Users/tchaymore/prosperime/prosperime/static/img/prosperme_demo_1.png','image/png')
		self.send_email()

	def send_email(self):
		try:
			self.backend.send_messages([self.msg])
			logger.info("Email sent: " + str(self.msg.to))
		except SMTPRecipientRefused, e:
			logger.info("Email recipient refused: " + str(self.msg.to) + " " + str(e))
		except e:
			logger.error("Email error: " + str(e))
		# TODO: move this to destructor
		# self.backend.close()