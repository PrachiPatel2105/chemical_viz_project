import os
import pandas as pd
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import UploadedDataset
from .serializers import UploadedDatasetSerializer
from django.db import IntegrityError
from django.http import HttpResponse

# --- ReportLab Imports for Phase 3 ---
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
# -----------------------------------

class HistoryListView(ListAPIView):
    """
    API endpoint to list the latest 5 uploaded datasets for the authenticated user.
    Uses the ordering defined in the model (newest first).
    """
    serializer_class = UploadedDatasetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Retrieve only the last 5 datasets for the current authenticated user
        return UploadedDataset.objects.filter(user=self.request.user)[:5]


class CSVUploadView(APIView):
    """
    API endpoint to handle CSV file upload, perform data analysis using Pandas,
    and save the data and summary to the database.
    """
    permission_classes = [IsAuthenticated]
    
    # Required columns for the analysis
    REQUIRED_COLUMNS = ['Equipment Name', 'Type', 'Flowrate', 'Pressure', 'Temperature']

    def post(self, request, *args, **kwargs):
        # 1. Check for file presence
        if 'file' not in request.FILES:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        # Simple check for CSV mime type (can be unreliable, but good practice)
        if not uploaded_file.name.endswith(('.csv', '.xlsx')):
             return Response({"error": "Unsupported file format. Please upload a CSV or Excel file."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. File Storage
        # Create a unique filename: user_id/original_filename
        filename = f"{request.user.id}_{uploaded_file.name}"
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        try:
            # Save the file to disk
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # 3. Data Processing and Analysis with Pandas
            
            # Read the file based on extension
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                # Should be caught by the file extension check, but safe to include
                return Response({"error": "Invalid file format."}, status=status.HTTP_400_BAD_REQUEST)

            # --- CRITICAL FIX: Clean up column names by stripping whitespace ---
            df.columns = df.columns.str.strip()
            # ------------------------------------------------------------------

            # Validate columns
            if not all(col in df.columns for col in self.REQUIRED_COLUMNS):
                missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
                # Delete the saved file before returning error
                os.remove(file_path) 
                return Response(
                    {"error": "Missing required columns in the dataset.", "missing": missing_cols},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Ensure numeric columns are actually numeric
            numeric_cols = ['Flowrate', 'Pressure', 'Temperature']
            for col in numeric_cols:
                # Coerce to numeric, turning non-numeric into NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Drop rows where critical numeric data is missing after coercion
                df.dropna(subset=[col], inplace=True)

            # Perform required analysis
            total_count = len(df)
            
            # Calculate averages, converting results to float/dict for JSON serialization
            avg_flowrate = float(df['Flowrate'].mean()) if total_count > 0 else 0.0
            avg_pressure = float(df['Pressure'].mean()) if total_count > 0 else 0.0
            avg_temperature = float(df['Temperature'].mean()) if total_count > 0 else 0.0
            
            # Calculate type distribution
            type_distribution = df['Type'].value_counts().to_dict()

            summary_data = {
                "total_records": total_count,
                "averages": {
                    "flowrate": avg_flowrate,
                    "pressure": avg_pressure,
                    "temperature": avg_temperature
                },
                "type_distribution": type_distribution,
                "data_preview": df.head(5).to_dict('records') # Optional: A small data preview
            }
            
            # 4. Save Metadata to Database
            dataset = UploadedDataset.objects.create(
                user=request.user,
                name=uploaded_file.name,
                summary_data=summary_data,
                file_path=file_path  # Stores the absolute path on disk
            )
            
            serializer = UploadedDatasetSerializer(dataset)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except pd.errors.EmptyDataError:
            # Delete the saved file if it's empty
            os.remove(file_path) 
            return Response({"error": "The uploaded file is empty or corrupted."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # General cleanup for errors after file save but before DB commit
            if os.path.exists(file_path):
                 os.remove(file_path)
            return Response({"error": f"An unexpected error occurred during processing: {str(e)}"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SummaryView(APIView):
    """
    API endpoint to retrieve the summary_data for a specific dataset ID (pk).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        # Ensure the user only retrieves their own dataset
        dataset = get_object_or_404(UploadedDataset, pk=pk, user=request.user)
        
        # Return only the summary_data field
        return Response(dataset.summary_data, status=status.HTTP_200_OK)


class PDFReportView(APIView):
    """
    Implements the PDF Report Generation logic using ReportLab.
    Generates a PDF summarizing dataset averages and type distribution.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        # 1. Fetch the dataset metadata
        dataset = get_object_or_404(UploadedDataset, pk=pk, user=request.user)
        summary = dataset.summary_data

        # 2. Configure the HTTP Response for PDF download
        response = HttpResponse(content_type='application/pdf')
        filename = f"Report_{dataset.name.split('.')[0]}_{dataset.timestamp.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # 3. Initialize ReportLab Document
        # Use SimpleDocTemplate for easy flowable management
        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Define custom styles (Renaming to avoid conflicts with ReportLab defaults)
        styles.add(ParagraphStyle(name='ReportTitle', fontSize=18, spaceAfter=20, alignment=1, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='CustomHeading', fontSize=14, spaceBefore=15, spaceAfter=10, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='NormalStyle', fontSize=10, spaceAfter=5))
        
        # --- PDF Content Generation ---
        
        # A. Title and Metadata
        title_text = f"Chemical Equipment Parameter Report"
        story.append(Paragraph(title_text, styles['ReportTitle']))
        
        story.append(Paragraph(f"<b>Dataset Name:</b> {dataset.name}", styles['NormalStyle']))
        story.append(Paragraph(f"<b>Uploaded By:</b> {request.user.username}", styles['NormalStyle']))
        story.append(Paragraph(f"<b>Timestamp:</b> {dataset.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", styles['NormalStyle']))
        story.append(Paragraph(f"<b>Total Records Processed:</b> {summary.get('total_records', 'N/A')}", styles['NormalStyle']))
        
        story.append(Spacer(1, 0.5 * inch))
        
        # B. Average Parameters Table
        story.append(Paragraph("Parameter Averages", styles['CustomHeading']))
        
        averages = summary.get('averages', {})
        avg_data = [
            ['Parameter', 'Average Value'],
            ['Flowrate', f"{averages.get('flowrate', 0.0):.2f}"],
            ['Pressure', f"{averages.get('pressure', 0.0):.2f}"],
            ['Temperature', f"{averages.get('temperature', 0.0):.2f}"],
        ]
        
        # Define table style
        avg_table = Table(avg_data, colWidths=[2 * inch, 2 * inch])
        avg_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(avg_table)
        
        story.append(Spacer(1, 0.5 * inch))
        
        # C. Equipment Type Distribution Table
        story.append(Paragraph("Equipment Type Distribution", styles['CustomHeading']))
        
        distribution = summary.get('type_distribution', {})
        dist_data = [
            ['Equipment Type', 'Count']
        ]
        # Sort distribution by count descending for readability
        sorted_distribution = sorted(distribution.items(), key=lambda item: item[1], reverse=True)
        
        for type_name, count in sorted_distribution:
            dist_data.append([type_name, str(count)])

        # Define table style
        dist_table = Table(dist_data, colWidths=[2 * inch, 2 * inch])
        dist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(dist_table)
        
        # 4. Build the PDF and return
        doc.build(story)
        
        return response