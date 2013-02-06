# from Python
import json

# from Django
from entities.models import Career, Position

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



