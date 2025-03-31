"""Parameter editing panel for the InSeis application."""

from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QPushButton, QLabel, QScrollArea,
                             QWidget, QCheckBox, QFileDialog)
from PySide6.QtCore import Qt, Signal

class ParametersPanel(QGroupBox):
    """Panel for editing process parameters."""
    
    # Signals
    addToWorkflowRequested = Signal(object, dict)  # Process, parameters
    acceptEditsRequested = Signal(dict)  # Parameters
    removeFromWorkflowRequested = Signal()
    
    def __init__(self, parent=None):
        """Initialize the parameters panel."""
        super().__init__("Process Parameters", parent)
        
        self.current_process = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        
        # Create scroll area for parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create widget to hold parameters
        params_widget = QWidget()
        self.param_form = QFormLayout(params_widget)
        scroll.setWidget(params_widget)
        layout.addWidget(scroll)
        
        # Button container
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add to Workflow")
        self.accept_edit_button = QPushButton("Accept Edits")
        self.remove_button = QPushButton("Remove")
        
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.accept_edit_button)
        buttons_layout.addWidget(self.remove_button)
        layout.addLayout(buttons_layout)
        
        # Hide edit and remove buttons initially
        self.accept_edit_button.hide()
        self.remove_button.hide()
        
        # Connect signals
        self.add_button.clicked.connect(self._on_add_to_workflow)
        self.accept_edit_button.clicked.connect(self._on_accept_edits)
        self.remove_button.clicked.connect(self._on_remove)
    
    def set_process(self, process, editing=False):
        """Set the current process and create parameter form."""
        self.current_process = process
        
        # Show/hide appropriate buttons
        if editing:
            self.accept_edit_button.show()
            self.remove_button.show()
            self.add_button.hide()
        else:
            self.add_button.show()
            self.accept_edit_button.hide()
            self.remove_button.hide()
        
        self._create_parameter_form()
    
    def clear(self):
        """Clear the panel."""
        self.current_process = None
        self.clear_parameter_form()
        self.add_button.hide()
        self.accept_edit_button.hide()
        self.remove_button.hide()
    
    def clear_parameter_form(self):
        """Clear all parameters from form."""
        while self.param_form.rowCount() > 0:
            self.param_form.removeRow(0)
    
    def _create_parameter_form(self):
        """Create form for process parameters."""
        self.clear_parameter_form()
        
        if not self.current_process:
            return
        
        # Add display name as title
        display_name = self.current_process.definition.get('display_name', self.current_process.name)
        title_label = QLabel(display_name)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.param_form.addRow(title_label)
        
        # Add description
        description = self.current_process.definition.get('description', '')
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("font-style: italic;")
            self.param_form.addRow(desc_label)
        
        # Add help button
        help_btn = QPushButton("Show Documentation")
        help_btn.clicked.connect(lambda: self.showDocumentation.emit(self.current_process.su_name))
        self.param_form.addRow(help_btn)
        
        # Add separator
        separator = QLabel("Parameters:")
        separator.setStyleSheet("font-weight: bold;")
        self.param_form.addRow(separator)
        
        # Add parameters
        param_descriptions = self.current_process.definition.get('parameter_descriptions', {})
        
        for param, value in self.current_process.get_parameters().items():
            param_type = self.current_process.parameter_types.get(param, str)
            
            # Create parameter label with required indicator
            if param in self.current_process.required_params:
                label = QLabel(f"{param} *")
                label.setStyleSheet("color: darkred; font-weight: bold;")
            else:
                label = QLabel(param)
            
            # Create parameter field container with input and description
            field_container = QWidget()
            field_layout = QHBoxLayout(field_container)
            field_layout.setContentsMargins(0, 0, 0, 0)
            
            # Create appropriate widget based on type
            if param_type == bool:
                widget = QCheckBox()
                widget.setChecked(value)
            elif param_type == "file":
                file_container = QWidget()
                file_layout = QHBoxLayout(file_container)
                file_layout.setContentsMargins(0, 0, 0, 0)
                line_edit = QLineEdit(str(value))
                browse_btn = QPushButton("Browse")
                browse_btn.clicked.connect(lambda checked, le=line_edit: self._browse_file(le))
                file_layout.addWidget(line_edit)
                file_layout.addWidget(browse_btn)
                widget = file_container
            else:
                widget = QLineEdit(str(value))
            
            # Add widget to the field layout
            field_layout.addWidget(widget)
            
            # Add description if available
            description = param_descriptions.get(param, '')
            if description:
                desc_label = QLabel(description)
                desc_label.setWordWrap(True)
                desc_label.setStyleSheet("color: #555555; font-size: 10px;")
                field_layout.addWidget(desc_label, 1)  # Give description more stretch
                
            self.param_form.addRow(label, field_container)
        
        # Add note about required parameters
        if hasattr(self.current_process, 'required_params') and self.current_process.required_params:
            note = QLabel("* Required parameters")
            note.setStyleSheet("color: darkred; font-style: italic;")
            self.param_form.addRow(note)
    
    def get_parameter_values(self):
        """Extract parameter values from form."""
        params = {}
        
        for i in range(0, self.param_form.rowCount()):
            label_item = self.param_form.itemAt(i, QFormLayout.LabelRole)
            field_item = self.param_form.itemAt(i, QFormLayout.FieldRole)
            
            if not label_item or not field_item:
                continue
                
            label_widget = label_item.widget()
            if not isinstance(label_widget, QLabel):
                continue
                
            # Clean up label text (remove asterisk if present)
            label_text = label_widget.text().split(' *')[0]
            if not label_text:
                continue
                
            # Get widget value
            field_widget = field_item.widget()
            if isinstance(field_widget, QCheckBox):
                params[label_text] = field_widget.isChecked()
            elif isinstance(field_widget, QLineEdit):
                params[label_text] = field_widget.text()
            elif hasattr(field_widget, 'layout'):
                # Handle container widgets
                layout = field_widget.layout()
                if layout and layout.count() > 0:
                    first_widget = layout.itemAt(0).widget()
                    if isinstance(first_widget, QLineEdit):
                        params[label_text] = first_widget.text()
                    elif isinstance(first_widget, QCheckBox):
                        params[label_text] = first_widget.isChecked()
        
        return params
    
    def _on_add_to_workflow(self):
        """Handle add to workflow button click."""
        if self.current_process:
            params = self.get_parameter_values()
            self.addToWorkflowRequested.emit(self.current_process, params)
    
    def _on_accept_edits(self):
        """Handle accept edits button click."""
        params = self.get_parameter_values()
        self.acceptEditsRequested.emit(params)
    
    def _on_remove(self):
        """Handle remove button click."""
        self.removeFromWorkflowRequested.emit()
    
    def _browse_file(self, line_edit):
        """Open file dialog to select a file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            line_edit.setText(file_path)
    
    # Signal for documentation request
    showDocumentation = Signal(str)  # SU command name