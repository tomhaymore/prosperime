# from Python
from datetime import datetime, timedelta
# from Django
from django.db import Q
# from Prosperime

class FeedBase():
	
	def get_univ_feed(self,user,**opts):
		"""
		Gathers universal feed items and returns list of dict items

		Keyword args:
		user_id -- user id

		Default args (opts):
		timeline - 24 hours
		"""
		# set defaults

		timeline = opts['timeline'] if 'timeline' in opts else 24
		stop = datetime.now() - timedelta(hours = timeline)

		# get user connections and educations
		connections = [u.id for u in user.connections.all()]
		educations = [u.id for u in User.objects.filter(positions__entity_id__in=user.educations(),positions__type="education")]
		# retrieve data
		paths = SavedPath.objects.filter(Q(owner__in=connections) | Q(owner__in=educations)).filter(date_modified__gte=stop)
		positions = GoalPosition.objects.filter(Q(owner__in=connections) | Q(owner__in=educations)).filter(updated__gte=stop)

		# concatenate into one list
		unordered_feed = [{'type':'careerpath','id':p.id,'user_id':p.owner_id,'user_name':p.owner.profile.full_name(),'title':p.title,'date':p.date_modified} for p in paths]
		unordered_feed.extend([{'type':'goalposition','id':p.id,'user_id':p.owner_id,'user_name':p.owner.profile.full_name(),'title':p.title,'date':p.updated} for p in positions])

		ordered_feed = sorted(unordered_feed, key=operator.itemgetter('date'),reverse=True)

		return ordered_feed


