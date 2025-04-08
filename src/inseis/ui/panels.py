"""Process selection panel for the InSeis application."""



from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QPushButton, QLabel, QScrollArea,
                             QWidget, QCheckBox, QFileDialog, QTreeWidget,
                             QTreeWidgetItem, QListWidget)
from PySide6.QtCore import Qt, Signal

class ProcessPanel(QGroupBox):
    """Panel for selecting processes from a categorized tree view."""
    
    # Signals
    processSelected = Signal(object)  # Emits the selected process
    
    def __init__(self, parent=None):
        """Initialize the process panel."""
        super().__init__("Available Processes", parent)
        
        self.available_processes = {}
        self.categorized_processes = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        
        # Add filter/search box
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search processes...")
        self.filter_input.textChanged.connect(self._filter_processes)
        filter_layout.addWidget(self.filter_input)
        layout.addLayout(filter_layout)
        
        # Create process tree
        self.process_tree = QTreeWidget()
        self.process_tree.setHeaderHidden(True)
        layout.addWidget(self.process_tree)
        
        # Connect signal
        self.process_tree.itemClicked.connect(self._handle_process_tree_click)
    
    def set_processes(self, available_processes, categorized_processes):
        """Set the available processes and update the tree."""
        self.available_processes = available_processes
        self.categorized_processes = categorized_processes
        self.populate_process_tree()
    
    def populate_process_tree(self):
        """Populate tree with categorized processes."""
        self.process_tree.clear()
        
        # Sort categories for consistent display
        sorted_categories = sorted(self.categorized_processes.keys())
        
        # Create category items first
        for category in sorted_categories:
            # Skip empty categories
            if not self.categorized_processes[category]:
                continue
                
            display_category = category.title()
            category_item = QTreeWidgetItem(self.process_tree, [display_category])
            category_item.setExpanded(True)  # Expand by default
            
            # Add processes as child items - sorted for consistency
            processes = self.categorized_processes[category]
            for process_name in sorted(processes.keys()):
                process_item = QTreeWidgetItem(category_item, [process_name])
                process_item.setData(0, Qt.UserRole, process_name)
    
    def _handle_process_tree_click(self, item, column):
        """Handle click on process tree item."""
        # Check if this is a process (has a parent) or a category (no parent)
        if item.parent():
            # This is a process - get its name
            process_name = item.data(0, Qt.UserRole)
            if process_name in self.available_processes:
                # Emit the process object
                self.processSelected.emit(self.available_processes[process_name])
    
    def _filter_processes(self, filter_text):
        """Filter processes based on search text."""
        filter_text = filter_text.lower()
        
        # If the filter is empty, show all items
        if not filter_text:
            for i in range(self.process_tree.topLevelItemCount()):
                category_item = self.process_tree.topLevelItem(i)
                category_item.setHidden(False)
                for j in range(category_item.childCount()):
                    category_item.child(j).setHidden(False)
            return
        
        # Otherwise, do filtering
        for i in range(self.process_tree.topLevelItemCount()):
            category_item = self.process_tree.topLevelItem(i)
            category_name = category_item.text(0).lower()
            
            # Check if any child or category matches
            category_matches = filter_text in category_name
            child_matches = False
            visible_children = 0
            
            # Check all children
            for j in range(category_item.childCount()):
                child = category_item.child(j)
                process_name = child.text(0).lower()
                matches = filter_text in process_name
                child.setHidden(not matches)
                if matches:
                    visible_children += 1
                    child_matches = True
            
            # Hide category if it doesn't match and no children match
            category_item.setHidden(not (category_matches or child_matches))
            
            # If category matches, show all children
            if category_matches:
                for j in range(category_item.childCount()):
                    category_item.child(j).setHidden(False)

