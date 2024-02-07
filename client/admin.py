from django.contrib import admin
from .models import User, Client, ChitFund, UserProfile, Category


# Register your models here.
admin.site.register(User)
admin.site.register(Client)
admin.site.register(ChitFund)
admin.site.register(UserProfile)
admin.site.register(Category)