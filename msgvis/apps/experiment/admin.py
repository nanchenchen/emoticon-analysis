from django.contrib import admin

# Register your models here.
from msgvis.apps.experiment import models
admin.site.register(models.Experiment)
admin.site.register(models.Stage)
admin.site.register(models.Condition)
admin.site.register(models.Assignment)
