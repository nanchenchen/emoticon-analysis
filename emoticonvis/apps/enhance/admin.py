from django.contrib import admin

# Register your models here.

from emoticonvis.apps.enhance import models
admin.site.register(models.Dictionary)
admin.site.register(models.Feature)
admin.site.register(models.MessageFeature)