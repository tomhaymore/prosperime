# from Python
import json

# from Django
from entities.models import Career, Position, User

class CareerSimBase():

	# fetch all users
	# users = User.objects.prefetch_related('positions').exclude(profile__status="deleted")
	users = {}

	# initializes organizational map
	users_orgs_map = {}

	# initialize educational map
	users_eds_map = {}

	def __init__(self):
		self.load_users()
		self.load_maps()

	def load_users(self):
		users = User.objects.values('id','positions__type','positions__entity__id')
		users_dict = {}
		for u in users:
			if u['id'] in users_dict:
				users_dict[u['id']]['positions'].append({'type':u['positions__type'],'id':u['positions__entity__id']})
			else:
				users_dict[u['id']] = {'positions':[{'type':u['positions__type'],'id':u['positions__entity__id']}]}
		self.users = users_dict
		# print self.users

	def load_maps(self):
		"""
		loads set of orgs / eds for each user
		"""
		for k,v in self.users.items():
			orgs = []
			eds = []
			for p in v['positions']:
				if p['type'] == "education":
					eds.append(p['id'])
				else:
					orgs.append(p['id'])
			if orgs:
				self.users_orgs_map[k] = set(orgs)
			if eds:
				self.users_eds_map[k] = set(eds)

	def get_focal_orgs(self,id):
		"""
		gets set of orgs / eds for focal user
		"""
		# fetch focal user
		user = User.objects.get(pk=id)
		# initialize holding arrays
		orgs = []
		eds =[]
		# loop through all positions to get unique entity ids
		for p in user.positions.all():
			if p.type == "education":
				eds.append(p.entity.id)
			else:
				orgs.append(p.entity.id)
		orgs_set = set(orgs)
		eds_set = set(eds)
		focal_orgs = {
			'orgs': orgs_set,
			'eds': eds_set
		}
		return focal_orgs

	def find_similar_careers(self,id):
		"""
		measures intersection of sets between focal user and other users to find most similar
		"""
		focal_orgs = self.get_focal_orgs(id) 
		orgs_sim = []
		eds_sim = []
		
		for k,v in self.users_orgs_map.items():
			intersect = focal_orgs['orgs'].intersection(v)
			jaccard = len(intersect)/len(v)
			orgs_sim.append((k,jaccard,))

		for k,v in self.users_eds_map.items():
			intersect = focal_orgs['eds'].intersection(v)
			jaccard = len(intersect)/len(v)
			eds_sim.append((k,jaccard,))	

		sorted_orgs_sim = sorted(orgs_sim, key=lambda x:x[1],reverse=True)
		sorted_eds_sim = sorted(eds_sim, key=lambda x:x[1],reverse=True)	

		sorted_orgs_sim = [u[0] for u in sorted_orgs_sim]

		return sorted_orgs_sim[:10]

class CareerMapBase():

	# set max size of ngram
	NGRAM_MAX = 10

	# set min size of ngram
	NGRAM_MIN = 1

	# initialize global dictionary for career-to-position mapping
	careers_to_positions_map = {}

	# initilize array for stop words
	STOP_LIST = []

	def __init__(self):
		# fill in career to positions map
		self.init_career_to_positions_map()
		self.load_stop_list()

	def load_stop_list(self):
		try:
			reader = (open('career_map_stop_list.csv','rU'))
		except:
			return None
		for row in reader:
			self.STOP_LIST.append(row[0])

	def tokenize_position(self,title):
		"""
		tokenizes position title based on spaces
		"""
		if title:
			# tokenize position title
			tokens = title.split(" ")
			# reduce all strings to lower case
			tokens = [t.lower() for t in tokens]
			return tokens
		return None

	def extract_ngrams(self,tokens):
		"""
		breaks position titles into appropriate number of ngrams and returns as a list
		"""
		if tokens:
			ngrams = []
			n_tokens = len(tokens)
			for i in range(n_tokens):
				for j in range(i+1,min(n_tokens,self.NGRAM_MAX)+1):
					ngram = " ".join(tokens[i:j])
					ngrams.append(ngram)
					# ngrams.append(tokens[i:j])

			return ngrams
		return None

	def init_career_to_positions_map(self):
		"""
		fill in career map dictionary from db
		"""
		careers = Career.objects.values('id','pos_titles').filter(status="active")

		career_map = {}

		for c in careers:
			if c['pos_titles']:
				titles = json.loads(c['pos_titles'])
				# add career-to-position title mapping, reduced to lower case
				titles = [t.lower() for t in titles]
				
				career_map[c['id']] = titles

		self.careers_to_positions_map = career_map

	def match_careers_to_position(self,pos):
		title_ngrams = self.extract_ngrams(self.tokenize_position(pos.title))
	
		careers = []

		for t in title_ngrams:
			# make sure position title is not in stop list, e.g., "Manager" or "Director" or something equally generic
			if t not in self.STOP_LIST:
				for k,v in self.careers_to_positions_map.items():
					if t in v and k not in careers:
						careers.append(k)

		for c_id in careers:
			c = Career.objects.get(pk=c_id)
			pos.careers.add(c)
		pos.save()

	def test_position(self,title):

		title_ngrams = self.extract_ngrams(self.tokenize_position(title))
		
		print title_ngrams

		for t in title_ngrams:
			# make sure position title is not in stop list, e.g., "Manager" or "Director" or something equally generic
			if t not in self.STOP_LIST:
				for k,v in self.careers_to_positions_map.items():
					# print v
					if t in v:
						career = Career.objects.get(pk=k)
						print title + " matches " + career.name

	def test_match_careers_to_position(self,title=None):

		positions = Position.objects.all()

		for p in positions:
			careers = []

			if p.title:
				title_ngrams = self.extract_ngrams(self.tokenize_position(p.title))

				# print title_ngrams

				for t in title_ngrams:
					# make sure position title is not in stop list, e.g., "Manager" or "Director" or something equally generic
					if t not in self.STOP_LIST:
						for k,v in self.careers_to_positions_map.items():
							if t in v and k not in careers:
								career = Career.objects.get(pk=k)
								print t + ": " + career.name

class CareerImportBase():

	def import_careers(self,file_path):

		f = open(file_path,'rU')
		c = csv.DictReader(f)
		for row in c:
			career = Career()
			career.short_name = row['name']
			career.long_name = row['name']
			career.save()
			if row['titles'] is not None and row['titles'] is not "":
				new_titles = row['titles'].split(',')
				for t in new_titles:
					career.add_pos_title(t)
			career.save()


