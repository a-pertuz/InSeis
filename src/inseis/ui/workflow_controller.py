"""Controller for workflow execution."""

from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtWidgets import QMessageBox, QApplication
import logging
import traceback
import os

from ..core import workflow_manager

# Set up logger
logger = logging.getLogger(__name__)

class WorkflowOutputHandler:
    """Simple handler for workflow output."""
    def __init__(self, console):
        self.console = console
        
    def append(self, text):
        """Log text to the console."""
        if self.console:
            try:
                self.console.log_workflow_output(text)
            except Exception:
                pass

class WorkflowExecutionWorker(QObject):
    """Worker object that runs workflow execution in a separate thread."""
    
    # Signals
    stepCompleted = Signal(int, int)  # current step, total steps
    outputProduced = Signal(str)  # text output
    workflowFinished = Signal(dict)  # results dictionary
    errorOccurred = Signal(str)  # error message
    
    def __init__(self, processes, job_name):
        """Initialize the worker with workflow processes and job name."""
        super().__init__()
        self.processes = processes
        self.job_name = job_name
        
    def run(self):
        """Execute the workflow in a background thread."""
        try:
            # Create a custom output handler that emits signals
            output_handler = self.ThreadSafeOutputHandler(self)
            
            # Execute the workflow with our signal-based output handler
            results = workflow_manager.execute_workflow(
                self.processes, 
                self.job_name, 
                output_handler
            )
            
            # Emit the finished signal with results
            self.workflowFinished.emit(results)
            
        except Exception as e:
            logger.error(f"Error in workflow thread: {str(e)}")
            logger.error(traceback.format_exc())
            self.errorOccurred.emit(f"Error executing workflow: {str(e)}")
    
    class ThreadSafeOutputHandler:
        """Output handler that emits signals for thread-safe console updates."""
        def __init__(self, worker):
            self.worker = worker
            
        def append(self, text):
            """Emit signal with the text."""
            self.worker.outputProduced.emit(text)

class WorkflowController(QObject):
    """Simple controller for workflow execution."""
    
    # Signal for visualization request
    visualizationRequested = Signal(str, list)  # job_dir, output_files
    
    def __init__(self, parent=None, console=None):
        """Initialize the workflow controller."""
        super().__init__(parent)
        self.console = console
        self.is_processing = False
        self.worker_thread = None
        self.worker = None
    
    def execute_workflow(self, processes, job_name):
        """Execute a workflow with processes in a background thread."""
        # Check if already processing - prevent multiple executions
        if self.is_processing:
            QMessageBox.warning(self.parent(), "Workflow Running", 
                               "A workflow is already running. Please wait for it to complete.")
            return
            
        if not processes:
            QMessageBox.warning(self.parent(), "Warning", "No workflow to execute.")
            return
        
        try:
            # Set processing flag
            self.is_processing = True
            
            # Validate workflow
            validation_errors = workflow_manager.validate_workflow(processes)
            if validation_errors:
                error_msg = "\n".join(validation_errors)
                QMessageBox.critical(self.parent(), "Workflow Validation Error",
                    f"Cannot run workflow due to the following errors:\n\n{error_msg}")
                self.is_processing = False
                return
                
            # Clear the console and log start message
            if self.console:
                self.console.clear_console()
                self.console.log_info("Starting workflow execution...")
            
            # Create worker and thread
            self.worker_thread = QThread()
            self.worker = WorkflowExecutionWorker(processes, job_name)
            self.worker.moveToThread(self.worker_thread)
            
            # Connect signals
            self.worker_thread.started.connect(self.worker.run)
            self.worker.outputProduced.connect(self._handle_output)
            self.worker.workflowFinished.connect(self._handle_workflow_finished)
            self.worker.errorOccurred.connect(self._handle_error)
            
            # Clean up when done
            self.worker.workflowFinished.connect(self.worker_thread.quit)
            self.worker.errorOccurred.connect(self.worker_thread.quit)
            self.worker_thread.finished.connect(self._cleanup_thread)
            
            # Start the thread
            self.worker_thread.start()
            
        except Exception as e:
            error_msg = f"Error setting up workflow execution: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            if self.console:
                self.console.log_error(error_msg)
            QMessageBox.critical(self.parent(), "Error", error_msg)
            self.is_processing = False
    
    def _handle_output(self, text):
        """Handle output from the worker thread."""
        if self.console:
            self.console.log_workflow_output(text)
    
    def _handle_workflow_finished(self, results):
        """Handle workflow completion."""
        try:
            # Process results
            if not results["success"]:
                if results["steps_completed"] == 0:
                    error_message = f"Workflow execution failed: {', '.join(results['errors'])}"
                    if self.console:
                        self.console.log_error(error_message)
                    QMessageBox.critical(self.parent(), "Workflow Error", error_message)
                else:
                    warning_message = f"Workflow completed with {results['total_steps'] - results['steps_completed']} errors.\nResults saved in: {results['job_dir']}"
                    if self.console:
                        self.console.log_warning(warning_message)
                    QMessageBox.warning(self.parent(), "Workflow Warning", warning_message)
                    
                    # Show visualization if there are output files
                    if results["output_files"]:
                        self.show_visualization(results["job_dir"], results["output_files"])
            else:
                success_message = f"Workflow executed successfully!\nResults saved in: {results['job_dir']}"
                if self.console:
                    self.console.log_success(success_message)
                
                # Show visualization if there are output files
                if results["output_files"]:
                    self.show_visualization(results["job_dir"], results["output_files"])
        
        except Exception as e:
            error_msg = f"Error processing workflow results: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            if self.console:
                self.console.log_error(error_msg)
        
        finally:
            # Reset processing flag
            self.is_processing = False
    
    def _handle_error(self, error_message):
        """Handle error from the worker thread."""
        if self.console:
            self.console.log_error(error_message)
        QMessageBox.critical(self.parent(), "Error", error_message)
        self.is_processing = False
    
    def _cleanup_thread(self):
        """Clean up thread and worker when thread is finished."""
        if self.worker_thread:
            self.worker_thread.deleteLater()
            self.worker_thread = None
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        self.is_processing = False
    
    def show_visualization(self, job_dir, output_files):
        """Show visualization of results."""
        if os.path.exists(job_dir):
            # Format output files for visualization
            valid_files = []
            
            for f in output_files:
                # Handle different output formats
                if isinstance(f, tuple):
                    display_name = f[0]  # First element is the display namef[0]
                    filename = f[1]      # Second element is the path to the file
                else:
                    filename = f
                    display_name = os.path.basename(filename)
                
                # Only include files that exist
                if os.path.exists(filename): 
                    valid_files.append((display_name, filename))
            
            if valid_files:
                # Log the files being visualized
                logger.info(f"Visualizing {len(valid_files)} files from {job_dir}")
                
                # Use a timer to delay showing until UI is fully updated
                QTimer.singleShot(100, lambda: self.visualizationRequested.emit(job_dir, valid_files))
