

# Frequency of careers in production 5/6/13
freq_map = [(u'Lawyers', 69), (u'General and operations managers', 53), (u'Postsecondary teachers', 17), (u'Personal and executive coaches and consultants', 15), (u'Marketing and sales managers', 13), (u'Market research analysts and marketing specialists', 10), (u'Technical writers', 9), (u'Social science research assistants', 8), (u'Accountants and auditors', 6), (u'Education administrators', 6), (u'Financial managers', 5), (u'Communications manager', 5), (u'Business development directors and managers', 5), (u'Web development managers', 4), (u'Business development analysts and specialists', 4), (u'Web developers', 4), (u'Communications representatives and specialists', 4), (u'Financial analysts', 4), (u'Nuclear engineers', 3), (u'Chemical engineers', 3), (u'First-line supervisors of food preparation and serving workers', 3), (u'Computer hardware engineers', 3), (u'Petroleum engineers', 3), (u'Chefs and head cooks', 3), (u'Civil engineers', 3), (u'Agricultural engineers', 3), (u'Electrical and electronics engineers', 3), (u'Environmental engineers', 3), (u'Mining and geological engineers, including mining safety engineers', 3), (u'Industrial engineers, including health and safety', 3), (u'Engineers, all other', 3), (u'Marine engineers and naval architects', 3), (u'Materials engineers', 3), (u'Aerospace engineers', 3), (u'Biomedical engineers', 3), (u'Media and communication equipment workers, all other', 2), (u'Financial specialists, all other', 2), (u'Local government managers, directors and others', 2), (u'Personal financial advisors', 2), (u'Miscellaneous media and communication workers', 2), (u'Bloggers and other independent writers', 2), (u'Program and project managers', 2), (u'Bookkeeping, accounting, and auditing clerks', 1), (u'Religious workers, all other', 1), (u'Sales managers and directors', 1), (u'Social and community service managers', 1), (u'Data scientists and analysts', 1), (u'Designers', 1), (u'Product management and development directors', 1), (u'Consulting analysts and specialists', 1), (u'Athletes, coaches, umpires, and related workers', 1), (u'Mobile software developer', 1), (u'Consulting managers and directors', 1), (u'Translator', 1), (u'Software developers, applications and systems software', 1), (u'Design and creativity managers and directors', 1), (u'Recruiting and placement specialists and representatives', 1), (u'Product management and development analysts and specialists', 1), (u'Sales representatives, services, all other', 1), (u'Secretaries and administrative assistants', 1), (u'Computer and information systems managers', 1), (u'Animators, cartoonists, and other digital artists', 1), (u'Office manager', 1), (u'Teacher assistants', 1)]


## All careers currently in use in production, mix of short and long names

mapper = {}

# Product
mapper["Product and Project Managers"] = [
"Program and project managers",
"Product management and development analysts and specialists",
"Product management and development directors",
]

# Office Staff
mapper["Office Administrators and Secretaries"] = [
"Office manager",
"Secretaries and administrative assistants",
]


# Engineers
mapper["Engineers"] = [
"Aerospace engineers",
"Biomedical engineers",
"Materials engineers",
"Marine engineers and naval architects",
"Engineers, all other",
"Industrial engineers, including health and safety",
"Mining and geological engineers, including mining safety engineers",
"Computer hardware engineers",
"Environmental engineers",
"Chemical engineers",
"Petroleum engineers",
"Nuclear engineers",
"Civil engineers",
"Electrical and electronics engineers",
"Agricultural engineers",
]



# Devs
mapper["Web and Mobile Developers"] = [
"Web developers",
"Web development managers",
"Mobile software developer"
]

mapper["Software and Systems Engineers"] = [
"Software developers, applications and systems software",
"Computer and information systems managers",
]

# Business Development
mapper["Business Development Professionals"] = [
"Business development analysts and specialists",
"Business development directors and managers",
]

# Education
mapper["Educators and Education Administrators"] = [
"Postsecondary teachers",
"Education administrators",
"Teacher assistants",
]


# Sales & Marketing
mapper["Sales and Marketing Professionals"] = [
"Sales representatives, services, all other",
"Sales managers and directors",
"Marketing and sales managers",
"Market research analysts and marketing specialists",
"Sales representatives, wholesale and manufacturing",
"Sales and related workers, all other",
]

# Singletons
mapper["Lawyers"] = ["Lawyers"]
mapper["Sports Professionals"] = ["Athletes, coaches, umpires, and related workers"]
mapper["Religous Workers"] = ["Religious workers, all other"]
mapper["Government Officials"] = ["Local government managers, directors and others"]
mapper["Translator"] = ["Translator"]
mapper["Recruiting Professionals"] = ["Recruiting and placement specialists and representatives"]
mapper["Data Scientists"] = ["Data scientists and analysts"]
mapper["General Managers"] = ["General and operations managers"]
mapper["Investment Professionals"] = ["Venture capitalists and other private investors | Venture capitalists and other private investors"]

# Designers & Artists
mapper["Designers"] = [
"Design and creativity managers and directors",
"Designers",
"Animators, cartoonists, and other digital artists",
]

# Finance
mapper["Financial Specialists"] = [
"Financial analysts",
"Personal financial advisors",
"Financial specialists, all other",
"Financial managers",
]

# Accountants
mapper["Accountants"] = [
"Bookkeeping, accounting, and auditing clerks",
"Accountants and auditors",
]

# Comm
mapper["Media and Communications Professionals"] = [
"Media and communication equipment workers, all other",
"Communications manager",
"Communications representatives and specialists",
"Social and community service managers",
"Miscellaneous media and communication workers",
]

# Writers
mapper["Writers"] = ["Bloggers and other independent writers",
 "Technical writers",
 "Editors",
 ]


# Food Services Professionals
mapper["Food Services Professionals"] = [
"Chefs and head cooks",
"First-line supervisors of food preparation and serving workers",
]

# Researchers
mapper["Researchers"] = ["Social science research assistants"]

# Consultant (way too broad...)
mapper["Consultant"] = [
"Consulting analysts and specialists",
"Personal and executive coaches and consultants",
"Consulting managers and directors",
]


#####################################
#####################################


from careers.models import Career, Position

## Creates parents from mapper bucket declared above
##	(after first use, just run to sync mapper to DB if mapper changed)
def create_parents():
	for k in mapper.keys():
		try:
			parent = Career.objects.get(long_name=k)
		except:
			parent = Career()
			parent.long_name = k
			parent.short_name = k
			parent.description = "parent"
			parent.save()
			print "Parent Career created: " + parent.long_name


# Finds all careers that are actually mapped to positions
def careers_in_use():
	all_pos = Position.objects.all()
	used_careers = []
	seen_before = set()
	for p in all_pos:
		for c in p.careers.all():
			if c.id not in seen_before:
				used_careers.append(c)
				seen_before.add(c.id)

	print "There are " + str(len(used_careers)) + " careers in use."
	return used_careers


# Iterates through used careers and maps them to parent mapper
def map_careers_to_parents():

	careers = careers_in_use()
	for c in careers:
		for k in mapper.keys():
			if not c.parent:
				if c.long_name in mapper[k] or c.short_name in mapper[k]:
					c.parent = Career.objects.get(long_name=k, description="parent")
					print "Mapped: " + c.long_name + " --> " + k
					c.save()


# Finds careers in use that don't currently have parents
def find_orphans():
	
	careers = careers_in_use()
	orphans = []
	for c in careers:
		if not c.parent:
			orphans.append(c)
			if c.short_name:
				print c.short_name + ' | ' + c.long_name
			else:
				print c.long_name






















