"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

# from Django
from django.test import TestCase
from django.utils import unittest

class IdealPositionTest(TestCase):
	import careers.careerlib as careerlib
	from careers.models import Position
	# fixtures = ['test_idealpos_20130402.json']

	def test_position_match_any_ideals(self):
		"""
		tests that there is at least one position -> ideal position match
		"""
		positions = self.Position.objects.all()
		matches = False
		for p in positions:
			if self.careerlib.match_position_to_ideals(p):
				matches = True
				break
		self.assertTrue(matches)



class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
