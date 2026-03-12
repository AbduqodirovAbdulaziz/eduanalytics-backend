from django.urls import path
from .views import OverviewStatsView, CourseStatsView, AtRiskStudentsView, GroupStatsView

urlpatterns = [
    path('overview/',                 OverviewStatsView.as_view(),  name='stats-overview'),
    path('courses/<int:course_id>/', CourseStatsView.as_view(),    name='stats-course'),
    path('groups/<int:group_id>/',   GroupStatsView.as_view(),     name='stats-group'),
    path('at-risk/',                  AtRiskStudentsView.as_view(), name='stats-at-risk'),
]
