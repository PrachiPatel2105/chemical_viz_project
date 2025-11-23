import os
import pandas as pd
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import UploadedDataset
from .serializers import UploadedDatasetSerializer
from django.db import IntegrityError
from django.http import HttpResponse
from django.contrib.auth.models import User

# --- ReportLab Imports for PDF Generation ---
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch

# --- Matplotlib Imports for Chart Generation ---
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import base64

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')

        if not username or not password:
            return Response(
                {"error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(password) < 6:
            return Response(
                {"error": "Password must be at least 6 characters long"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )
            return Response(
                {
                    "message": "User registered successfully",
                    "username": user.username
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": f"Registration failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HistoryListView(ListAPIView):
    serializer_class = UploadedDatasetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UploadedDataset.objects.filter(user=self.request.user)[:5]
    
    def delete(self, request, pk, *args, **kwargs):
        dataset = get_object_or_404(UploadedDataset, pk=pk, user=request.user)
        
        if dataset.file_path and os.path.exists(dataset.file_path):
            try:
                os.remove(dataset.file_path)
            except OSError:
                pass
        
        dataset.delete()
        return Response({"message": "Dataset deleted successfully"}, status=status.HTTP_200_OK)


class CSVUploadView(APIView):
    permission_classes = [IsAuthenticated]
    
    REQUIRED_COLUMNS = ['Equipment Name', 'Type', 'Flowrate', 'Pressure', 'Temperature']

    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        if not uploaded_file.name.endswith(('.csv', '.xlsx')):
             return Response({"error": "Unsupported file format. Please upload a CSV or Excel file."}, status=status.HTTP_400_BAD_REQUEST)

        filename = f"{request.user.id}_{uploaded_file.name}"
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        try:
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                return Response({"error": "Invalid file format."}, status=status.HTTP_400_BAD_REQUEST)

            df.columns = df.columns.str.strip()

            if not all(col in df.columns for col in self.REQUIRED_COLUMNS):
                missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
                os.remove(file_path) 
                return Response(
                    {"error": "Missing required columns in the dataset.", "missing": missing_cols},
                    status=status.HTTP_400_BAD_REQUEST
                )

            numeric_cols = ['Flowrate', 'Pressure', 'Temperature']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df.dropna(subset=[col], inplace=True)

            total_count = len(df)
            
            avg_flowrate = float(df['Flowrate'].mean()) if total_count > 0 else 0.0
            avg_pressure = float(df['Pressure'].mean()) if total_count > 0 else 0.0
            avg_temperature = float(df['Temperature'].mean()) if total_count > 0 else 0.0
            
            type_distribution = df['Type'].value_counts().to_dict()

            summary_data = {
                "total_records": total_count,
                "averages": {
                    "flowrate": avg_flowrate,
                    "pressure": avg_pressure,
                    "temperature": avg_temperature
                },
                "type_distribution": type_distribution,
                "data_preview": df.head(5).to_dict('records')
            }
            
            dataset = UploadedDataset.objects.create(
                user=request.user,
                name=uploaded_file.name,
                summary_data=summary_data,
                file_path=file_path
            )
            
            serializer = UploadedDatasetSerializer(dataset)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except pd.errors.EmptyDataError:
            os.remove(file_path) 
            return Response({"error": "The uploaded file is empty or corrupted."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            if os.path.exists(file_path):
                 os.remove(file_path)
            return Response({"error": f"An unexpected error occurred during processing: {str(e)}"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None, *args, **kwargs):
        dataset_id = pk or request.GET.get('id')
        
        if not dataset_id:
            return Response({"error": "Dataset ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        dataset = get_object_or_404(UploadedDataset, pk=dataset_id, user=request.user)
        
        summary = dataset.summary_data
        
        response_data = {
            "records": summary.get("total_records", 0),
            "categories": list(summary.get("type_distribution", {}).keys()),
            "bar": {
                "title": "Equipment Type Distribution",
                "labels": list(summary.get("type_distribution", {}).keys()),
                "values": list(summary.get("type_distribution", {}).values())
            },
            "doughnut": {
                "categories": list(summary.get("type_distribution", {}).keys()),
                "counts": list(summary.get("type_distribution", {}).values())
            },
            "averages": summary.get("averages", {}),
            "data_preview": summary.get("data_preview", [])
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class PDFReportView(APIView):
    permission_classes = [IsAuthenticated]
    
    def create_bar_chart(self, distribution_data, title="Equipment Type Distribution"):
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(8, 5))
        fig.patch.set_facecolor('white')
        
        if not distribution_data:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=14, color='gray')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        else:
            sorted_items = sorted(distribution_data.items(), key=lambda x: x[1], reverse=True)
            labels, values = zip(*sorted_items) if sorted_items else ([], [])
            
            bars = ax.bar(labels, values, color=['#2563eb', '#7c3aed', '#dc2626', '#059669', '#d97706', '#0891b2', '#be185d'])
            
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Equipment Type', fontsize=12, fontweight='bold')
            ax.set_ylabel('Count', fontsize=12, fontweight='bold')
            
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                       f'{int(height)}', ha='center', va='bottom', fontweight='bold')
            
            plt.xticks(rotation=45, ha='right')
            
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def create_pie_chart(self, distribution_data, title="Equipment Type Distribution"):
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(7, 7))
        fig.patch.set_facecolor('white')
        
        if not distribution_data:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=14, color='gray')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        else:
            labels = list(distribution_data.keys())
            sizes = list(distribution_data.values())
            
            colors_palette = ['#2563eb', '#7c3aed', '#dc2626', '#059669', '#d97706', '#0891b2', '#be185d', '#6366f1']
            
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                            colors=colors_palette[:len(labels)],
                                            startangle=90, textprops={'fontsize': 10})
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        # Save to BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def create_averages_chart(self, averages_data, title="Parameter Averages"):
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor('white')
        
        if not averages_data:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=14, color='gray')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        else:
            parameters = list(averages_data.keys())
            values = list(averages_data.values())
            
            bars = ax.barh(parameters, values, color=['#059669', '#dc2626', '#d97706'])
            
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Average Value', fontsize=12, fontweight='bold')
            
            for i, (bar, value) in enumerate(zip(bars, values)):
                ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height()/2,
                       f'{value:.2f}', ha='left', va='center', fontweight='bold')
            
            ax.set_yticklabels([param.capitalize() for param in parameters])
        
        plt.tight_layout()
        
        # Save to BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer

    def get(self, request, pk=None, *args, **kwargs):
        dataset_id = pk or request.GET.get('id')
        
        if not dataset_id:
            return Response({"error": "Dataset ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        dataset = get_object_or_404(UploadedDataset, pk=dataset_id, user=request.user)
        summary = dataset.summary_data

        response = HttpResponse(content_type='application/pdf')
        filename = f"Report_{dataset.name.split('.')[0]}_{dataset.timestamp.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        styles.add(ParagraphStyle(name='ReportTitle', fontSize=18, spaceAfter=20, alignment=1, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='CustomHeading', fontSize=14, spaceBefore=15, spaceAfter=10, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='NormalStyle', fontSize=10, spaceAfter=5))
        
        title_text = f"Chemical Equipment Parameter Report"
        story.append(Paragraph(title_text, styles['ReportTitle']))
        
        story.append(Paragraph(f"<b>Dataset Name:</b> {dataset.name}", styles['NormalStyle']))
        story.append(Paragraph(f"<b>Uploaded By:</b> {request.user.username}", styles['NormalStyle']))
        story.append(Paragraph(f"<b>Timestamp:</b> {dataset.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", styles['NormalStyle']))
        story.append(Paragraph(f"<b>Total Records Processed:</b> {summary.get('total_records', 'N/A')}", styles['NormalStyle']))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # B. Parameter Averages Chart
        story.append(Paragraph("Parameter Averages Analysis", styles['CustomHeading']))
        
        averages = summary.get('averages', {})
        if averages:
            # Create and add averages chart
            avg_chart_buffer = self.create_averages_chart(averages, "Parameter Averages")
            avg_chart_img = Image(avg_chart_buffer, width=6*inch, height=3*inch)
            story.append(avg_chart_img)
            story.append(Spacer(1, 0.2 * inch))
            
            # Add summary table below chart
            avg_data = [
                ['Parameter', 'Average Value', 'Unit'],
                ['Flowrate', f"{averages.get('flowrate', 0.0):.2f}", 'L/min'],
                ['Pressure', f"{averages.get('pressure', 0.0):.2f}", 'bar'],
                ['Temperature', f"{averages.get('temperature', 0.0):.2f}", '°C'],
            ]
            
            avg_table = Table(avg_data, colWidths=[2*inch, 1.5*inch, 1*inch])
            avg_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            story.append(avg_table)
        
        story.append(Spacer(1, 0.4 * inch))
        
        # C. Equipment Type Distribution Charts
        story.append(Paragraph("Equipment Type Distribution Analysis", styles['CustomHeading']))
        
        distribution = summary.get('type_distribution', {})
        if distribution:
            # Create bar chart
            bar_chart_buffer = self.create_bar_chart(distribution, "Equipment Count by Type")
            bar_chart_img = Image(bar_chart_buffer, width=6*inch, height=3.5*inch)
            story.append(bar_chart_img)
            story.append(Spacer(1, 0.3 * inch))
            
            # Create pie chart
            pie_chart_buffer = self.create_pie_chart(distribution, "Equipment Type Distribution")
            pie_chart_img = Image(pie_chart_buffer, width=5*inch, height=5*inch)
            story.append(pie_chart_img)
            story.append(Spacer(1, 0.2 * inch))
            
            # Add summary table below charts
            dist_data = [['Equipment Type', 'Count', 'Percentage']]
            total_count = sum(distribution.values())
            sorted_distribution = sorted(distribution.items(), key=lambda item: item[1], reverse=True)
            
            for type_name, count in sorted_distribution:
                percentage = (count / total_count * 100) if total_count > 0 else 0
                dist_data.append([type_name, str(count), f"{percentage:.1f}%"])

            dist_table = Table(dist_data, colWidths=[2.5*inch, 1*inch, 1*inch])
            dist_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            story.append(dist_table)
        
        # 4. Build the PDF and return
        doc.build(story)
        
        return response