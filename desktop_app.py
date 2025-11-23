import sys
import os
import requests
import json
import base64
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QLineEdit, QLabel, QSplitter,
    QFileDialog, QDialog, QMessageBox, QTabWidget, QGridLayout,
    QListWidgetItem
)
from PyQt5.QtGui import QFont, QIcon, QColor
from PyQt5.QtCore import Qt, QSize, QByteArray, QDateTime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import matplotlib.pyplot as plt
plt.style.use('dark_background')

API_BASE_URL = 'http://127.0.0.1:8000/api'
REQUIRED_COLUMNS = ['Equipment Name', 'Type', 'Flowrate', 'Pressure', 'Temperature']
class MplCanvas(FigureCanvas):
    """A simple canvas class for embedding Matplotlib figures."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        # Set figure background to match dark theme
        self.fig.patch.set_facecolor('#1e1e1e')
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.setMinimumHeight(300)

    def update_bar_chart(self, distribution):
        self.axes.clear()
        if not distribution:
            self.axes.text(0.5, 0.5, "No data uploaded.", ha='center', va='center', fontsize=12, color='gray')
            self.axes.set_xticks([])
            self.draw()
            return
        
        types = list(distribution.keys())
        counts = list(distribution.values())
        
        bars = self.axes.bar(types, counts, color='#8b5cf6')
        self.axes.set_title('Equipment Type Distribution', color='white')
        self.axes.set_xlabel('Equipment Type', color='white')
        self.axes.set_ylabel('Count', color='white')
        self.fig.tight_layout()
        self.draw()

    def update_pie_chart(self, averages):
        self.axes.clear()
        if not any(averages.values()):
            self.axes.text(0.5, 0.5, "No numeric data found.", ha='center', va='center', fontsize=12, color='gray')
            self.draw()
            return
            
        labels = ['Flowrate', 'Pressure', 'Temperature']
        values = [averages.get('flowrate', 0.0), averages.get('pressure', 0.0), averages.get('temperature', 0.0)]
        
        valid_data = [(l, v) for l, v in zip(labels, values) if v > 0]
        labels = [item[0] for item in valid_data]
        values = [item[1] for item in valid_data]

        colors = ['#f87171', '#34d399', '#60a5fa']

        wedges, texts, autotexts = self.axes.pie(
            values, labels=labels, autopct='%1.1f%%', startangle=90, 
            colors=colors, wedgeprops={'edgecolor': 'white'}
        )
        self.axes.set_title('Relative Parameter Averages', color='white')
        self.axes.axis('equal')
        self.draw()


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Login")
        self.setFixedSize(350, 200)
        self.auth_token = None
        self.username = None
        
        self.layout = QVBoxLayout(self)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.login_button = QPushButton("Log In")
        self.login_button.clicked.connect(self.attempt_login)
        
        self.status_label = QLabel("Enter API Credentials")
        self.status_label.setStyleSheet("color: #9ca3af;")

        self.layout.addWidget(QLabel("Username:"))
        self.layout.addWidget(self.username_input)
        self.layout.addWidget(QLabel("Password:"))
        self.layout.addWidget(self.password_input)
        self.layout.addWidget(self.login_button)
        self.layout.addWidget(self.status_label)
        
        self.setStyleSheet(
            """
            QDialog { background-color: #1e1e1e; color: #ffffff; }
            QLabel { color: #d1d5db; font-weight: bold; }
            QLineEdit { 
                background-color: #374151; 
                color: #ffffff; 
                border: 1px solid #4b5563; 
                padding: 5px; 
                border-radius: 4px;
            }
            QPushButton {
                background-color: #4f46e5;
                color: white;
                padding: 8px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #4338ca; }
            """
        )

    def attempt_login(self):
        user = self.username_input.text()
        password = self.password_input.text()
        
        if not user or not password:
            self.status_label.setText("Username and password are required.")
            return

        try:
            # Generate Basic Auth header
            auth_bytes = f"{user}:{password}".encode("utf-8")
            auth_token = "Basic " + base64.b64encode(auth_bytes).decode("utf-8")
            
            headers = {'Authorization': auth_token}
            self.status_label.setText("Authenticating...")

            response = requests.get(f"{API_BASE_URL}/history/", headers=headers, timeout=5)
            
            if response.status_code == 200:
                self.auth_token = auth_token
                self.username = user
                self.accept()
            else:
                self.status_label.setText(f"Login failed: {response.status_code} UNAUTHORIZED.")
                self.auth_token = None

        except requests.exceptions.RequestException as e:
            self.status_label.setText(f"Connection error: Check Django server.")
            QMessageBox.critical(self, "Connection Error", f"Could not connect to Django API: {e}")
            self.auth_token = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chemical Parameter Visualizer")
        self.setGeometry(100, 100, 1200, 800)
        self.auth_token = None
        self.username = None
        self.current_summary = {}
        self.selected_dataset_id = None

        self.setStyleSheet(
            """
            QMainWindow, QWidget { background-color: #121212; color: #ffffff; }
            QListWidget { background-color: #1e1e1e; border: 1px solid #333333; padding: 5px; }
            QListWidget::item { padding: 5px; border-bottom: 1px solid #333333; }
            QListWidget::item:selected { background-color: #4f46e5; color: white; }
            QLabel#Title { color: #4f46e5; font-size: 24px; font-weight: bold; margin-bottom: 10px; }
            QLabel#SubTitle { color: #d1d5db; font-size: 16px; font-weight: bold; margin-top: 15px; }
            QPushButton {
                background-color: #4f46e5;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #4338ca; }
            QPushButton#Logout { background-color: #dc2626; }
            QPushButton#Logout:hover { background-color: #b91c1c; }
            """
        )

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.login_and_setup()

    def login_and_setup(self):
        login_dialog = LoginDialog(self)
        if login_dialog.exec_() == QDialog.Accepted:
            self.auth_token = login_dialog.auth_token
            self.username = login_dialog.username
            self.setup_ui()
            self.fetch_history()
        else:
            QMessageBox.warning(self, "Login Required", "Application requires successful API login to proceed.")
            QApplication.quit() 

    def setup_ui(self):
        for i in reversed(range(self.main_layout.count())): 
            widget = self.main_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.sidebar = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar.setFixedWidth(300)
        self.sidebar.setStyleSheet("background-color: #1e1e1e; padding: 10px; border-radius: 8px;")

        self.logout_button = QPushButton("Logout", self)
        self.logout_button.setObjectName("Logout")
        self.logout_button.clicked.connect(self.logout)
        self.sidebar_layout.addWidget(self.logout_button)
        
        upload_group = QWidget()
        upload_layout = QVBoxLayout(upload_group)
        upload_layout.addWidget(QLabel("Upload CSV/Excel", objectName="SubTitle"))
        
        self.file_path_label = QLineEdit()
        self.file_path_label.setPlaceholderText("Select file...")
        self.file_path_label.setReadOnly(True)
        
        file_select_button = QPushButton("Browse")
        file_select_button.clicked.connect(self.select_file)
        
        self.upload_button = QPushButton("Upload & Analyze")
        self.upload_button.clicked.connect(self.upload_file)
        self.upload_button.setEnabled(False)

        upload_layout.addWidget(self.file_path_label)
        upload_layout.addWidget(file_select_button)
        upload_layout.addWidget(self.upload_button)
        self.sidebar_layout.addWidget(upload_group)

        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_summary)
        self.sidebar_layout.addWidget(QLabel("History (Last 5)", objectName="SubTitle"))
        self.sidebar_layout.addWidget(self.history_list)
        
        self.vis_area = QWidget()
        self.vis_layout = QVBoxLayout(self.vis_area)
        
        self.title_label = QLabel(f"Welcome, {self.username}. Select a dataset to visualize.")
        self.title_label.setObjectName("Title")
        self.vis_layout.addWidget(self.title_label)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            """
            QTabWidget::pane { border: 1px solid #333333; }
            QTabBar::tab { background: #1e1e1e; color: #d1d5db; padding: 10px; }
            QTabBar::tab:selected { background: #374151; color: white; }
            """
        )
        
        self.chart_widget = QWidget()
        self.chart_layout = QGridLayout(self.chart_widget)
        
        self.bar_chart = MplCanvas(self)
        self.bar_chart.axes.set_title("Equipment Type Distribution", color='white')
        self.chart_layout.addWidget(self.bar_chart, 0, 0)
        
        self.pie_chart = MplCanvas(self)
        self.pie_chart.axes.set_title("Relative Parameter Averages", color='white')
        self.chart_layout.addWidget(self.pie_chart, 0, 1)

        self.tab_widget.addTab(self.chart_widget, "Charts & Averages")

        self.data_label = QLabel("Data Preview and Statistics will appear here.")
        self.data_label.setWordWrap(True)
        self.tab_widget.addTab(self.data_label, "Data & Stats")

        self.vis_layout.addWidget(self.tab_widget)
        
        self.pdf_button = QPushButton("Download PDF Report")
        self.pdf_button.clicked.connect(self.download_pdf)
        self.pdf_button.setEnabled(False)
        self.vis_layout.addWidget(self.pdf_button)
        
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.vis_area)
        self.splitter.setSizes([300, 900])
        
        self.main_layout.addWidget(self.splitter)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def logout(self):
        self.auth_token = None
        self.username = None
        QApplication.quit()

    def get_headers(self):
        return {'Authorization': self.auth_token}

    def fetch_history(self):
        try:
            response = requests.get(f"{API_BASE_URL}/history/", headers=self.get_headers(), timeout=5)
            response.raise_for_status()
            
            self.history_list.clear()
            datasets = response.json()
            
            for dataset in datasets:
                item = QListWidgetItem(f"{dataset['name']}\n{dataset['timestamp']}")
                item.setData(Qt.UserRole, dataset['id']) 
                self.history_list.addItem(item)

            if datasets and not self.selected_dataset_id:
                newest_id = datasets[0]['id']
                self.load_summary(self.history_list.item(0))

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "API Error", f"Failed to fetch history: {e}")
            self.logout()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV/Excel File", "", "Data Files (*.csv *.xlsx)"
        )
        if file_path:
            self.file_path_label.setText(file_path)
            self.upload_button.setEnabled(True)

    def upload_file(self):
        file_path = self.file_path_label.text()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Upload Error", "Please select a valid file.")
            return

        self.upload_button.setEnabled(False)
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
                
                response = requests.post(
                    f"{API_BASE_URL}/upload/", 
                    headers=self.get_headers(), 
                    files=files, 
                    timeout=30
                )
                response.raise_for_status()
                
                upload_data = response.json()
                QMessageBox.information(self, "Success", f"File '{os.path.basename(file_path)}' uploaded and analyzed successfully.")
                self.file_path_label.clear()
                self.upload_button.setEnabled(False)
                
                self.fetch_history()
                
                if upload_data and 'id' in upload_data:
                    for i in range(self.history_list.count()):
                        item = self.history_list.item(i)
                        if item.data(Qt.UserRole) == upload_data['id']:
                            self.history_list.setCurrentItem(item)
                            self.load_summary(item)
                            break

        except requests.exceptions.HTTPError as e:
            try:
                error_data = e.response.json()
                error_msg = error_data.get('error', str(e))
                if 'missing' in error_data:
                    error_msg += f"\nMissing Columns: {', '.join(error_data['missing'])}"
                QMessageBox.critical(self, "API Error", error_msg)
            except json.JSONDecodeError:
                QMessageBox.critical(self, "API Error", f"Upload failed: {e.response.text}")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect or upload: {e}")
        finally:
            self.upload_button.setEnabled(True)

    def load_summary(self, item):
        dataset_id = item.data(Qt.UserRole)
        self.selected_dataset_id = dataset_id
        
        try:
            response = requests.get(f"{API_BASE_URL}/summary/{dataset_id}/", headers=self.get_headers(), timeout=5)
            response.raise_for_status()
            
            self.current_summary = response.json()
            self.update_visualization()
            self.pdf_button.setEnabled(True)
            self.title_label.setText(f"Visualization Summary: {item.text().splitlines()[0]}")
            
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "API Error", f"Failed to load summary: {e}")
            self.current_summary = {}
            self.pdf_button.setEnabled(False)

    def download_pdf(self):
        if not self.selected_dataset_id:
            QMessageBox.warning(self, "Download Error", "Please select a dataset first.")
            return

        try:
            response = requests.get(
                f"{API_BASE_URL}/report/{self.selected_dataset_id}/", 
                headers=self.get_headers(), 
                stream=True, 
                timeout=10
            )
            response.raise_for_status()

            filename = response.headers.get('Content-Disposition', 'report.pdf')
            if 'filename=' in filename:
                filename = filename.split('filename=')[1].strip('"\'')
            
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Save PDF Report", filename, "PDF Files (*.pdf)"
            )
            
            if save_path:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                QMessageBox.information(self, "Success", f"PDF Report saved successfully to:\n{save_path}")

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "API Error", f"Failed to download PDF: {e}")

    def update_visualization(self):
        summary = self.current_summary

        bar_data = summary.get('bar', {})
        if bar_data and 'labels' in bar_data and 'values' in bar_data:
            distribution = dict(zip(bar_data['labels'], bar_data['values']))
        else:
            distribution = summary.get('type_distribution', {})
        
        self.bar_chart.update_bar_chart(distribution)
        
        averages = summary.get('averages', {})
        self.pie_chart.update_pie_chart(averages)
        
        stats_html = self.generate_stats_html(summary)
        self.data_label.setText(stats_html)
        self.data_label.setStyleSheet("background-color: #1e1e1e; color: #ffffff; padding: 15px;")

    def generate_stats_html(self, summary):
        total_records = summary.get('records', summary.get('total_records', 'N/A'))
        
        html = f"""
        <div style="font-family: Arial, sans-serif; background-color: #1e1e1e; color: #d1d5db; padding: 10px;">
            <h3 style="color: #4f46e5; margin-top: 0;">Overall Statistics</h3>
            <p><strong>Total Records Processed:</strong> {total_records}</p>
            
            <h3 style="color: #4f46e5; margin-top: 20px;">Parameter Averages</h3>
            <table style="width: 50%; border-collapse: collapse; color: #d1d5db;">
                <tr>
                    <th style="border: 1px solid #333; padding: 8px; background-color: #374151;">Parameter</th>
                    <th style="border: 1px solid #333; padding: 8px; background-color: #374151;">Average Value</th>
                </tr>
        """
        averages = summary.get('averages', {})
        for key, value in averages.items():
            html += f"""
                <tr>
                    <td style="border: 1px solid #333; padding: 8px;">{key.capitalize()}</td>
                    <td style="border: 1px solid #333; padding: 8px; text-align: right; color: #34d399;">{value:.2f}</td>
                </tr>
            """
        html += "</table>"
        
        html += f"""
            <h3 style="color: #4f46e5; margin-top: 20px;">Data Preview (First 5 Rows)</h3>
            <table style="width: 100%; border-collapse: collapse; color: #d1d5db;">
                <tr>
                    <th style="border: 1px solid #333; padding: 8px; background-color: #374151; text-align: left;">Equipment Name</th>
                    <th style="border: 1px solid #333; padding: 8px; background-color: #374151; text-align: left;">Type</th>
                    <th style="border: 1px solid #333; padding: 8px; background-color: #374151; text-align: right;">Flowrate</th>
                    <th style="border: 1px solid #333; padding: 8px; background-color: #374151; text-align: right;">Pressure</th>
                    <th style="border: 1px solid #333; padding: 8px; background-color: #374151; text-align: right;">Temperature</th>
                </tr>
        """
        preview = summary.get('data_preview', [])
        for row in preview:
            html += f"""
                <tr>
                    <td style="border: 1px solid #333; padding: 8px;">{row.get('Equipment Name', 'N/A')}</td>
                    <td style="border: 1px solid #333; padding: 8px;">{row.get('Type', 'N/A')}</td>
                    <td style="border: 1px solid #333; padding: 8px; text-align: right;">{row.get('Flowrate', 0.0):.2f}</td>
                    <td style="border: 1px solid #333; padding: 8px; text-align: right;">{row.get('Pressure', 0.0):.2f}</td>
                    <td style="border: 1px solid #333; padding: 8px; text-align: right;">{row.get('Temperature', 0.0):.2f}</td>
                </tr>
            """
        html += "</table></div>"
        
        return html


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    app.setStyle("Fusion") 
    
    palette = app.palette()
    palette.setColor(palette.Window, Qt.GlobalColor.black)
    palette.setColor(palette.WindowText, Qt.GlobalColor.white)
    palette.setColor(palette.Base, Qt.GlobalColor.darkGray)
    palette.setColor(palette.AlternateBase, QColor('#282828')) 
    palette.setColor(palette.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(palette.ToolTipText, Qt.GlobalColor.black)
    palette.setColor(palette.Text, Qt.GlobalColor.white)
    palette.setColor(palette.Button, Qt.GlobalColor.darkGray)
    palette.setColor(palette.ButtonText, Qt.GlobalColor.white)
    palette.setColor(palette.BrightText, Qt.GlobalColor.red)
    palette.setColor(palette.Link, Qt.GlobalColor.cyan)
    palette.setColor(palette.Highlight, Qt.GlobalColor.blue)
    palette.setColor(palette.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())