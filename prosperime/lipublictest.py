# Python
from bs4 import BeautifulSoup
import urllib2
import re

# Django

# public url
url = "http://www.linkedin.com/in/scottleese"

# fetch html and soup it
html = urllib2.urlopen(url)
soup = BeautifulSoup(html)

# get all profile container divs
divs = soup.find_all("div","section",id=re.compile("^profile"))

# loop throuh each div
for d in divs:
	# identify type
	if d['id'] == 'profile-experience':
		# get all position divs
		positions = d.find_all("div","position")
		for p in positions:
			# skip current position (should already get from LI API)
			# if "summary-current" in p['class']:
			# 	pass
			# else:
			# 	pass
			title = p.find("div","postitle").span.contents[0]
			print title
			co_uniq_name = p.find("a","company-profile-public").get('href')
			# print co_uniq_name
			# m = re.search("^\/company\/(.*)",co_uniq_name)
			m = re.search("(?<=\/company\/)([\w-]*)",co_uniq_name)
			print m.group(0)
			co_uniq_name = m.group(0)
			start_date = p.find("abbr","dtstart").get("title")
			print start_date
			try:
				end_date = p.find("abbr","dtend").get("title")
				print end_date
			except:
				print "no end date"
			descr = p.find("p","description").contents[0]
			print descr
	elif d['id'] == 'profile-education':
		positions = d.find_all("div",'position')
		for p in positions:
			inst_uniq_id = p.get('id')
			print inst_uniq_id
			inst_name = p.h3.contents[0]
			print inst_name
			try:
				degree = p.find("span","degree").contents[0]
				print degree
			except:
				pass
			try:
				major = p.find("span","major").contents[0]
				print major
			except:
				pass
	else:
		# do nothing
		pass

# print divs
