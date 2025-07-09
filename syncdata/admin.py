
from django.contrib import admin
from .models import SyncedRecord

class FirstNameFilter(admin.SimpleListFilter):
    title = "First Name"
    parameter_name = "first_name"
    template = "admin/filters/filter_first_name_input.html"

    def lookups(self, request, model_admin):
        return [("all", "All")]  # Not used

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(first_name__icontains=value)
        return queryset

    def expected_parameters(self):
        return [self.parameter_name]

    def choices(self, changelist):
        # Provide required context for custom template
        yield {
            'parameter_name': self.parameter_name,
            'value': self.value(),
            'title': self.title,
            'query_string': changelist.get_query_string(remove=[self.parameter_name]),
        }



@admin.register(SyncedRecord)
class SyncedRecordAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled')
    list_display_links = ('first_name', 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled')
    search_fields = ('first_name', 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled')
    list_filter = (FirstNameFilter, 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled')
    readonly_fields = ('first_name', 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled')
    ordering = ('-valid_to',)
