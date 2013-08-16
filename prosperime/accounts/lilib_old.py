	###############
	### V1 CODE ###
	###############
	def add_dormant_user(self,user_info):

		# compile temporary user name
		temp_username = user_info['firstName'] + user_info['lastName'] + user_info['id']
		temp_username = temp_username[:30]
		
		# check to see if user already exists
		try:
			user = User.objects.get(username=temp_username)
		except ObjectDoesNotExist:
			# create dormant user account
			user = User()
			user.username = temp_username
			user.is_active = False
			user.save()

		# create user profile
		user.profile.first_name = user_info['firstName']
		user.profile.last_name = user_info['lastName']
		if 'headline' in user_info:
			user.profile.headline = user_info['headline']		
		user.profile.status = "dormant"
		user.profile.save()

		# add pofile picture
		if 'pictureUrl' in user_info:
			self.add_profile_pic(user,user_info['pictureUrl'])

		# create LinkedIn account
		
		acct = Account()
		acct.owner = user
		acct.service = 'linkedin'
		acct.uniq_id = user_info['id']
		if 'publicProfileUrl' in user_info:
			acct.public_url = user_info['publicProfileUrl']
		acct.status = "unlinked"
		acct.save()

		if self.logging:
			print 'Add Dormant User: ' + user_info['firstName'] + ' ' + user_info['lastName']

		return user

	def process_public_page(self,user,url):
		# fetch html and soup it
		
		# html = self.get_public_page(url)
		try:
			html = urllib2.urlopen(url)
		except:
			return None
		soup = BeautifulSoup(html)

		# get all profile container divs
		divs = soup.find_all("div","section",id=re.compile("^profile"))

		# loop throuh each div
		for d in divs:
			# identify type
			if d['id'] == 'profile-experience':
				# extract position data
				positions = self.extract_pos_from_public_page(d)
				for p in positions:
					# check to see if a co uniq was returned
					if p['co_uniq_name'] is not None:
						# check to see if new company
						# co = self.get_company(name=p['co_uniq_name'])
						co = self.get_company_safe(name=p['co_uniq_name'])

						if co is None:
							# add new company
							co = self.add_company(name=p['co_uniq_name'])
							if co is None: # try to add legit company, if fails, add stub
								co = self.add_unverified_company(p)
							if co is not None:
								self.add_position(user,co,p)
						else:
							pos = self.get_position(user,co,p)
							if pos is None:
								self.add_position(user,co,p)
							
			# handle Education
			elif d['id'] == 'profile-education':
				ed_positions = self.extract_ed_pos_from_public_page(d)
				for p in ed_positions:
					# check to see if new company
					# inst = self.get_institution(name=p['inst_name'])
					inst = self.get_institution_safe(name=p['inst_name'])

					if inst is None:
						# add new company
						inst = self.add_institution(p)
						# if it's a new company, position must be new as well
						# if inst is not None:
						self.add_ed_position(user,inst,p)
					else:
						# TODO update company
						pos = self.get_position(user,inst,p,type="ed")
						if pos is None:
							self.add_ed_position(user,inst,p) 

# class LITest(LIBase):

# 	def process_public_page(self,url):
# 		# fetch html and soup it
		
# 		# html = self.get_public_page(url)
# 		html = urllib2.urlopen(url)
# 		soup = BeautifulSoup(html)

# 		# get all profile container divs
# 		divs = soup.find_all("div","section",id=re.compile("^profile"))

# 		# loop throuh each div
# 		for d in divs:
# 			# identify type
# 			if d['id'] == 'profile-experience':
# 				# extract position data
# 				positions = self.extract_pos_from_public_page(d)
# 				for p in positions:
# 					print p
							
# 			elif d['id'] == 'profile-education':
# 				ed_positions = self.extract_ed_pos_from_public_page(d)
# 				# for p in ed_positions:
# 					# print p

# 	def extract_pos_from_public_page(self,data):
# 		# initialize positions array
# 		positions = []
# 		# get all position divs
# 		raw_positions = data.find_all("div","position")
# 		# loop through each position
# 		for p in raw_positions:
# 			# get title of position
# 			title = p.find("div","postitle").span.contents[0]
# 			# get uniq ue name of company
# 			co_uniq_name = p.find("a","company-profile-public")
# 			if co_uniq_name:
# 				co_uniq_name = co_uniq_name.get('href')
# 				m = re.search("(?<=\/company\/)([\w-]*)",co_uniq_name)
# 				co_uniq_name = m.group(0).strip()
# 				# print co_uniq_name
# 				# get start and end dates
# 				start_date = p.find("abbr","dtstart")
# 				if start_date is not None:
# 					start_date = start_date.get('title')
# 				try:
# 					end_date = p.find('abbr','dtstamp').get('title')
# 					current = True
# 				except:
# 					current = False

# 				try:
# 					end_date = p.find("abbr","dtend").get("title")
# 				except:
# 					end_date = None
# 				# get descriptions
# 				try:
# 					descr = p.find("p","description").contents[0]
# 				except:
# 					descr = None
# 				# append to main positions array
# 				positions.append({'title':title,'co_uniq_name':co_uniq_name,'startDate':start_date,'endDate':end_date,'summary':descr,'isCurrent':current})
# 		return positions

# 	def extract_ed_pos_from_public_page(self,data):
# 		# initialize positions array
# 		positions = []
# 		# get all position divs
# 		raw_positions = data.find_all("div","position")
# 		# loop through each position
# 		for p in raw_positions:
# 			inst_uniq_id = p.get('id')
# 			inst_name = p.h3.contents[0].strip()
# 			try:
# 				degree = p.find("span","degree").contents[0]
				
# 			except:
# 				degree = None
# 			try:
# 				major = p.find("span","major").contents[0]
# 			except:
# 				major = None
# 			positions.append({'inst_uniq_id':inst_uniq_id,'inst_name':inst_name,'degree':degree,'fieldofStudy':major})
# 		return positions

