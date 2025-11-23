from django.urls import path
from .views import HistoryListView, CSVUploadView, SummaryView, PDFReportView

urlpatterns = [
    # GET: List latest 5 uploaded datasets (History)
    path('history/', HistoryListView.as_view(), name='data-history'),
    
    # POST: Handle file upload and data processing
    path('upload/', CSVUploadView.as_view(), name='data-upload'),
    
    # GET: Retrieve summary data for a specific dataset (supports both URL param and query param)
    path('summary/<int:pk>/', SummaryView.as_view(), name='data-summary-pk'),
    path('summary/', SummaryView.as_view(), name='data-summary'),

    # GET: Generate a PDF report for a specific dataset (supports both URL param and query param)
    path('report/<int:pk>/', PDFReportView.as_view(), name='data-report-pk'),
    path('report/', PDFReportView.as_view(), name='data-report'),
    
    # DELETE: Delete a specific dataset
    path('history/<int:pk>/', HistoryListView.as_view(), name='data-history-delete'),
]