"""Dialog windows for the InSeis application."""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QFormLayout,
    QLineEdit, QPushButton, QLabel, QTextEdit, QMessageBox,
    QListWidgetItem, QDialogButtonBox, QGroupBox, QRadioButton, 
    QButtonGroup, QFileDialog, QScrollArea, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from ..core import workflow_manager

class SaveWorkflowDialog(QDialog):
    """Dialog for saving a workflow."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Workflow")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Add name and description fields
        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        
        form_layout.addRow("Workflow Name:", self.name_edit)
        form_layout.addRow("Description:", self.description_edit)
        layout.addLayout(form_layout)
        
        # Add buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

class LoadWorkflowDialog(QDialog):
    """Dialog for loading a workflow."""
    def __init__(self, workflow_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load Workflow")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.workflow_files = workflow_files
        self.selected_file = None
        
        layout = QVBoxLayout(self)
        
        # Add workflow list
        list_label = QLabel("Available Workflows:")
        layout.addWidget(list_label)
        
        self.workflow_list = QListWidget()
        layout.addWidget(self.workflow_list)
        
        # Add details section
        details_label = QLabel("Workflow Details:")
        layout.addWidget(details_label)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        layout.addWidget(self.details_text)
        
        # Add buttons
        button_layout = QHBoxLayout()
        self.load_button = QPushButton("Load")
        self.load_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_workflow)
        
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # Disable buttons until selection made
        self.load_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        
        # Populate the list
        self.populate_workflows()
        
        # Connect signals
        self.workflow_list.currentItemChanged.connect(self.show_workflow_details)
        
    def populate_workflows(self):
        """Populate the list with available workflows."""
        self.workflow_list.clear()
        
        for file_info in self.workflow_files:
            item = QListWidgetItem(file_info['name'])
            item.setData(Qt.UserRole, file_info)
            self.workflow_list.addItem(item)
    
    def show_workflow_details(self, current, previous):
        """Display details of the selected workflow."""
        if current:
            file_info = current.data(Qt.UserRole)
            self.selected_file = file_info['file_path']
            
            details = f"Name: {file_info['name']}\n"
            details += f"Description: {file_info['description']}\n"
            details += f"Created: {file_info['created']}\n"
            details += f"Processes: {file_info['process_count']} processes"
            
            self.details_text.setText(details)
            self.load_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else:
            self.selected_file = None
            self.details_text.clear()
            self.load_button.setEnabled(False)
            self.delete_button.setEnabled(False)
    
    def delete_workflow(self):
        """Delete the selected workflow."""
        if not self.selected_file:
            return
            
        reply = QMessageBox.question(
            self, "Delete Workflow", 
            f"Are you sure you want to delete the workflow '{self.workflow_list.currentItem().text()}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = workflow_manager.delete_workflow(self.selected_file)
            if success:
                self.workflow_files.remove(self.workflow_list.currentItem().data(Qt.UserRole))
                self.workflow_list.takeItem(self.workflow_list.currentRow())
                self.details_text.clear()
                self.load_button.setEnabled(False)
                self.delete_button.setEnabled(False)
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.warning(self, "Error", message)

class FirstRunDialog(QDialog):
    """Dialog shown on first run to configure application settings."""
    
    def __init__(self, parent=None, default_location=None):
        """Initialize the dialog with the default storage location."""
        super().__init__(parent)
        self.selected_location = default_location
        self.custom_location = None
        
        self.setWindowTitle("Welcome to InSeis!")
        self.resize(600, 400)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Welcome heading
        welcome_label = QLabel("Welcome to InSeis!", self)
        welcome_label.setFont(QFont("Arial", 18, QFont.Bold))
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Description
        description = QLabel(
            "Choose where you'd like to store your workflow data, jobs, and presets.\n"
            "You can change this later in the application settings.\n", 
            self
        )
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        layout.addSpacing(20)
        
        # Location options group
        location_group = QGroupBox("Data Storage Location", self)
        location_layout = QVBoxLayout()
        
        # Radio button group
        self.location_btn_group = QButtonGroup(self)
        
        # Default location option (from appdirs)
        self.default_radio = QRadioButton("Default location (system-managed)", self)
        self.default_radio.setToolTip(f"Store in: {self.selected_location}")
        self.location_btn_group.addButton(self.default_radio, 1)
        location_layout.addWidget(self.default_radio)
        
        # Documents folder option
        documents_path = os.path.join(os.path.expanduser("~"), "Documents", "InSeis")
        self.documents_radio = QRadioButton(f"Documents folder: {documents_path}", self)
        self.location_btn_group.addButton(self.documents_radio, 2)
        location_layout.addWidget(self.documents_radio)
        
        # Custom location option
        custom_layout = QHBoxLayout()
        self.custom_radio = QRadioButton("Custom location:", self)
        self.location_btn_group.addButton(self.custom_radio, 3)
        custom_layout.addWidget(self.custom_radio)
        
        self.browse_btn = QPushButton("Browse...", self)
        self.browse_btn.clicked.connect(self.browse_location)
        custom_layout.addWidget(self.browse_btn)
        
        location_layout.addLayout(custom_layout)
        
        # Selected path display
        self.path_label = QLabel("", self)
        location_layout.addWidget(self.path_label)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.continue_btn = QPushButton("Continue", self)
        self.continue_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.continue_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Set default selection
        self.default_radio.setChecked(True)
        self.location_btn_group.buttonClicked.connect(self.update_selection)
    
    def browse_location(self):
        """Open file dialog to select custom location."""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Directory for InSeis Data",
            os.path.expanduser("~")
        )
        
        if directory:
            self.custom_location = os.path.join(directory, "InSeis")
            self.path_label.setText(f"Selected: {self.custom_location}")
            self.custom_radio.setChecked(True)
            self.update_selection(self.custom_radio)
    
    def update_selection(self, button):
        """Update the selected location based on radio button choice."""
        if button == self.default_radio:
            self.selected_location = self.selected_location
        elif button == self.documents_radio:
            self.selected_location = os.path.join(os.path.expanduser("~"), "Documents", "InSeis")
        elif button == self.custom_radio and self.custom_location:
            self.selected_location = self.custom_location
    
    def get_selected_location(self):
        """Return the user's selected location."""
        return self.selected_location

