"""Main window for the inseis application."""

import os
import subprocess
from PySide6.QtWidgets import (QMainWindow, QWidget, QApplication, QHBoxLayout, QVBoxLayout, QListWidget,
                             QFormLayout, QLineEdit, QPushButton, QLabel, QMessageBox,
                             QGroupBox, QTextEdit, QInputDialog, QCheckBox, QScrollArea,
                             QFileDialog, QDialog, QTreeWidget, QTreeWidgetItem, QComboBox,
                             QSplitter)
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QAction, QClipboard, QColor, QTextCharFormat, QFont

from ..core import process_manager
from ..core.process_manager import Process
from ..core import workflow_manager
from ..ui.dialogs import SaveWorkflowDialog, LoadWorkflowDialog, FirstRunDialog, HelpDialog, AboutDialog
from ..ui.visualization import VisualizationDialog
from ..ui.panels import ProcessPanel, WorkflowPanel, ParametersPanel
from .workflow_controller import WorkflowController
from ..config import settings
from ..utils.console import ConsoleWidget
from ..utils.path_utils import PathManager

class InSeis(QMainWindow):
    """Main application window for InSeis."""
    
    def __init__(self):
        """Initialize the main application window."""
        super().__init__()
        self.setWindowTitle("InSeis - Seismic Unix Workflow Manager")
        
        # Initialize workflow-related data
        self.workflow_processes = []
        self.current_process = None
        self.current_workflow_index = -1
        self.is_workflow_modified = False
        
        # Load process definitions
        self.available_processes, self.categorized_processes = process_manager.load_process_definitions()
        
        # Set up the UI components
        self.setup_ui()
        
        # Handle first run setup
        self.handle_first_run()
        
        # Ensure directories exist
        settings.ensure_directories()
        
        # Load configuration
        config = settings.load_config()
        self.cwproot = config.get("cwproot", settings.DEFAULT_CONFIG["cwproot"])
        
        # Check environment
        self.check_environment()
        
        # Setup menus
        self.setup_menus()
        
        # Create workflow controller
        self.workflow_controller = WorkflowController(self, self.console)
        self.workflow_controller.visualizationRequested.connect(self.show_visualization)

        # Show info about loaded processes and data directory in console
        if self.console:
            self.console.log_info(f"Data directory: {settings.USER_DATA_DIR}")
            self.console.log_info(f"Config directory: {settings.CONFIG_DIR}")
            self.console.log_info("")
            
            if not self.available_processes:
                self.console.log_warning("No process definitions found. Please add JSON definitions to the process_definitions directory.")
            else:
                self.console.log_success(f"Loaded {len(self.available_processes)} processes from definitions.")
    
    def setup_ui(self):
        """Set up the user interface components."""
        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create a vertical splitter for the main UI sections
        self.main_splitter = QSplitter(Qt.Vertical)
        
        # Top widget for panels
        panels_widget = QWidget()
        panels_layout = QVBoxLayout(panels_widget)
        panels_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create horizontal splitter for the three panels
        self.horizontal_splitter = QSplitter(Qt.Horizontal)
        
        # Process panel (left)
        self.process_panel = ProcessPanel()
        self.process_panel.set_processes(self.available_processes, self.categorized_processes)
        self.process_panel.processSelected.connect(self.on_process_selected)
        self.horizontal_splitter.addWidget(self.process_panel)
        
        # Workflow panel (center)
        self.workflow_panel = WorkflowPanel()
        self.workflow_panel.processSelected.connect(self.on_workflow_process_selected)
        self.workflow_panel.runWorkflowRequested.connect(self.run_workflow)
        self.workflow_panel.swapProcesses.connect(self.swap_workflow_processes)
        self.horizontal_splitter.addWidget(self.workflow_panel)
        
        # Parameters panel (right)
        self.parameters_panel = ParametersPanel()
        self.parameters_panel.addToWorkflowRequested.connect(self.add_to_workflow)
        self.parameters_panel.acceptEditsRequested.connect(self.accept_workflow_edit)
        self.parameters_panel.removeFromWorkflowRequested.connect(self.remove_from_workflow)
        self.parameters_panel.showDocumentation.connect(self.show_su_doc)
        self.horizontal_splitter.addWidget(self.parameters_panel)
        
        # Add the horizontal splitter to the panels layout
        panels_layout.addWidget(self.horizontal_splitter)
        
       
        total_width = 1000  # Arbitrary reference width
        self.horizontal_splitter.setSizes([int(total_width * 0.25), int(total_width * 0.2), int(total_width * 0.55)])
        
        # Add panels widget to the main vertical splitter
        self.main_splitter.addWidget(panels_widget)
        
        # Bottom widget for job name and console
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # Job name input
        job_layout = QHBoxLayout()
        job_layout.addWidget(QLabel("Job Name:"))
        self.job_name_input = QLineEdit()
        self.job_name_input.setPlaceholderText("Enter custom job name (optional)")
        job_layout.addWidget(self.job_name_input)
        bottom_layout.addLayout(job_layout)
        
        # Console widget
        self.console = ConsoleWidget()
        bottom_layout.addWidget(self.console)
        
        # Add bottom widget to the splitter
        self.main_splitter.addWidget(bottom_widget)
        
        # Add the main splitter to the main layout
        main_layout.addWidget(self.main_splitter)
        
        # Set initial sizes for the main splitter (allocate more space to panels initially)
        self.main_splitter.setSizes([600, 400])
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def handle_first_run(self):
        """Handle first run setup."""
        if settings.is_first_run():
            # Show first run dialog
            dialog = FirstRunDialog(self, settings.DATA_DIR)
            result = dialog.exec()
            
            if result == QDialog.Accepted:
                # Get the selected location
                selected_dir = dialog.get_selected_location()
                if selected_dir != settings.DATA_DIR:
                    # Update the data directory
                    settings.update_data_dir(selected_dir)
                else:
                    # Using default, just mark first run complete
                    settings.complete_first_run_setup()
            else:
                # User canceled, use default and mark as completed
                settings.complete_first_run_setup()
    
    def check_environment(self):
        """Check if the environment is properly setup."""
        if not process_manager.check_wsl_available():
            QMessageBox.warning(self, "Environment Warning",
                "WSL availability check failed. Verify that WSL is properly installed.")
        
        if not process_manager.check_su_available(self.cwproot):
            result = QMessageBox.warning(self, "Environment Error",
                f"Seismic Unix was not found at {self.cwproot}. Would you like to set a different path?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            
            if result == QMessageBox.Yes:
                self.show_cwproot_dialog()
    
    def on_process_selected(self, process):
        """Handle a process being selected from the process panel."""
        self.current_process = process
        self.current_workflow_index = -1  # Not editing a workflow item
        self.parameters_panel.set_process(process, editing=False)
    
    def on_workflow_process_selected(self, index):
        """Handle a process being selected from the workflow panel."""
        if 0 <= index < len(self.workflow_processes):
            self.current_process = self.workflow_processes[index]
            self.current_workflow_index = index
            self.parameters_panel.set_process(self.current_process, editing=True)
    
    def add_to_workflow(self, process, parameters):
        """Add a process to the workflow."""
        # Create a new process instance
        new_process = Process(process.definition)
       
        
        # Set parameters
        validation_errors = new_process.set_parameters(parameters)
        
        # Check validation errors
        if validation_errors:
            error_msg = "\n".join(validation_errors)
            result = QMessageBox.warning(self, "Parameter Validation Error",
                f"The following errors were found:\n{error_msg}\n\nAdd process anyway?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if result == QMessageBox.No:
                return
        
        # Add to workflow
        self.workflow_processes.append(new_process)
        self.workflow_panel.add_process(new_process)
        self.is_workflow_modified = True
        
        # Log
        self.console.log_info(f"Added process '{new_process.name}' to workflow")
    
    def accept_workflow_edit(self, parameters):
        """Accept edits to a workflow process."""
        if self.current_workflow_index < 0 or self.current_workflow_index >= len(self.workflow_processes):
            return
            
        # Get the current process
        process = self.workflow_processes[self.current_workflow_index]
        
        # Update parameters
        validation_errors = process.set_parameters(parameters)
        
        if validation_errors:
            error_msg = "\n".join(validation_errors)
            result = QMessageBox.warning(self, "Parameter Validation Error",
                f"The following errors were found:\n{error_msg}\n\nSave changes anyway?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if result == QMessageBox.No:
                return
        
        # Update the workflow panel
        self.workflow_panel.update_process(self.current_workflow_index, process)
        self.is_workflow_modified = True
        
        # Log
        self.console.log_info(f"Updated parameters for '{process.name}'")
    
    def remove_from_workflow(self):
        """Remove the current process from the workflow."""
        if self.current_workflow_index < 0 or self.current_workflow_index >= len(self.workflow_processes):
            return
        
        # Get the process name for logging
        process_name = self.workflow_processes[self.current_workflow_index].name
        
        # Remove from data model
        self.workflow_processes.pop(self.current_workflow_index)
        
        # Remove from UI
        self.workflow_panel.remove_process(self.current_workflow_index)
        
        # Clear the parameters panel
        self.parameters_panel.clear()
        
        # Update tracking
        self.current_process = None
        self.current_workflow_index = -1
        self.is_workflow_modified = True
        
        # Log
        self.console.log_info(f"Removed process '{process_name}' from workflow")
    
    def swap_workflow_processes(self, from_index, to_index):
        """Swap two processes in the workflow."""
        if 0 <= from_index < len(self.workflow_processes) and 0 <= to_index < len(self.workflow_processes):
            # Swap in the data model
            self.workflow_processes[from_index], self.workflow_processes[to_index] = \
                self.workflow_processes[to_index], self.workflow_processes[from_index]
            
            # Update current index if we were editing one of these
            if self.current_workflow_index == from_index:
                self.current_workflow_index = to_index
            elif self.current_workflow_index == to_index:
                self.current_workflow_index = from_index
                
            self.is_workflow_modified = True
    
    def run_workflow(self):
        """Execute the current workflow."""
        if not self.workflow_processes:
            QMessageBox.warning(self, "Warning", "No workflow to execute.")
            return
        
        # Get job name
        job_name = self.job_name_input.text().strip() or "Job"
        
        # Use the workflow controller to execute
        self.workflow_controller.execute_workflow(self.workflow_processes, job_name)
    
    def show_visualization(self, job_dir, output_files):
        """Show visualization dialog for seismic data."""
        try:
            # Filter to only include existing files
            valid_files = [(name, path) for name, path in output_files if os.path.exists(path)]
            
            if not valid_files:
                QMessageBox.warning(self, "Visualization", "No valid output files found to visualize.")
                return
            
            # Create and show the visualization dialog
            viz_dialog = VisualizationDialog(job_dir, valid_files, self)
            viz_dialog.show()
        except Exception as e:
            error_msg = f"Error showing visualization: {str(e)}"
            self.console.log_error(error_msg)
            QMessageBox.warning(self, "Visualization Error", error_msg)
    
    def show_su_doc(self, su_command):
        """Show documentation for a Seismic Unix command."""
        if su_command in ["cat"]:
            QMessageBox.information(self, "Info", 
                "No Seismic Unix documentation available for this process.")
            return
            
        try:
            command = f'wsl bash -c "export CWPROOT={self.cwproot} && {process_manager.SU_BIN}/sudoc {su_command}"'
            
            self.console.log_info(f"Getting documentation for {su_command}...")
            result = subprocess.run(command, shell=True, text=True, capture_output=True)
            
            if result.returncode == 0:
                doc_dialog = QDialog(self)
                doc_dialog.setWindowTitle(f"Documentation for {su_command}")
                doc_dialog.setModal(True)
                
                layout = QVBoxLayout(doc_dialog)
                
                text_display = QTextEdit()
                text_display.setReadOnly(True)
                text_display.setPlainText(result.stdout)
                text_display.setMinimumSize(600, 400)
                
                close_btn = QPushButton("Close")
                close_btn.clicked.connect(doc_dialog.close)
                
                layout.addWidget(text_display)
                layout.addWidget(close_btn)
                
                doc_dialog.show()
            else:
                error_msg = f"Could not fetch documentation for {su_command}"
                if "No such file or directory" in result.stderr:
                    error_msg += f". The command may not exist or CWPROOT may be incorrect."
                QMessageBox.warning(self, "Error", error_msg)
                self.console.log_error(error_msg)
                
        except Exception as e:
            error_msg = f"Error executing sudoc: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            self.console.log_error(error_msg)
    
    def setup_menus(self):
        """Set up the application menus."""
        menubar = self.menuBar()
        
        # Config menu
        config_menu = menubar.addMenu('Configuration')
        
        set_cwproot_action = QAction('Set CWPROOT', self)
        set_cwproot_action.triggered.connect(self.show_cwproot_dialog)
        config_menu.addAction(set_cwproot_action)
        
        set_data_dir_action = QAction('Set Data Directory', self)
        set_data_dir_action.triggered.connect(self.show_data_dir_dialog)
        config_menu.addAction(set_data_dir_action)
        
        # Process Definitions menu
        process_defs_menu = menubar.addMenu('Process Definitions')
        
        reload_defs_action = QAction('Reload Definitions', self)
        reload_defs_action.triggered.connect(self.reload_process_definitions)
        process_defs_menu.addAction(reload_defs_action)
        
        reset_defs_action = QAction('Reset to Default Definitions', self)
        reset_defs_action.triggered.connect(self.reset_process_definitions)
        process_defs_menu.addAction(reset_defs_action)
        
        open_def_dir_action = QAction('Open Definitions Directory', self)
        open_def_dir_action.triggered.connect(self.open_definitions_directory)
        process_defs_menu.addAction(open_def_dir_action)

        # Workflows menu
        workflow_menu = menubar.addMenu('Workflows')
        
        save_workflow_action = QAction('Save Workflow...', self)
        save_workflow_action.triggered.connect(self.save_workflow)
        workflow_menu.addAction(save_workflow_action)
        
        load_workflow_action = QAction('Load Workflow...', self)
        load_workflow_action.triggered.connect(self.load_workflow)
        workflow_menu.addAction(load_workflow_action)
        
        # Add SU to SEGY conversion option
        convert_su_action = QAction('Convert SU to SEGY', self)
        convert_su_action.triggered.connect(self.convert_su_to_segy)
        menubar.addAction(convert_su_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')

        help_action = QAction('How to', self)
        help_action.triggered.connect(lambda: HelpDialog(self).show())
        help_menu.addAction(help_action)
        
        about_action = QAction('About', self)
        about_action.triggered.connect(lambda: AboutDialog(self).show())
        help_menu.addAction(about_action)
    
    def save_workflow(self):
        """Save the current workflow to a file."""
        if not self.workflow_processes:
            QMessageBox.warning(self, "Warning", "There is no workflow to save.")
            return
        
        save_dialog = SaveWorkflowDialog(self)
        if save_dialog.exec() != QDialog.Accepted:
            return
        
        workflow_name = save_dialog.name_edit.text().strip()
        if not workflow_name:
            QMessageBox.warning(self, "Warning", "Please provide a name for the workflow.")
            return
            
        description = save_dialog.description_edit.toPlainText().strip()
        success, message = workflow_manager.save_workflow(self.workflow_processes, workflow_name, description)
        
        if success:
            self.console.log_success(f"Workflow '{workflow_name}' saved successfully.")
            QMessageBox.information(self, "Success", message)
            self.is_workflow_modified = False
        else:
            QMessageBox.critical(self, "Error", message)
    
    def load_workflow(self):
        """Load a workflow from a file."""
        workflows = workflow_manager.get_available_workflows()
        if not workflows:
            QMessageBox.information(self, "No Workflows", "No saved workflows found.")
            return
            
        load_dialog = LoadWorkflowDialog(workflows, self)
        if load_dialog.exec() != QDialog.Accepted or not load_dialog.selected_file:
            return
        
        if self.workflow_processes and self.is_workflow_modified:
            reply = QMessageBox.question(
                self, "Replace Workflow", 
                "This will replace your current workflow. Continue?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        result = workflow_manager.load_workflow(load_dialog.selected_file, self.available_processes)
        
        if result["success"]:
            # Update data model
            self.workflow_processes = result["processes"]
            
            # Update UI
            self.workflow_panel.set_workflow(self.workflow_processes)
            
            # Clear current selection
            self.current_process = None
            self.current_workflow_index = -1
            self.parameters_panel.clear()
            
            # Reset modified flag
            self.is_workflow_modified = False
            
            # Log
            msg = f"Workflow '{result['name']}' loaded: {result['loaded_count']} processes loaded"
            if result["skipped_count"] > 0:
                msg += f", {result['skipped_count']} skipped"
                
            self.console.log_success(msg)
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(self, "Error", f"Failed to load workflow: {result['error']}")
    
    def reload_process_definitions(self):
        """Reload process definitions from the data directory."""
        try:
            self.available_processes, self.categorized_processes = process_manager.load_process_definitions()
            self.process_panel.set_processes(self.available_processes, self.categorized_processes)
            count = len(self.available_processes)
            self.console.log_success(f"Reloaded {count} process definitions.")
            QMessageBox.information(self, "Success", f"Successfully reloaded {count} process definitions.")
        except Exception as e:
            error_msg = f"Error reloading process definitions: {str(e)}"
            self.console.log_error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def reset_process_definitions(self):
        """Reset process definitions to default."""
        try:
            # Confirm before resetting
            reply = QMessageBox.question(
                self, "Reset Definitions", 
                "This will reset all process definitions to default, replacing any customizations. Continue?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            
            # Clear directory and copy defaults
            process_def_dir = settings.PROCESS_DEFINITIONS_DIR
            for filename in os.listdir(process_def_dir):
                file_path = os.path.join(process_def_dir, filename)
                if os.path.isfile(file_path) and filename.endswith('.json'):
                    os.remove(file_path)
            
            process_manager.copy_default_definitions()
            
            # Reload definitions
            self.reload_process_definitions()
            self.console.log_success("Reset process definitions to default.")
            
        except Exception as e:
            error_msg = f"Error resetting process definitions: {str(e)}"
            self.console.log_error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def open_definitions_directory(self):
        """Open the process definitions directory in file explorer."""
        try:
            process_def_dir = settings.PROCESS_DEFINITIONS_DIR
            if os.path.exists(process_def_dir):
                os.startfile(process_def_dir)
            else:
                QMessageBox.warning(self, "Directory Not Found", 
                    f"Process definitions directory does not exist: {process_def_dir}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open directory: {str(e)}")
    
    def show_cwproot_dialog(self):
        """Show dialog to set the CWPROOT path."""
        path, ok = QInputDialog.getText(self, 'Set CWPROOT',
            'Enter CWPROOT path:', text=self.cwproot)
        if ok and path:
            self.set_cwproot(path)
    
    def set_cwproot(self, path):
        """Set the CWPROOT path."""
        if path and path != self.cwproot:
            self.cwproot = path
            
            config = settings.load_config()
            config["cwproot"] = path
            settings.save_config(config)
            
            # Log change
            self.console.log_info(f"CWPROOT set to {path} and saved to config.")
            
            if not process_manager.check_su_available(path):
                QMessageBox.warning(self, "Warning", 
                    f"Seismic Unix was not detected at {path}. Commands may fail.")
    
    def show_data_dir_dialog(self):
        """Show dialog to select data directory."""
        current_dir = settings.DATA_DIR
        
        dir_path = QFileDialog.getExistingDirectory(
            self, 'Select Base Directory for InSeis Data',
            current_dir, QFileDialog.ShowDirsOnly
        )
        
        if dir_path:
            try:
                # Update the data directory
                new_data_dir = settings.update_data_dir(dir_path)
                
                # Inform the user
                QMessageBox.information(
                    self, 'Data Directory Changed',
                    f'Data directory changed to:\n{new_data_dir}\n\n'
                    f'The application will use this location for workflows, jobs, and presets.'
                )
                
                self.console.log_info(f"Data directory changed to: {new_data_dir}")
                
            except Exception as e:
                QMessageBox.critical(
                    self, 'Error',
                    f'Failed to change data directory: {str(e)}'
                )
    
    def closeEvent(self, event):
        """Handle application close event."""
        if self.workflow_processes and self.is_workflow_modified:
            reply = QMessageBox.question(
                self, 'Save Changes', 
                'Do you want to save changes to the current workflow before quitting?',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # Try to save workflow
                self.save_workflow()
                # If still modified (user canceled save dialog), ask again
                if self.is_workflow_modified:
                    reply = QMessageBox.question(
                        self, 'Discard Changes',
                        'Changes were not saved. Really quit?',
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        event.ignore()
                        return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        # Accept the close event
        event.accept()
    
    def convert_su_to_segy(self):
        """Convert all SU files in a selected folder to SEGY format."""
        # Prompt for folder selection
        folder_path = QFileDialog.getExistingDirectory(
            self, 'Select Job Folder with SU Files',
            settings.JOBS_DIR, QFileDialog.ShowDirsOnly
        )
        
        if not folder_path:
            return  # User cancelled
        
        # Find all .su files in the folder
        su_files = []
        try:
            for file in os.listdir(folder_path):
                if file.lower().endswith('.su'):
                    su_files.append(os.path.join(folder_path, file))
        except Exception as e:
            error_msg = f"Error reading folder contents: {str(e)}"
            self.console.log_error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            return
        
        # Check if any SU files were found
        if not su_files:
            msg = f"No .su files found in the selected folder."
            self.console.log_warning(msg)
            QMessageBox.warning(self, "No Files Found", msg)
            return
        
        # Process each SU file
        converted_count = 0
        errors = []
        
        self.console.log_info(f"Converting {len(su_files)} SU files to SEGY format...")
        
        for su_file in su_files:
            try:
                file_name = os.path.basename(su_file)
                base_name = os.path.splitext(file_name)[0]
                segy_file = os.path.join(folder_path, f"{base_name}.segy")
                
                command = f'wsl bash -c "export CWPROOT={self.cwproot} && cd \"{PathManager.windows_to_wsl(folder_path)}\" && {process_manager.SU_BIN}/segyhdrs < \"{file_name}\" | {process_manager.SU_BIN}/segywrite tape=\"{base_name}.segy\""'
                
                self.console.log_info(f"Converting {file_name} to {base_name}.segy...")
                result = subprocess.run(command, shell=True, text=True, capture_output=True)
                
                if result.returncode == 0:
                    self.console.log_success(f"Successfully converted {file_name} to SEGY format.")
                    converted_count += 1
                else:
                    err_msg = f"Error converting {file_name}: {result.stderr}"
                    self.console.log_error(err_msg)
                    errors.append(err_msg)
            
            except Exception as e:
                err_msg = f"Exception processing {file_name}: {str(e)}"
                self.console.log_error(err_msg)
                errors.append(err_msg)
        
        # Show results
        if errors:
            QMessageBox.warning(
                self, "Conversion Results", 
                f"Converted {converted_count} of {len(su_files)} files.\n"
                f"{len(errors)} files had errors. See console for details."
            )
        else:
            QMessageBox.information(
                self, "Conversion Complete", 
                f"Successfully converted {converted_count} SU files to SEGY format."
            )