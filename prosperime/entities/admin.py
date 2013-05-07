# from Django
from django.contrib import admin

# from Prosperime
from entities.models import Entity, Industry, Image

class EntityAdmin(admin.ModelAdmin):
	search_fields = ['name']

class IndustryAdmin(admin.ModelAdmin):
	search_fields = ['name']

class ImageAdmin(admin.ModelAdmin):
	search_fields = ['entity__name']

admin.site.register(Entity,EntityAdmin)
admin.site.register(Industry,IndustryAdmin)
admin.site.register(Image,ImageAdmin)

