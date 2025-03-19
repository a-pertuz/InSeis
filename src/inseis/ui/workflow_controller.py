"""Controller for workflow execution."""

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QMessageBox, QPushButton, QApplication

from ..core import workflow_manager
from ..core.process_manager import Process
from .dialogs import WorkflowProgressDialog

class WorkflowOutputHandler:
    def __init__(self, console, progress_dialog):
        self.console = console
        self.progress_dialog = progress_dialog
        
    def append(self, text):
        if self.console:
            self.console.log_workflow_output(text)
        
    def update_progress(self, current, total):
        self.progress_dialog.set_determinate_progress(current, total)

class WorkflowThread(QThread):
    """Thread for executing workflows without blocking the UI."""
    
    finished = Signal(dict)  # Emits results dictionary
    progress = Signal(int, int)  # current step, total steps
    
    def __init__(self, processes, job_name, output_handler):
        super().__init__()
        self.processes = processes
        self.job_name = job_name
        self.output_handler = output_handler
    
    def run(self):
        """Execute the workflow in a separate thread."""
        results = workflow_manager.execute_workflow(self.processes, self.job_name, self.output_handler)
        self.finished.emit(results)

class WorkflowController(QObject):
    """Controller for workflow execution and management."""
    
    def __init__(self, parent=None, console=None):
        """Initialize the workflow controller."""
        super().__init__(parent)
        self.console = console
        self.workflow_thread = None
    
    def execute_workflow(self, processes, job_name):
        """Execute a workflow with processes."""
        if not processes:
            QMessageBox.warning(self.parent(), "Warning", "No workflow to execute.")
            return
        
        try:
            # Validate workflow
            validation_errors = workflow_manager.validate_workflow(processes)
            if validation_errors:
                error_msg = "\n".join(validation_errors)
                QMessageBox.critical(self.parent(), "Workflow Validation Error",
                    f"Cannot run workflow due to the following errors:\n\n{error_msg}")
                return
                
            # Clear the console and log start message
            if self.console:
                self.console.clear_console()
                self.console.log_info("Starting workflow execution...")
            
            # Show progress dialog
            progress_dialog = WorkflowProgressDialog(self.parent(), job_name)
            progress_dialog.show()
            
            # Create output handler
            output_handler = WorkflowOutputHandler(self.console, progress_dialog)
            
            # Create and start the worker thread
            self.workflow_thread = WorkflowThread(processes, job_name, output_handler)
            
            # Connect signals
            self.workflow_thread.finished.connect(
                lambda results: self._workflow_completed(results, progress_dialog))
            self.workflow_thread.progress.connect(output_handler.update_progress)
            
            progress_dialog.rejected.connect(self.cancel_workflow)
            
            # Start thread
            self.workflow_thread.start()
            
        except Exception as e:
            error_msg = f"Error executing workflow: {str(e)}"
            if self.console:
                self.console.log_error(error_msg)
            QMessageBox.critical(self.parent(), "Error", error_msg)
    
    def cancel_workflow(self):
        """Cancel the running workflow."""
        if self.workflow_thread and self.workflow_thread.isRunning():
            # Log cancellation
            if self.console:
                self.console.log_warning("Workflow execution canceled by user")
            
            # Terminate the thread
            self.workflow_thread.terminate()
            self.workflow_thread.wait()
            self.workflow_thread = None
    
    def _workflow_completed(self, results, progress_dialog):
        """Handle workflow completion."""
        # First process results and emit signals
        if not results["success"]:
            if results["steps_completed"] == 0:
                error_message = f"Workflow execution failed: {', '.join(results['errors'])}"
                if self.console:
                    self.console.log_error(error_message)
            else:
                warning_message = f"Workflow completed with {results['total_steps'] - results['steps_completed']} errors.\nPartial results saved in: {results['job_dir']}"
                if self.console:
                    self.console.log_warning(warning_message)
                # Emit signal for visualization if there are output files
                if results["output_files"]:
                    self.visualizationRequested.emit(results["job_dir"], results["output_files"])
        else:
            success_message = f"Workflow executed successfully!\nResults saved in: {results['job_dir']}"
            if self.console:
                self.console.log_info(success_message)
            # Emit signal for visualization if there are output files
            if results["output_files"]:
                self.visualizationRequested.emit(results["job_dir"], results["output_files"])
                
        # Disconnect the progress dialog's rejected signal to prevent issues when closing
        progress_dialog.rejected.disconnect(self.cancel_workflow)
        
        # Make sure the thread is properly terminated
        self.workflow_thread = None
        
        # Finally close the progress dialog
        progress_dialog.close()
    
    # Signal for visualization request
    visualizationRequested = Signal(str, list)  # job_dir, output_files
