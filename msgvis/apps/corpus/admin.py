from django.contrib import admin

from msgvis.apps.corpus import models
admin.site.register(models.Dataset)
admin.site.register(models.Code)
admin.site.register(models.Message)