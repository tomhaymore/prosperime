# from Django
from django.contrib import admin

# from Prosperime
from accounts.models import Account, Profile, Picture

class AccountAdmin(admin.ModelAdmin):
	pass

class ProfileAdmin(admin.ModelAdmin):
	pass

class PictureAdmin(admin.ModelAdmin):
	pass

admin.site.register(Account, AccountAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Picture, PictureAdmin)

