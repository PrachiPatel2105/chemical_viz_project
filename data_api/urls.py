from django.urls import path
from .views import HistoryListView, CSVUploadView, SummaryView, PDFReportView

urlpatterns = [
    # GET: List latest 5 uploaded datasets (History)
    path('history/', HistoryListView.as_view(), name='data-history'),
    
    # POST: Handle file upload and data processing
    path('upload/', CSVUploadView.as_view(), name='data-upload'),
    
    # GET: Retrieve summary data for a specific dataset
    path('summary/<int:pk>/', SummaryView.as_view(), name='data-summary'),

    # GET: Generate a PDF report for a specific dataset (Placeholder for Phase 3)
    path('report/<int:pk>/', PDFReportView.as_view(), name='data-report'),
]