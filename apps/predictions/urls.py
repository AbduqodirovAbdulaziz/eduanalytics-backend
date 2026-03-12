from django.urls import path
from .views import PredictView, BatchPredictView, PredictionHistoryView

urlpatterns = [
    path('',                        PredictView.as_view(),          name='predict'),
    path('batch/',                   BatchPredictView.as_view(),     name='predict-batch'),
    path('history/<int:student_id>/', PredictionHistoryView.as_view(), name='predict-history'),
]
