from django.contrib import admin

from users.models import User, BlogPost

admin.site.register(User)
admin.site.register(BlogPost)
