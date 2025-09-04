from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DatasetViewSet, MetricsView, ColumnDistributionView

router = DefaultRouter()
router.register(r'datasets', DatasetViewSet, basename='dataset')

urlpatterns = [
    path('', include(router.urls)),
    path('datasets/<int:pk>/metrics/', MetricsView.as_view(), name='dataset-metrics'),
    path('datasets/<int:pk>/column/<str:column>/distribution/', ColumnDistributionView.as_view(), name='column-dist'),
]
