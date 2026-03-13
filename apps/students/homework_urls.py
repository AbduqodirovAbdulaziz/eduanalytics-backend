from django.urls import path
from .views import BulkHomeworkView

urlpatterns = [
    path('bulk/', BulkHomeworkView.as_view(), name='homework-bulk'),
]
