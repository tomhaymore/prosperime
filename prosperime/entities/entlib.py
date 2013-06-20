# from python
import logging

# from django

# from prosperme
from entities.models import Entity, Image, Financing, Industry, Office
from careers.models import Career, Position, IdealPosition

logger = logging.getLogger(__name__)

class EntitiesCleaner():
	
	def consolidate_entity(self,master,name):

		master_entity = Entity.objects.get(id=master)

		target_entities = Entity.objects.filter(name=name).exclude(id=master)

		count = 0

		for e in target_entities:
			logger.info("Deleting " + e.name + " ...")
			# double check and skip master entity
			if e.id == master:
				continue
			# switch over positions
			positions = Position.objects.filter(entity=e)
			for p in positions:
				p.entity = master_entity
				p.save()

			# switch over offices
			offices = Office.objects.filter(entity=e)
			for o in offices:
				o.entity = master_entity
				o.save()

			# switch over industries
			industries = Industry.objects.filter(entity=e)
			for i in industries:
				i.entities.add(master_entity)
				i.save()

			# switch over financings
			financings = Financing.objects.filter(target=e)
			for f in financings:
				f.target = master_entity
				f.save()

			# switch over images
			images = Image.objects.filter(entity=e)
			for i in images:
				i.entity = master_entity
				i.save()

			# de;ete entity
			e.delete()

			count += 1

		logger.info("consolidated " + str(count) + " entities")
