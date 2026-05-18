from django.contrib import admin
from django.urls import path, include
from .views import index

urlpatterns = [
    path("", index),
    path("admin/", admin.site.urls),
    path("analytics/", include("concept_analytics.urls")),
]
