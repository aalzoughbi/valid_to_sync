from django.contrib import admin
from .models import SyncedRecord

# Register your models here.
@admin.register(SyncedRecord)
class SyncedRecordAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'valid_to')
    list_display_links = ('first_name', 'last_name', 'valid_to')
    search_fields = ('first_name', 'last_name', 'valid_to')
    list_filter = ('first_name', 'last_name', 'valid_to')
    readonly_fields = ('first_name', 'last_name', 'valid_to')
    ordering = ('-valid_to',)