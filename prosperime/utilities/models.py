from django.db import models
from storages.backends.s3boto import S3BotoStorage
import datetime

class Report(models.Model):

	# returns path for uploading reports
    def _get_report_path(self,filename):
        path = "reports/" + self.category + "/" + filename + str(datetime.date.today())
        return path

	title = models.CharField(max_length=150)
	category = models.CharField(max_length=150)
	description = models.TextField(null=True,blank=True)
	report = models.FileField(storage=S3BotoStorage(bucket="prosperme_reports"),upload_to=_get_report_path)