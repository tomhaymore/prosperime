# from Django
from django.contrib import admin

# from Prosperime
from social.models import Comment, Conversation, Tag

class CommentAdmin(admin.ModelAdmin):
	pass

class ConversationAdmin(admin.ModelAdmin):
	pass

class TagAdmin(admin.ModelAdmin):
	pass

admin.site.register(Comment, CommentAdmin)
admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Tag, TagAdmin)
