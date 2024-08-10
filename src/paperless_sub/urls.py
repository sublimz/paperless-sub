from django.urls import include, path
from paperless_sub.views import PublicIndexView

from django.urls import path
from django.urls import re_path

urlpatterns = [
    # ... autres URL de votre projet ...
    re_path('public/', PublicIndexView.as_view(), name='pindex'),
    re_path('', include('paperless.urls')),
]