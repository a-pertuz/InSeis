"""Process selection panel for the InSeis application."""

from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTreeWidget, QTreeWidgetItem)
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