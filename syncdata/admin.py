from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.admin import AdminSite

from .models import SyncedRecord, AdminPreference
from .forms import AdminColumnPreferenceForm
from utils.ad_actions import deactivate_user, activate_user


class FirstNameFilter(admin.SimpleListFilter):
    title = "First Name"
    parameter_name = "first_name"
    template = "admin/filters/filter_first_name_input.html"

    def lookups(self, request, model_admin):
        return [("all", "All")]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(first_name__icontains=value)
        return queryset

    def expected_parameters(self):
        return [self.parameter_name]

    def choices(self, changelist):
        yield {
            'parameter_name': self.parameter_name,
            'value': self.value(),
            'title': self.title,
            'query_string': changelist.get_query_string(remove=[self.parameter_name]),
        }

@admin.register(SyncedRecord)
class SyncedRecordAdmin(admin.ModelAdmin):
    all_columns = ['first_name', 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled', 'distinguished_name']

    list_display = ('first_name', 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled', 'distinguished_name')
    list_display_links = ('first_name', 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled', 'distinguished_name')
    search_fields = ('first_name', 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled', 'distinguished_name')
    list_filter = (FirstNameFilter, 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled', 'distinguished_name')
    readonly_fields = ('first_name', 'last_name', 'valid_to', 'ad_display_name', 'ad_samaccountname', 'ad_enabled', 'distinguished_name')
    ordering = ('-valid_to',)

    actions = ['deactivate_ad_accounts', 'activate_ad_accounts']

    def deactivate_ad_accounts(self, request, queryset):
        for record in queryset:
            if record.distinguished_name:
                try:
                    new_dn = deactivate_user(record.distinguished_name)
                    record.ad_enabled = False
                    record.distinguished_name = new_dn  # Update to new DN
                    record.save()
                    self.message_user(request, f"✅ Deactivated: {record.ad_samaccountname}", level=messages.SUCCESS)
                except Exception as e:
                    self.message_user(request, f"❌ Error deactivating {record.ad_samaccountname}: {e}", level=messages.ERROR)

    def activate_ad_accounts(self, request, queryset):
        for record in queryset:
            if record.distinguished_name:
                try:
                    new_dn = activate_user(record.distinguished_name)
                    record.ad_enabled = True
                    record.distinguished_name = new_dn  # Update to new DN
                    record.save()
                    self.message_user(request, f"✅ Activated: {record.ad_samaccountname}", level=messages.SUCCESS)
                except Exception as e:
                    self.message_user(request, f"❌ Error activating {record.ad_samaccountname}: {e}", level=messages.ERROR)

    deactivate_ad_accounts.short_description = "Deactivate selected AD accounts"
    activate_ad_accounts.short_description = "Activate selected AD accounts"

    def get_list_display(self, request):
        try:
            pref = AdminPreference.objects.get(user=request.user, model_name='syncedrecord')
            return pref.columns or self.all_columns
        except AdminPreference.DoesNotExist:
            return self.all_columns

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('column-preferences/', self.admin_site.admin_view(self.set_column_preferences))
        ]
        return custom_urls + urls

    def set_column_preferences(self, request):
        model_name = 'syncedrecord'
        try:
            pref = AdminPreference.objects.get(user=request.user, model_name=model_name)
            initial = {'columns': pref.columns}
        except AdminPreference.DoesNotExist:
            initial = {'columns': self.all_columns}

        form = AdminColumnPreferenceForm(request.POST or None, initial=initial)
        form.fields['columns'].choices = [(col, col) for col in self.all_columns]

        if request.method == 'POST' and form.is_valid():
            columns = form.cleaned_data['columns']
            obj, _ = AdminPreference.objects.get_or_create(user=request.user, model_name=model_name)
            obj.columns = columns
            obj.save()
            return redirect(f'../')

        context = dict(
            self.admin_site.each_context(request),
            title='Set column preferences',
            form=form,
        )
        return render(request, 'admin/column_preferences.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['column_pref_link'] = 'column-preferences/'
        return super().changelist_view(request, extra_context=extra_context)