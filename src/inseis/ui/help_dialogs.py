"""Dialogs for the inseis application."""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QRadioButton, QButtonGroup,
    QFileDialog, QScrollArea, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QDialogButtonBox

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
        __version__ = "1.2.0"
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