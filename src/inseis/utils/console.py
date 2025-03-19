"""Enhanced console widget with formatting and color-coding."""

import datetime
import re
import os
from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor

class MessageType:
    """Message type constants for the application."""
    INFO = "info"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    COMMAND = "command"
    OUTPUT = "output"
    
    # Default colors for each message type
    COLORS = {
        INFO: "#3498db",      # Blue
        SUCCESS: "#2ecc71",   # Green
        ERROR: "#e74c3c",     # Red
        WARNING: "#f39c12",   # Orange
        COMMAND: "#7f8c8d",   # Gray
        OUTPUT: "#555555",    # Dark gray
    }
    
    # Icons for each message type
    ICONS = {
        INFO: "ℹ️",
        SUCCESS: "✓",
        ERROR: "❌",
        WARNING: "⚠️",
        COMMAND: "⌨️",
        OUTPUT: "📄",
    }


class ConsoleWidget(QTextEdit):
    """Enhanced text console with color-coded message types and formatting."""
    
    def __init__(self, parent=None):
        """Initialize the console widget."""
        super().__init__(parent)
        self.setReadOnly(True)
        self.setAcceptRichText(True)
    
    def get_timestamp(self):
        """Get current timestamp for log messages."""
        return datetime.datetime.now().strftime("%H:%M:%S")
    
    def simplify_path(self, text):
        """Show only filenames instead of full paths in text."""
        # Use regex to find paths in the text
        path_regex = r'(?:\/mnt\/\w+)?(?:\/[\w\-\.\\]+)+'
        
        def replace_path(match):
            path = match.group(0)
            filename = os.path.basename(path)
            return filename if filename else path
        
        result = text
        if '/' in text or '\\' in text:
            if any(pattern in text for pattern in ['.su', '.segy', '/mnt/']):
                result = re.sub(path_regex, replace_path, text)
                
        return result
    
    def log_message(self, message, msg_type=None):
        """Add a formatted message to the console."""
        # Default to info if no type specified
        if msg_type is None:
            msg_type = MessageType.INFO
            
        timestamp = self.get_timestamp()
        color = MessageType.COLORS.get(msg_type, MessageType.COLORS[MessageType.INFO])
        icon = MessageType.ICONS.get(msg_type, "")
        
        # Clean message by simplifying paths
        if msg_type == MessageType.COMMAND or msg_type == MessageType.INFO:
            message = self.simplify_path(message)
        
        # Apply different formatting based on message type
        if msg_type == MessageType.COMMAND:
            formatted_msg = f'<span style="color:{color};">{icon} <b>[{timestamp}]</b> Command: <span style="font-family:monospace; white-space:pre;">{message}</span></span>'
        elif msg_type == MessageType.OUTPUT:
            formatted_msg = f'<pre style="color:{color}; font-family:monospace;">{message}</pre>'
        else:
            formatted_msg = f'<span style="color:{color};">{icon} <b>[{timestamp}]</b> {message}</span>'
            
        # Append formatted message
        super().append(formatted_msg)
        
        # Auto-scroll to bottom
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def log_info(self, message):
        """Log an informational message."""
        self.log_message(message, MessageType.INFO)
    
    def log_success(self, message):
        """Log a success message."""
        self.log_message(message, MessageType.SUCCESS)
    
    def log_error(self, message):
        """Log an error message."""
        self.log_message(message, MessageType.ERROR)
    
    def log_warning(self, message):
        """Log a warning message."""
        self.log_message(message, MessageType.WARNING)
    
    def log_command(self, command):
        """Log a command with syntax highlighting."""
        self.log_message(command, MessageType.COMMAND)
    
    def log_output(self, output):
        """Log command output."""
        self.log_message(output, MessageType.OUTPUT)
    
    def log_workflow_output(self, text, output_type=None):
        """Simplified workflow output logger that directly maps outputs to message types."""
        if not text:
            return
            
        # Strip any terminal control characters that might be in the output
        text = self._clean_terminal_output(text)
        
        # Look for step patterns and extract step numbers
        step_match = re.search(r'---\s+Step\s+(\d+)/(\d+):\s+Running\s+(.+?)\s*---', text)
        if step_match:
            process_name = step_match.group(3).strip()
            # Log directly as info instead of workflow step
            self.log_info(f"Running {process_name}")
            return
        
        # Check if this is a step completion message
        success_match = re.search(r'Step\s+(\d+)\s+completed\s+successfully', text)
        if success_match:
            self.log_success(text)
            return
            
        # Check if this is a process step without the standard format
        # Example: "SEGYREAD" or other operation names
        if text.isupper() and len(text.strip()) > 2 and " " not in text.strip():
            # This is likely just an operation name - log as info
            self.log_info(text.strip())
            return
            
        # If output type is specified, use it directly
        if output_type:
            self.log_message(text, output_type)
            return
        
        # Simple keyword-based detection for common output types
        lower_text = text.lower()
        if text.lower().startswith("error:") or "failed" in lower_text or "error" in lower_text:
            self.log_error(text)
        elif text.lower().startswith("warning:") or "warning" in lower_text:
            self.log_warning(text)
        elif "success" in lower_text or "completed" in lower_text:
            self.log_success(text)
        elif text.startswith("Command:"):
            self.log_command(text.replace("Command:", "").strip())
        elif "step" in lower_text and ("running" in lower_text or "executing" in lower_text):
            # Extract operation name if possible
            if "running" in lower_text:
                parts = text.split("running", 1)
                if len(parts) > 1:
                    operation = parts[1].strip()
                    self.log_info(f"Running {operation}")
                else:
                    self.log_info(text)
            else:
                self.log_info(text)
        else:
            # Default to information message
            self.log_info(text)
    
    def _clean_terminal_output(self, text):
        """Remove ANSI escape sequences and other terminal control characters."""
        # Pattern to match ANSI escape sequences
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def append(self, text):
        """Override append to handle workflow output directly."""
        # For backward compatibility with APIs that use append directly
        if isinstance(text, str):
            self.log_workflow_output(text)
        else:
            super().append(str(text))
    
    def clear_console(self):
        """Clear the console."""
        super().clear()

