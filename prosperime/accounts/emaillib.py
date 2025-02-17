# from python
import logging
import csv
import mandrill
# from smtplib import SMTPRecipientRefused

# from Django
from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

# from prosperme

logger = logging.getLogger(__name__)

class EmailBase():
	msg = None

	client = mandrill.Mandrill("IT3A1T6VpHnqHhwdg9Kbsg")

	def trigger(self):
		res = self.client.messages.send(message=self.msg)
		return res

class NotificationEmail(EmailBase):

	def __init__(self,text):
		d = Context({
				'text':text
			})
		text_content = get_template('emails/notification_email.txt').render(d)
		html_content = get_template('emails/notification_email.html').render(d)
		self.msg = {
			'from_email':'admin@prospr.me',
			'from_name':'ProsperMe',
			'text':text_content,
			'html':html_content,
			'subject':"New email to blocklist",
			'track_clicks':False,
			'track_opens':False,
			'to':[{'name':'admins','email':'admin@prospr.me'}]
		}

class MarketingEmail(EmailBase):

	def __init__(self,**params):
		# pass params to context
		d = Context(params['template_vars'])
		# render html and text versions
		text_content = get_template('emails/'+params['template']+'.txt').render(d)
		html_content = get_template('emails/'+params['template']+'.html').render(d)
		# compile message attributes
		self.msg = {
			'from_email':'admin@prospr.me',
			'from_name':'ProsperMe',
			'text':text_content,
			'html':html_content,
			'subject':params['subject'],
			'track_clicks':True,
			'track_opens':True,
			'google_campaign_name':'prosper_welcome',
			'tags':['marketing','career-services'],
			'to':[{'name':params['name'],'email':params['email_address']}]
		}

class WelcomeEmail():
	"""
	Thin wrapper around Mandrill client
	"""

	msg = None

	client = None

	def __init__(self,user):
		d = Context({
			'full_name':user.profile.full_name()
			})
		text_content = get_template('emails/welcome_email.txt').render(d)
		html_content = get_template('emails/welcome_email.html').render(d)
		self.msg = {
			'from_email':'welcome@prospr.me',
			'from_name':'ProsperMe',
			'text':text_content,
			'html':html_content,
			'subject': "Welcome to ProsperMe!",
			'track_clicks': True,
			'track_opens':True,
			'google_campaign_name':'prosper_welcome',
			'to':[{'name':user.profile.full_name(),'email':user.email}]
		}

	def trigger(self):
		self.client = mandrill.Mandrill("IT3A1T6VpHnqHhwdg9Kbsg")
		res = self.client.messages.send(message=self.msg)
		return res

	# msg = None

	# backend = EmailBackend()

	# # basic email settings
	# subject = "Welcome to ProsperMe!"
	# origin = "ProsperMe <welcome@prospr.me>"

	# # fetch templates
	# plaintext = get_template('emails/welcome_email.txt')
	# htmlformat    = get_template('emails/welcome_email.html')



	# def __init__(self,user):
	# 	# get context for email message
	# 	d = Context({
	# 		'full_name':user.profile.full_name()
	# 		})
	# 	text_content = self.plaintext.render(d)
	# 	html_content = self.htmlformat.render(d)
	# 	self.msg = EmailMultiAlternatives(self.subject,text_content,self.origin,[user.email])
	# 	self.msg.attach_alternative(html_content, "text/html")

	# 	self.backend.open()

	# def send_email(self):
	# 	self.backend.send_messages([self.msg])
	# 	self.backend.close()

