from django.contrib import admin
from .models import Test, Lecture, Question, Material, Doubt

admin.site.register(Test)
admin.site.register(Lecture)
admin.site.register(Question)
admin.site.register(Material)
admin.site.register(Doubt)
