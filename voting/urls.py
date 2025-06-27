from django.urls import path
from . import views

app_name = 'voting'

urlpatterns = [
    path('', views.index, name='index'),
    path('vote/', views.vote, name='vote'),
    path('vote/<code>/', views.vote, name='vote_with_code'),
    path('success/', views.success, name='success'),
    path('results/', views.results, name='results'),

    # NEUER URL-PFAD
    path('send-codes/', views.send_codes_to_list, name='send_codes_to_list'),
    path('live-results/', views.live_results, name='live_results'),
    path('api/live-results-data/', views.live_results_data, name='live_results_data'),
]