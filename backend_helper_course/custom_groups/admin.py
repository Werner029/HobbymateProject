from django.contrib import admin

from .models import CustomGroup, GroupMember

admin.site.register(CustomGroup)
admin.site.register(GroupMember)
