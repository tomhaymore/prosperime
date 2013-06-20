# from Django
from django.contrib import admin

# from Prosperime
from careers.models import Career, IdealPosition, SavedCareer, Position

class CareerAdmin(admin.ModelAdmin):
	search_fields = ['long_name','short_name']

class IdealPositionAdmin(admin.ModelAdmin):
	search_fields = ['title','long_title','description','major']

class SavedCareerAdmin(admin.ModelAdmin):
	pass

class PositionAdmin(admin.ModelAdmin):
	pass

admin.site.register(Career,CareerAdmin)
admin.site.register(IdealPosition,IdealPositionAdmin)
admin.site.register(SavedCareer,SavedCareerAdmin)
admin.site.register(Position,PositionAdmin)

