# Python
import logging

# Django
from celery import task

# Prosperime
from lilib import LIConnections, LIProfile, LIUpdate
import accounts.cblib as cblib
from careers.careerlib import CareerMapBase
## somewhat useful for celery debugging
# from celery.contrib import rdb

logger = logging.getLogger(__name__)

@task()
def add(x,y):
	return x + y

@task()
def process_li_connections(user_id,acct_id,**kwargs):

	# call LI parser object
	li_cxn_parser = LIConnections(user_id,acct_id)
	li_cxn_parser.process_connections()

@task()
def process_li_profile(user_id,acct_id,**kwargs):

	# call LI parser object
	# li_parser = LIProfile(career_mapper)
	li_parser = LIProfile()
	li_parser.process_profile(user_id,acct_id)

@task()
def update_li_profile(user_id,acct_id,**kwargs):
	print LIUpdate
	li_updater = LIUpdate()
	li_updater.update_profile(user_id, acct_id)

@task()
def match_position(pos):
	mapper = CareerMapBase()
	mapper.match_position_to_ideals(pos)

@task()
def process_cb_people():
	cb = cblib.CBPeople()
	cb.parse_people()

@task()
def send_welcome_email(user):
	import accounts.emaillib as emaillib
	welcome = emaillib.WelcomeEmail(user)
	welcome.send_email()
	logger.info("sent welcome email to user: "+user.email)

# tasks.register(ProcessLIProfile)
# tasks.register(ProcessLIConnections)