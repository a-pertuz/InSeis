"""Workflow panel for the InSeis application."""

from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, 
                             QListWidget, QPushButton)
from PySide6.QtCore import Qt, Signal

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
        button_width = 24
        self.up_button.setFixedWidth(button_width)
        self.down_button.setFixedWidth(button_width)
        
        # Apply stylesheets for better appearance
        arrow_button_style = """
            QPushButton {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #999;
                border-radius: 4px;
                background-color: #f0f0f0;
                min-height: 24px;
                max-height: 24px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """
        self.up_button.setStyleSheet(arrow_button_style)
        self.down_button.setStyleSheet(arrow_button_style)
        
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