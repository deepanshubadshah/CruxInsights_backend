from django.urls import path
from .views import CruxDataView, MultiUrlCruxDataView

urlpatterns = [
    path('crux-data/', CruxDataView.as_view(), name='crux-data'),
    path('multi-url-crux-data/', MultiUrlCruxDataView.as_view(), name='multi-url-crux-data'),
]