"""Dialog windows for the InSeis application."""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QFormLayout,
                              QLineEdit, QPushButton, QLabel, QTextEdit, QMessageBox,
                              QListWidgetItem, QProgressBar, QDialogButtonBox)
from PySide6.QtCore import Qt, Signal, QTimer

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

class WorkflowProgressDialog(QDialog):
    """Dialog shown during workflow execution."""
    
    def __init__(self, parent=None, job_name=""):
        super().__init__(parent)
        self.setWindowTitle("Running Workflow")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setMinimumWidth(400)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setModal(True)
        
        # Create main layout
        layout = QVBoxLayout(self)
        
        # Add job name label
        if job_name:
            job_label = QLabel(f"Executing: {job_name}")
            job_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(job_label)
        
        # Add animated processing label
        self.status_label = QLabel("Processing workflow...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Add indeterminate progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        layout.addWidget(self.progress_bar)
        
        # Add stop button
        self.button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # Setup animation for dots
        self.dots_count = 0
        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(500)  # Update every 500ms
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.start()
        
        # Initial animation update
        self._update_animation()
    
    def _update_animation(self):
        """Update the animation dots."""
        self.dots_count = (self.dots_count + 1) % 4
        dots = "." * self.dots_count
        self.status_label.setText(f"Processing workflow{dots}")
    
    def update_status(self, text):
        """Update the status text."""
        self.status_label.setText(text)
    
    def set_determinate_progress(self, current, total):
        """Switch to determinate progress mode with current/total values."""
        if self.progress_bar.maximum() == 0:  # Currently indeterminate
            self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Processing step {current} of {total}")
        

