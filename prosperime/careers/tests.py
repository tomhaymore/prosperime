
# from Django
from django.test import TestCase
from django.utils import unittest

# from prosperme
import careers.careerlib as careerlib
from careers.models import Position

class IdealPositionTest(TestCase):
	
	fixtures = ['all_data_20130528.json']

	def test_position_match_any_ideals(self):
		"""
		tests that there is at least one position -> ideal position match
		"""
		positions = Position.objects.all()
		matches = False
		for p in positions:
			if careerlib.match_position_to_ideals(p,True):
				matches = True
				break
		self.assertTrue(matches)