class WorkflowPanel(QGroupBox):
    """Panel for managing workflow steps."""
    
    # Signals
    runWorkflowRequested = Signal()
    processSelected = Signal(int)  # Emits the index of the selected process in the workflow
    
    def __init__(self, parent=None):
        """Initialize the workflow panel."""
        super().__init__("Current Workflow", parent)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        
        # Create horizontal layout for workflow list and arrows
        workflow_layout = QHBoxLayout()
        
        # Workflow list
        self.workflow_list = QListWidget()
        workflow_layout.addWidget(self.workflow_list)
        
        # Move buttons
        arrows_layout = QVBoxLayout()
        
        # Create stylish arrow buttons with fixed width
        self.up_button = QPushButton("↑")
        self.down_button = QPushButton("↓")
        
        # Set fixed width to make buttons narrower
        button_width = 30
        self.up_button.setFixedWidth(button_width)
        self.down_button.setFixedWidth(button_width)
        
        
        # Add buttons to layout with spacing
        arrows_layout.addSpacing(6)
        arrows_layout.addWidget(self.up_button)
        arrows_layout.addSpacing(2)
        arrows_layout.addWidget(self.down_button)
        arrows_layout.addStretch()
        
        # Add arrows layout to main workflow layout with margins
        workflow_layout.addLayout(arrows_layout)
        workflow_layout.setStretchFactor(self.workflow_list, 1)  # Give list widget stretch priority
        
        layout.addLayout(workflow_layout)
        
        # Run button
        self.run_button = QPushButton("Run Workflow")
        layout.addWidget(self.run_button)
        
        # Connect signals
        self.workflow_list.itemClicked.connect(self._on_item_clicked)
        self.run_button.clicked.connect(self.runWorkflowRequested.emit)
        self.up_button.clicked.connect(self._move_process_up)
        self.down_button.clicked.connect(self._move_process_down)
    
    def set_workflow(self, processes):
        """Update the workflow list with the provided processes."""
        self.workflow_list.clear()
        
        for process in processes:
            self.workflow_list.addItem(process.name)
    
    def add_process(self, process):
        """Add a process to the workflow list."""
        self.workflow_list.addItem(process.name)
    
    def update_process(self, index, process):
        """Update a process in the workflow list."""
        if 0 <= index < self.workflow_list.count():
            self.workflow_list.item(index).setText(process.name)
    
    def remove_process(self, index):
        """Remove a process from the workflow list."""
        if 0 <= index < self.workflow_list.count():
            self.workflow_list.takeItem(index)
    
    def clear_workflow(self):
        """Clear the workflow list."""
        self.workflow_list.clear()
    
    def get_selected_index(self):
        """Get the index of the selected item."""
        return self.workflow_list.currentRow()
    
    def set_selected_index(self, index):
        """Set the selected item by index."""
        if 0 <= index < self.workflow_list.count():
            self.workflow_list.setCurrentRow(index)
    
    def _on_item_clicked(self, item):
        """Handle item click in the workflow list."""
        index = self.workflow_list.row(item)
        self.processSelected.emit(index)
    
    def _move_process_up(self):
        """Move selected process up in the workflow."""
        current_row = self.workflow_list.currentRow()
        if current_row > 0:
            current_text = self.workflow_list.item(current_row).text()
            above_text = self.workflow_list.item(current_row-1).text()
            self.workflow_list.item(current_row).setText(above_text)
            self.workflow_list.item(current_row-1).setText(current_text)
            self.workflow_list.setCurrentRow(current_row-1)
            
            # Signal that item moved so parent can update data model
            self.swapProcesses.emit(current_row, current_row-1)
    
    def _move_process_down(self):
        """Move selected process down in the workflow."""
        current_row = self.workflow_list.currentRow()
        if current_row < self.workflow_list.count() - 1:
            current_text = self.workflow_list.item(current_row).text()
            below_text = self.workflow_list.item(current_row+1).text()
            self.workflow_list.item(current_row).setText(below_text)
            self.workflow_list.item(current_row+1).setText(current_text)
            self.workflow_list.setCurrentRow(current_row+1)
            
            # Signal that item moved so parent can update data model
            self.swapProcesses.emit(current_row, current_row+1)
    
    # Add missing signal
    swapProcesses = Signal(int, int)  # From index, to index

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
