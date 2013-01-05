"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

LI_CO_DATA = {u'industries': {u'_total': 1, u'values': [{u'code': u'6', u'name': u'Internet'}]}, u'status': {u'code': u'OPR', u'name': u'Operating'}, u'description': u'LinkedIn takes your professional network online, giving you access to people, jobs and opportunities like never before. Built upon trusted connections and relationships, LinkedIn has established the world\u2019s largest and most powerful professional network. Currently, more than 187 million professionals are on LinkedIn, including executives from all five hundred of the Fortune 500 companies, as well as a wide range of household names in technology, financial services, media, consumer packaged goods, entertainment, and numerous other industries. The company is publicly held and has a diversified business model with revenues coming from user subscriptions, advertising sales and hiring solutions.', u'twitterId': u'linkedin', u'locations': {u'_total': 4, u'values': [{u'description': u'', u'address': {u'postalCode': u'94043'}}, {u'description': u'Customer Service Office', u'address': {u'postalCode': u'68114'}}, {u'description': u'', u'address': {u'postalCode': u'02478'}}, {u'description': u'Post Montgomery Center', u'address': {u'postalCode': u'94104'}}]}, u'employeeCountRange': {u'code': u'G', u'name': u'1001-5000'}, u'websiteUrl': u'http://www.linkedin.com', u'logoUrl': u'http://m3.licdn.com/mpr/mpr/p/3/000/124/1a6/089a29a.png', u'stockExchange': {u'code': u'NYS', u'name': u'New York Stock Exchange'}, u'universalName': u'linkedin', u'ticker': u'LNKD', u'id': 1337, u'companyType': {u'code': u'C', u'name': u'Public Company'}, u'name': u'LinkedIn'}

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
