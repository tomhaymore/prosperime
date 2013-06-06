from celery import task
from lilib import LIConnections, LIProfile
import accounts.cblib as cblib
from careers.careerlib import CareerMapBase
## somewhat useful for celery debugging
# from celery.contrib import rdb

@task()
def add(x,y):
	return x + y

# class ProcessLIProfile(Task):

# 	def run(self,user_id,acct_id,**kwargs):

# 		# call LI parser object
# 		li_parser = LIProfile()

# 		li_parser.process_profile(user_id,acct_id)

# class ProcessLIConnections(Task):

# 	def run(self,user_id,acct_id,**kwargs):

# 		# call LI parser object
# 		li_cxn_parser = LIConnections(user_id,acct_id)

# 		li_cxn_parser.process_connections()

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
def match_position(pos):
	mapper = CareerMapBase()
	mapper.match_position_to_ideals(pos)

@task()
def process_cb_people():
	cb = cblib.CBPeople()
	cb.parse_people()

# tasks.register(ProcessLIProfile)
# tasks.register(ProcessLIConnections)