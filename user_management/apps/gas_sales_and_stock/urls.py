from django.urls import path
from .views import MakeSaleView, AddStockView, ViewSalesView, SalesSummaryView, ViewStockView

urlpatterns = [
    path('make-sale/', MakeSaleView.as_view(), name='make-sale'),
    path('add-stock/', AddStockView.as_view(), name='add-stock'),
    path('view-sales/', ViewSalesView.as_view(), name='view-sales'),
    path('sales-summary/', SalesSummaryView.as_view(), name='sales-summary'),
    path('view-stock/', ViewStockView.as_view(), name='view-stock'),
]
