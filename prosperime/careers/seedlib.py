import os
import random

from entities.models import Industry, Entity
from accounts.models import Profile
from django.contrib.auth.models import User
from careers.models import SavedIndustry


class SeedBase():

	seed_to_industry_map = {

		"Automotive":["elon_musk",],
		"Banking":["michael_bloomberg",],
		"Biotech":["eric_lander",],
		"Biotechnology":["eric_lander",],

		"Broadcast Media":["reed_hastings",],

		"Computer Hardware":["jony_ive",],
		"Computer Software":["elon_musk","reed_hastings",],
		"Consumer Electronics":["jony_ive",],


		"Defense & Space":["elon_musk",],
		"Design":["jony_ive"],

		"Entertainment":["reed_hastings",],
		"Financial Services":["michael_bloomberg", "mary_meeker"],
		"Food & Beverages":["howard_schultz",],
		"Fundraising":["mary_meeker",],
		"Government Administration":["paul_clement","michael_bloomberg"],


		"Internet":["elon_musk","reed_hastings", "mary_meeker"],
		"Investment Banking/Venture":["michael_bloomberg", "mary_meeker"],
		"Investment Management":["michael_bloomberg",],

		"Judiciary":["paul_clement",],

		"Law Practice":["paul_clement",],
		"Legal Services":["paul_clement",],
		"Life Sciences":["eric_lander",],

		"Market Research":["mary_meeker",],
		"Marketing & Advertising":["howard_schultz",],
		"Mechanical or Industrial Engineering":["jony_ive",],
		"Medical Devices":["eric_lander",],
		"Military":["reed_hastings",],
		"Pharmaceuticals":["eric_lander",],
		"Philanthropy":["michael_bloomberg"],
		"Political Organization":["nate_silver", "paul_clement", "michael_bloomberg"],
		"Public Policy":["michael_bloomberg",],

		"Renewables & Environment":["elon_musk",],
		"Research":["eric_lander",],

		"Restaurants":["howard_schultz",],
		"Restaurants & Food Service":["howard_schultz",],

		"Sports":["nate_silver"],
		"Think Tanks":["eric_lander",],
		"Venture Capital":["mary_meeker"],
		"Writing & Editing":["nate_silver"],
	}

	prefix = "careers/seed_people/"
	suffix = ".json"

	def __init__(self):
		stage = os.environ.get('PROSPR_ENV',None)
		if stage is None:
			prefix = "careers/seed_people/"
		elif stage == 'production' or stage == 'staging':
			prefix = "/app/prosperime/careers/seed_people/"

	def test(self):

		rand_max = User.objects.all()
		rand = random.randint(600,len(rand_max))
		user = User.objects.get(id=rand)
		print user.profile.full_name() + ' '  +str(user.id)
		print str(len(user.positions.all())) + ' positions'
		self.get_seeds(user)


	def get_seeds(self,user,**opts):

		## For Dev to test all industries
		# ind_names = [str(i.name) for i in Industry.objects.all()]
		
		# # Grab your related inds and saved inds
		ind_names = [str(i.name) for i in user.profile._industries()]
		saved_industries = [str(saved_ind.industry.name) for saved_ind in SavedIndustry.objects.filter(owner=user)]
		ind_names.extend(saved_industries)
		print ind_names

		# Iterate through and return JSON people
		seed_filenames = []
		print ind_names
		for i in ind_names:
			if i in self.seed_to_industry_map:
				for s in self.seed_to_industry_map[i]:
					filename = self.prefix + s + self.suffix
					if filename not in seed_filenames:
						seed_filenames.append(filename)
			else:
				print "@seedlib, no industry match: " + i

		# If no matches, default to Reed Hastings
		if not seed_filenames:
			seed_filenames.append(self.prefix + "reed_hastings" + self.suffix)

		return seed_filenames










