from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Liked, Rejected

CustomUser = get_user_model()

admin.site.register(CustomUser)
admin.site.register(Rejected)
admin.site.register(Liked)
