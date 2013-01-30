# Python imports
import csv
from optparse import make_option

# Django imports
from django.core.management.base import BaseCommand, CommandError
from entities.models import Career


class Command(BaseCommand):
	
	option_list = BaseCommand.option_list + (
			make_option('-u',
						action="store_true",
						dest="update"),
			make_option('-c',
						action="store_true",
						dest="clean"),
		)

	def handle(self,*args, **options):
		
		f = open('/Users/thaymore/Projects/prosperime/prosperime/careers.csv','rU')
		c = csv.DictReader(f)
		for row in c:
			if row['id']:
				career = Career.objects.get(pk=row['id'])
				titles = career.get_pos_titles()
				if row['titles'] is not None and row['titles'] is not "":
					new_titles = row['titles'].split(',')
					for t in new_titles:
						if titles is not None:
							if t not in titles:
								career.add_pos_title(t)
						else:
							career.add_pos_title(t)
				career.save()
			else:
				career = Career()
				career.short_name = row['name']
				career.long_name = row['name']
				career.save()
				if row['titles'] is not None and row['titles'] is not "":
					new_titles = row['titles'].split(',')
					for t in new_titles:
						career.add_pos_title(t)
				career.save()
		
			
			