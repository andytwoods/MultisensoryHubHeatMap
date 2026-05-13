from django.urls import path, include

urlpatterns = [
    path("concept-analytics/", include("concept_analytics.urls")),
]
