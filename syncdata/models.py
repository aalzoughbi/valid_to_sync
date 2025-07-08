from django.db import models

# Create your models here.
class SyncedRecord(models.Model):
    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100, default="")
    valid_to = models.DateField()

    def __str__(self):
        return f"{self.valid_to} - {self.first_name} {self.last_name}"
