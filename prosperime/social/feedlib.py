# from Python
from datetime import datetime, timedelta
import operator 
# from Django
from django.db.models import Q
from django.contrib.auth.models import User
# from Prosperime
from careers.models import SavedPath, SavedCareer, GoalPosition
from social.models import Comment

class FeedBase():
	
	def get_univ_feed(self,user,**opts):
		"""
		Gathers universal feed items and returns list of dict items

		Keyword args:
		user_id -- user id

		Default args (opts):
		timeline - 24 hours
		"""
		# sefrom t defaults

		timeline = opts['timeline'] if 'timeline' in opts else 48
		stop = datetime.now() - timedelta(hours = timeline)

		# get user connections and educations
		connections = [u.id for u in user.profile.connections.all()]
		educations = [u.id for u in User.objects.filter(positions__entity_id__in=user.profile.educations(),positions__type="education")]
	
		# retrieve data
		paths = SavedPath.objects.filter(Q(owner__in=connections) | Q(owner__in=educations)).filter(date_modified__gte=stop)
		print paths
		careers = SavedCareer.objects.filter(Q(owner__in=connections) | Q(owner__in=educations)).filter(updated__gte=stop)
		positions = GoalPosition.objects.filter(Q(owner__in=connections) | Q(owner__in=educations)).filter(updated__gte=stop)
		users = User.objects.filter(Q(id__in=connections) | Q(id__in=educations)).filter(date_joined__gte=stop)
		comments = Comment.objects.filter(Q(owner__in=connections) | Q(owner__in=educations)).filter(updated__gte=stop)

		# concatenate into one list
		unordered_feed = [{'type':'careerpath','id':p.id,'user_id':p.owner_id,'user_name':p.owner.profile.full_name(),'title':p.title,'body':None,'target_user_name':None,'target_user_id':None,'target_type':None,'target_name':None,'target_id':None,'date':p.date_modified,'stub':{'user_id':p.owner_id,'user_name':p.owner.profile.full_name(),'user_pic':p.owner.profile.default_profile_pic(),'connected':p.owner_id in connections,'saved_paths':len(p.owner.savedPath.all()),'saved_positions':len(p.owner.goal_position.all()),'path':p.path_simple(),'career':None,'position':None,'comment':None}} for p in paths]
		unordered_feed.extend([{'type':'savedcareer','id':c.id,'user_id':c.owner_id,'user_name':c.owner.profile.full_name(),'title':c.title,'body':None,'target_user_name':None,'target_user_id':None,'target_type':None,'target_name':None,'target_id':None,'date':c.updated,'stub':{'user_id':c.owner_id,'user_name':c.owner.profile.full_name(),'user_pic':c.owner.profile.default_profile_pic(),'connected':c.owner_id in connections,'saved_paths':len(c.owner.savedPath.all()),'saved_positions':len(c.owner.goal_position.all()),'path':None,'career':{'title':c.title,'id':c.career.id},'position':None,'comment':None}} for c in careers])
		unordered_feed.extend([{'type':'goalposition','id':p.id,'user_id':p.owner_id,'user_name':p.owner.profile.full_name(),'title':p.position.title,'body':None,'target_user_name':None,'target_user_id':None,'target_type':None,'target_name':None,'target_id':None,'date':p.updated,'stub':{'user_id':p.owner_id,'user_name':p.owner.profile.full_name(),'user_pic':p.owner.profile.default_profile_pic(),'connected':p.owner_id in connections,'saved_paths':len(p.owner.savedPath.all()),'saved_positions':len(p.owner.goal_position.all()),'path':None,'career':None,'position':p.owner.profile.bio_simple(),'comment':None}} for p in positions])
		unordered_feed.extend([{'type':'newuser','id':u.id,'user_id':u.id,'user_name':u.profile.full_name(),'title':None,'body':None,'target_user_name':None,'target_user_id':None,'target_type':None,'target_name':None,'target_id':None,'date':u.date_joined,'stub':{'user_id':u.id,'user_name':u.profile.full_name(),'user_pic':u.profile.default_profile_pic(),'connected':u.id in connections,'saved_paths':len(u.savedPath.all()),'saved_positions':len(u.goal_position.all()),'path':None,'career':None,'position':None,'comment':None}} for u in users])
		unordered_feed.extend([{'type':'comment','id':c.id,'user_id':c.owner.id,'user_name':c.owner.profile.full_name(),'title':None,'body':c.body,'target_user_id':c.target_user().id,'target_user_name':c.target_user().profile.full_name(),'target_type':c.type,'target_name':c.target_name(),'target_id':c.target_id(),'date':c.updated,'stub':{'user_id':c.target_user().id,'user_name':c.target_user().profile.full_name(),'user_pic':c.target_user().profile.default_profile_pic(),'connected':c.target_user().id in connections,'saved_paths':len(c.target_user().savedPath.all()),'saved_positions':len(c.target_user().goal_position.all()),'path':None,'career':None,'position':None,'comment':{'body':c.body,'commenter_id':c.owner_id,'commenter_name':c.owner.profile.full_name(),'commenter_pic':c.owner.profile.default_profile_pic()}}} for c in comments])

		ordered_feed = sorted(unordered_feed, key=operator.itemgetter('date'),reverse=True)

		return ordered_feed


