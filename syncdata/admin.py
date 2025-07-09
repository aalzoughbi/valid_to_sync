
from django.contrib import admin, messages
from .models import SyncedRecord
from utils.ad_actions import deactivate_user, activate_user


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
    list_display = ('first_name', 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled', 'distinguished_name')
    list_display_links = ('first_name', 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled', 'distinguished_name')
    search_fields = ('first_name', 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled', 'distinguished_name')
    list_filter = (FirstNameFilter, 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled',  'distinguished_name')
    readonly_fields = ('first_name', 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled', 'distinguished_name')
    ordering = ('-valid_to',)

    actions = ['deactivate_ad_accounts', 'activate_ad_accounts']

    def deactivate_ad_accounts(self, request, queryset):
        for record in queryset:
            if record.distinguished_name:
                try:
                    deactivate_user(record.distinguished_name)
                    record.ad_enabled = False  # Update locally
                    record.save()
                    self.message_user(request, f"✅ Deactivated: {record.ad_samaccountname}", level=messages.SUCCESS)
                except Exception as e:
                    self.message_user(request, f"❌ Error deactivating {record.ad_samaccountname}: {e}",
                                      level=messages.ERROR)

    def activate_ad_accounts(self, request, queryset):
        for record in queryset:
            if record.distinguished_name:
                try:
                    activate_user(record.distinguished_name)
                    record.ad_enabled = True  # Update locally
                    record.save()
                    self.message_user(request, f"✅ Activated: {record.ad_samaccountname}", level=messages.SUCCESS)
                except Exception as e:
                    self.message_user(request, f"❌ Error activating {record.ad_samaccountname}: {e}",
                                      level=messages.ERROR)

    deactivate_ad_accounts.short_description = "Deactivate selected AD accounts"
    activate_ad_accounts.short_description = "Activate selected AD accounts"