class AboutDialog(QDialog):
    """Dialog displaying information about the application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("About InSeis")
        
        # Calculate window size and position
        screen = QApplication.primaryScreen().geometry()
        screen_width = min(screen.width(), 1920)
        screen_height = min(screen.height(), 1080)
        window_width = int(screen_width * 0.3)
        window_height = int(screen_height * 0.5)
        pos_x = (screen_width - window_width) // 2
        pos_y = (screen_height - window_height) // 2
        self.setGeometry(pos_x, pos_y, window_width, window_height)
        
        layout = QVBoxLayout(self)
        
        # App title
        title = QLabel("velrecover")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        
        # Version and copyright info
        __version__ = "1.3.0"
        version = QLabel(f"Version {__version__}")
        version.setAlignment(Qt.AlignCenter)
        
        copyright = QLabel("© 2025 Alejandro Pertuz")
        copyright.setAlignment(Qt.AlignCenter)
        
        # Description text
        description = QLabel(
            "A GUI tool for using Seismic Unix through Windows Subsystem for Linux (WSL).")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        
        # License info
        license_info = QLabel("Released under the GPL-3.0 License")
        license_info.setAlignment(Qt.AlignCenter)
        
        # Add all widgets to layout
        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(copyright)
        layout.addSpacing(10)
        layout.addWidget(description)
        layout.addSpacing(20)
        layout.addWidget(license_info)
        
        # Add OK button at bottom
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

class HelpDialog(QDialog):
    """Help dialog with information about the application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How to Use subrdigepy")    
        screen = QApplication.primaryScreen().geometry()
        screen_width = min(screen.width(), 1920)
        screen_height = min(screen.height(), 1080)
        pos_x = int(screen_width * 0.45 + 20)
        pos_y = int(screen_height * 0.15)
        window_width= int(screen_width * 0.3)
        window_height = int(screen_height * 0.85)
        self.setGeometry(pos_x, pos_y, window_width, window_height)          
        # Create scroll area
        scroll = QWidget()
        scroll_layout = QVBoxLayout(scroll)
        
        # Add content
        msg = """
        <h1 style="color:#2B66CC; text-align:center;">Welcome to InSeis</h1>
        <h3 style="text-align:center;">A GUI for Seismic Unix Processing Workflows</h3>
        
        <hr>
        
        <h2>📋 Quick Start Guide</h2>
        <p>InSeis allows you to create, save, and run Seismic Unix processing workflows through a user-friendly interface.</p>
        
        <h2>🖼️ Interface Overview</h2>
        <p>The application is divided into three main panels:</p>
        <ul>
            <li><b>Available Processes</b> (left) - Process library grouped by category</li>
            <li><b>Current Workflow</b> (middle) - Your workflow steps in sequence</li>
            <li><b>Process Parameters</b> (right) - Configure parameters for each process</li>
        </ul>
        
        <h2>🔄 Creating a Workflow</h2>
        <ol>
            <li><b>Select a process</b> from the left panel (e.g., "Load SU" to start)</li>
            <li><b>Configure parameters</b> in the right panel
                <ul>
                    <li>Required parameters are marked with an asterisk (*)</li>
                    <li>For file inputs, use the Browse button</li>
                </ul>
            </li>
            <li><b>Add to workflow</b> by clicking the "Add to Workflow" button</li>
            <li><b>Continue adding processes</b> to build your complete workflow</li>
            <li><b>Reorder processes</b> using the up/down arrows in the workflow panel if needed</li>
        </ol>
        
        <h2>⚙️ Running a Workflow</h2>
        <ol>
            <li>Enter a <b>Job Name</b> in the input field (optional)</li>
            <li>Click the <b>Run Workflow</b> button in the middle panel</li>
            <li>A progress dialog will appear showing execution status</li>
            <li>Results will be saved in the Jobs folder and displayed for visualization if applicable</li>
        </ol>
        
        <h2>💾 Managing Workflows</h2>
        <p>Use the <b>Workflows</b> menu to:</p>
        <ul>
            <li><b>Save Workflow</b> - Save your current workflow for future use</li>
            <li><b>Load Workflow</b> - Load a previously saved workflow</li>
        </ul>
        
        <h2>📊 Visualization</h2>
        <p>After running a workflow, results will be automatically visualized:</p>
        <ul>
            <li>Use tabs to switch between different outputs</li>
            <li>Adjust the percentile value to control clipping</li>
            <li>Change the horizontal axis to view different aspects of the data</li>
        </ul>
        
        <h2>⚠️ Troubleshooting</h2>
        <ul>
            <li><b>WSL not found</b> - Ensure Windows Subsystem for Linux is installed and enabled</li>
            <li><b>Seismic Unix not found</b> - Set the correct CWPROOT path in Configuration menu</li>
            <li><b>Missing parameters</b> - Check for required parameters marked with asterisk (*)</li>
            <li><b>See console output</b> - Check the console panel at the bottom for error messages</li>
        </ul>
        
        <h2>🔍 Documentation</h2>
        <p>For detailed documentation on specific Seismic Unix commands:</p>
        <ol>
            <li>Select a process in the Process Parameters panel</li>
            <li>Click the "Show Documentation" button</li>
        </ol>
        
        <hr>
        <p style="text-align:center;"><i>For more information, visit the <a href="https://github.com/a-pertuz/InSeis/">InSeis GitHub repository</a>.</i></p>
        """
        
        # Create text label with HTML content
        text = QLabel(msg)
        text.setWordWrap(True)
        text.setTextFormat(Qt.RichText)
        scroll_layout.addWidget(text)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll)
        scroll_area.setWidgetResizable(True)
        
        # Create main layout
        layout = QVBoxLayout(self)
        layout.addWidget(scroll_area)
        
        # Add OK button at bottom
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
