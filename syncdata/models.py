from django.db import models

# Create your models here.
class SyncedRecord(models.Model):
    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100, default="")
    valid_to = models.DateField()

    ad_display_name = models.CharField(max_length=255, null=True, blank=True)
    ad_samaccountname = models.CharField(max_length=255, null=True, blank=True)
    ad_enabled = models.BooleanField(null=True, blank=True)
    distinguished_name = models.CharField(max_length=1024, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
