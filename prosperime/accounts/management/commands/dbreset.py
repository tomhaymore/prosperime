# from Python
from optparse import make_option

# from Django
from django.contrib.auth.models import User
from accounts.models import Profile, Connection
from entities.models import Position
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

	option_list = BaseCommand.option_list + (
			# option for storing user id
			make_option('-u','--users',
						action="store_true",
						dest="users"),
			# option for storing acct id
			make_option('-x','--connections',
						action="store_true",
						dest="connections"),
			make_option('-p','--positions',
						action="store_true",
						dest="positions"),
			make_option('-a','--all',
						action="store_true",
						dest="all"),
		)

	def handle(self,*args, **options):

		if options['all']:
			# reset all users save admin
			users = User.objects.exclude(pk=1)
			users.delete()

			# reset all connections
			cxns = Connection.objects.all()
			cxns.delete()

			# reset all positions
			positions = Position.objects.all()
			positions.delete()
		elif options['users']:
			# reset all users save admin
			users = User.objects.exclude(pk=1)
			users.delete()
		elif options['connections']:
			# reset all connections
			cxns = Connection.objects.all()
			cxns.delete()
		elif options['positions']:
			# reset all positions
			positions = Position.objects.all()
			positions.delete()

