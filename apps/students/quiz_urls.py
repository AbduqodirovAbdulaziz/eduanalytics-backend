from django.urls import path
from .views import BulkQuizView

urlpatterns = [
    path('bulk/', BulkQuizView.as_view(), name='quiz-bulk'),
]
