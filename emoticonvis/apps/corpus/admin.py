from django.contrib import admin

from emoticonvis.apps.corpus import models
admin.site.register(models.Dataset)
admin.site.register(models.Participant)
admin.site.register(models.Message)
admin.site.register(models.Emoticon)