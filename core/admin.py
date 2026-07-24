from django.contrib import admin

from core.models import UserProfile, SharedFile, UserFolder, UserFile

admin.site.register(UserProfile)
admin.site.register(SharedFile)
admin.site.register(UserFolder)
@admin.register(UserFile)
class UserFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_name', 'user', 'folder', 'status', 'uploaded_at')
    list_filter = ('status', 'uploaded_at')
    search_fields = ('original_name', 'user__username', 'folder__folder_name')

    
    
