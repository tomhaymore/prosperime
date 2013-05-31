from celery import task

# from prosperme
import careers.careerlib as careerlib
from careers.models import Position

@task()
def match_unmatched_positions():
	"""
	fetches and matches all unmatched positions
	"""
	mapper = careerlib.CareerMapBase()
	noideals = Position.objects.filter(ideal_position=None).exclude(title="")

	# set init counts
	all_count = 0
	match_count = 0

	for n in noideals:
		all_count += 1
		res = mapper.match_position_to_ideals(n)
		if res:
			match_count +=1

	print "Matched %i out of %i positions (%d)" % (all_count,match_count,float(match_count)/all_counts)
