# Python
import logging

# Django
from celery import task

# Prosperime


logger = logging.getLogger(__name__)

@task()
def send_advisor_request(req):

	return None
