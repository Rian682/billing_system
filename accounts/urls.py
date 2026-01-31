from django.urls import path, include
from .views import CurrentUserView

urlpatterns = [
    path('me/', CurrentUserView.as_view(), name='current-user'),
]