class UniversityEmail():
	msg = None
	emailed = []
	backend = EmailBackend()

	# basic message settings
	subject = "ProsperMe -- A new tool for exploring career paths for your major"
	origin = "ProsperMe <welcome@prospr.me>"
	sender = None
	# fetch templates
	plaintext = get_template('emails/univ_departments_A1.txt')
	htmlformat = get_template('emails/univ_departments_A1.html')

	def __init__(self):
		# open backend
		pass
	
	def process_emails(self,owner,path,round):
		
		# open file
		f = open(path,'rU')
		# convert to dict object
		c = csv.DictReader(f)
		# loop thruogh each row
		for row in c:
			# check to make sure it hasn't already been emailed
			if row['Emailed'] == "Y":
				continue
			# check to make sure it's the right round
			if int(row["Round"]) != round:
				continue
			# check to make sure that it's a valid email address
			if not row["Email"] or row["Email"] == "":
				continue
			# compile
			if row["First Name"]:
				first_name = row["First Name"]
			elif row["Last Name"]:
				first_name = row["Last Name"]
			else:
				first_name = None
			email = row["Email"]
			# logger.info((owner,fullname,email,))
			if email not in self.emailed:
				self.send_univ_email(owner,first_name,email)

	def send_univ_email(self,owner,name,address):
		d = Context({
				'first_name':name,
				'owner':owner
			})
		text_content = self.plaintext.render(d)
		html_content = self.htmlformat.render(d)
		self.msg = EmailMultiAlternatives(self.subject,text_content,self.origin,[address])
		self.msg.bcc = ["admin@prospr.me"]
		self.msg.attach_alternative(html_content, "text/html")
		self.msg.attach_file('/Users/tchaymore/prosperime/prosperime/static/img/prosperme_demo_1.png','image/png')
		self.send_email()

	def send_email(self):
		try:
			self.backend.send_messages([self.msg])
			logger.info("Email sent: " + str(self.msg.to))
			self.emailed.append(self.msg.to)
		# except SMTPRecipientRefused as e:
		# 	logger.info("Email recipient refused: " + str(self.msg.to) + " " + str(e))
		except Exception as e:
			logger.error("Email error: " + str(e))
		# TODO: move this to destructor
		# self.backend.close()

class CareerEmail():
	msg = None

	backend = EmailBackend()

	# basic message settings
	subject = "ProsperMe -- A new tool for choosing college majors"
	origin = "ProsperMe <welcome@prospr.me>"
	sender = None
	# fetch templates
	plaintext = get_template('emails/career_services_A1.txt')
	htmlformat = get_template('emails/career_services_A1.html')

	def __init__(self):
		# open backend
		pass
	
	def process_emails(self,owner,path,round):
		
		# open file
		f = open(path,'rU')
		# convert to dict object
		c = csv.DictReader(f)
		# loop thruogh each row
		for row in c:
			# check to make sure it hasn't already been emailed
			if row['Emailed'] == "Y":
				continue
			# check to make sure it's the right round
			if int(row["Round"]) != round:
				continue
			# check to make sure that it's a valid email address
			if not row["Email"] or row["Email"] == "":
				continue
			# compile
			if row["First Name"] and row["Last Name"]:
				fullname = row["First Name"] + " " + row["Last Name"]
			elif row["First Name"]:
				fullname = row["First Name"]
			elif row["Last Name"]:
				fullname = row["Last Name"]
			else:
				fullname = None
			email = row["Email"]
			# logger.info((owner,fullname,email,))
			self.send_career_email(owner,fullname,email)

	def send_career_email(self,owner,name,address):
		d = Context({
				'full_name':name,
				'owner':owner
			})
		text_content = self.plaintext.render(d)
		html_content = self.htmlformat.render(d)
		self.msg = EmailMultiAlternatives(self.subject,text_content,self.origin,[address])
		self.msg.bcc = ["admin@prospr.me"]
		self.msg.attach_alternative(html_content, "text/html")
		self.msg.attach_file('/Users/tchaymore/prosperime/prosperime/static/img/prosperme_demo_1.png','image/png')
		self.send_email()

	def send_email(self):
		try:
			self.backend.send_messages([self.msg])
			logger.info("Email sent: " + str(self.msg.to))
		# except SMTPRecipientRefused as e:
		# 	logger.info("Email recipient refused: " + str(self.msg.to) + " " + str(e))
		except Exception as e:
			logger.error("Email error: " + str(e))
		# TODO: move this to destructor
		# self.backend.close()