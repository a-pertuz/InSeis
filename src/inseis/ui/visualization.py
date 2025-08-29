"""Visualization components for seismic data."""

import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
                              QLabel, QSlider, QSpinBox, QComboBox, QPushButton, QGroupBox)
from PySide6.QtCore import Qt, Signal, Slot

import seisio
import seisplot


class PercAdjustmentWidget(QWidget):
    """Widget for adjusting percentile clipping of seismic display."""
    
    valueChanged = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set both fixed and maximum height to ensure consistent 50px height
        self.setMaximumHeight(50)
        self.setFixedHeight(50)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Slider for percentile adjustment
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(90)
        self.slider.setMaximum(100)
        self.slider.setValue(100)
        self.slider.setTracking(True)
        
        # Spinbox for precise percentile value
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(90)
        self.spinbox.setMaximum(100)
        self.spinbox.setValue(100)
        
        # Update button
        self.update_btn = QPushButton("Update")
        self.update_btn.setToolTip("Update display with new percentile value")
        
        # Label
        layout.addWidget(QLabel("Percentile:"))
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.spinbox)
        layout.addWidget(self.update_btn)
        
        # Connect signals
        self.slider.valueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)
        self.update_btn.clicked.connect(self._emit_value_changed)
    
    def _emit_value_changed(self):
        """Emit the value changed signal with the current percentile value."""
        self.valueChanged.emit(self.spinbox.value())
    
    def get_perc(self):
        """Get the current percentile value."""
        return self.spinbox.value()

class SeismicDisplayTab(QWidget):
    """Widget for displaying a single seismic dataset."""
    
    def __init__(self, title, su_file_path, parent=None):
        super().__init__(parent)
        self.title = title
        self.su_file_path = su_file_path
        self.perc = 100
        self.haxis_options = ["tracf", "offset", "tracl", "cdp"]
        self.current_haxis = "tracf"
        
        # Setup UI
        self._setup_ui()
        
        # Load and plot seismic data
        self._load_and_plot()
    
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Create figure and canvas for matplotlib
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        
        # Create controls
        controls_layout = QHBoxLayout()
        
        # Percentile adjustment
        self.perc_widget = PercAdjustmentWidget()
        self.perc_widget.valueChanged.connect(self._update_plot)
        controls_layout.addWidget(self.perc_widget)
        
        # Horizontal axis selection
        haxis_layout = QHBoxLayout()
        haxis_layout.addWidget(QLabel("Horizontal Axis:"))
        self.haxis_combo = QComboBox()
        self.haxis_combo.addItems(self.haxis_options)
        self.haxis_combo.currentTextChanged.connect(self._change_haxis)
        haxis_layout.addWidget(self.haxis_combo)
        controls_layout.addLayout(haxis_layout)
        
        # Group controls
        controls_group = QGroupBox("Display Controls")
        controls_group.setLayout(controls_layout)
        controls_group.setMaximumHeight(80)  # Limit the height of control group
        
        # Add canvas and toolbar to layout with stretch factors
        # Canvas gets the highest stretch factor to take maximum space
        layout.addWidget(self.canvas, 10)  # High stretch factor for canvas
        layout.addWidget(NavigationToolbar(self.canvas, self), 0)  # No stretch for toolbar
        layout.addWidget(controls_group, 0)  # No stretch for controls
        
        # Set spacing to minimum
        layout.setSpacing(5)
    
    def _load_and_plot(self):
        """Load seismic data and create the initial plot."""
        try:
            # Load SU file
            sio = seisio.input(self.su_file_path)
            self.dataset = sio.read_all_traces()
            self.seismic_data = self.dataset["data"]
            
            # Update plot
            self._update_plot(self.perc)
            
        except Exception as e:
            print(f"Error loading seismic data from {self.su_file_path}: {str(e)}")
            self.ax.text(0.5, 0.5, f"Error loading seismic data:\n{str(e)}", 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
    
    def _update_plot(self, perc=None):
        """Update the plot with new parameters."""
        if perc is not None:
            self.perc = perc
        
        if hasattr(self, 'seismic_data') and self.seismic_data is not None:
            # Clear previous plot
            self.ax.clear()
            
            # Create new plot
            seisplot.plot(self.seismic_data, 
                         perc=self.perc, 
                         haxis=self.current_haxis, 
                         hlabel=f"{self.current_haxis.title()}", 
                         vlabel="Time (ms)",
                         ax=self.ax)
                         
            # Update the figure
            self.fig.tight_layout()
            self.canvas.draw()
    
    def _change_haxis(self, haxis):
        """Change the horizontal axis for plotting."""
        self.current_haxis = haxis
        self._update_plot()
    
    def cleanup(self):
        """Clean up matplotlib figure to free memory."""
        if hasattr(self, 'fig') and self.fig is not None:
            plt.close(self.fig)
            self.fig = None

class VisualizationDialog(QDialog):
    """Dialog for visualizing seismic data from processing steps."""
    
    def __init__(self, job_dir, su_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seismic Visualization")
        self.setMinimumSize(1000, 600)
        self.setWindowTitle(os.path.basename(job_dir))
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)

        
        self.job_dir = job_dir
        self.su_files = su_files  # List of (name, path) tuples
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create a tab for each SU file
        for name, path in self.su_files:
            tab = SeismicDisplayTab(name, path)
            self.tab_widget.addTab(tab, name)
    
    def closeEvent(self, event):
        """Override close event to clean up matplotlib figures."""
        # Clean up all tabs
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if hasattr(tab, 'cleanup'):
                tab.cleanup()
        
        # Accept the close event
        event.accept()