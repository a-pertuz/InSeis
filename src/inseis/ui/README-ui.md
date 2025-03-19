# InSeis UI Module

This directory contains the user interface components for the InSeis application, a GUI tool for using Seismic Unix through Windows Subsystem for Linux (WSL).

## File Structure Overview

The UI module is organized into several components that work together to provide the application's interface:

### Core UI Files

- `main_window.py` - Main application window that orchestrates all UI components
- `workflow_controller.py` - Controller for workflow execution logic
- `dialogs.py` - Dialog windows for various application functions
- `help_dialogs.py` - Specialized dialogs for help, about, and first-run experience

### UI Panels

- `process_panel.py` - Panel for selecting processes from available definitions
- `workflow_panel.py` - Panel for managing the current workflow steps
- `parameters_panel.py` - Panel for editing process parameters

### Visualization

- `visualization.py` - Components for visualizing seismic data results


## File Descriptions

### main_window.py

The main application window that ties together all UI components. It:
- Initializes the main interface
- Manages the three main panels (process, workflow, parameters)
- Handles menu actions and configuration
- Coordinates interactions between panels
- Manages workflow saving/loading

### workflow_controller.py

Controls workflow execution in a non-blocking way:
- Executes workflows in a separate thread
- Communicates with the progress dialog
- Handles success/error states
- Triggers visualization when complete

### dialogs.py

Contains dialog windows used throughout the application:
- `SaveWorkflowDialog` - For saving a workflow with name and description
- `LoadWorkflowDialog` - For loading a saved workflow
- `WorkflowProgressDialog` - Shows progress during workflow execution

### help_dialogs.py

Specialized dialog windows for help and information:
- `FirstRunDialog` - Shown on first run to configure application settings
- `AboutDialog` - Displays information about the application
- `HelpDialog` - Provides help documentation

### process_panel.py

Panel for selecting processes:
- Displays available processes in a tree view
- Groups processes by category
- Provides filtering/search
- Emits signals when a process is selected

### workflow_panel.py

Panel for managing the current workflow:
- Displays the ordered list of processes in the workflow
- Provides up/down buttons to reorder processes
- Includes a Run button to execute the workflow
- Emits signals for process selection and workflow execution

### parameters_panel.py

Panel for editing process parameters:
- Displays editable form fields for process parameters
- Handles parameter validation
- Provides buttons for adding to workflow or accepting edits
- Manages required vs optional parameters

### visualization.py

Components for visualizing seismic data:
- `SeismicDisplayTab` - Tab for displaying a single seismic dataset
- `VisualizationDialog` - Dialog with tabs for multiple seismic outputs
- Controls for adjusting display parameters (percentile, axes)

## Data Flow

1. User selects a process from `process_panel`
2. `parameters_panel` shows editable parameters for the selected process
3. User adds process to workflow using the "Add to Workflow" button
4. `workflow_panel` displays the updated workflow list
5. User can select processes in the workflow to edit parameters
6. When "Run Workflow" is clicked, `workflow_controller` executes the workflow
7. `WorkflowProgressDialog` shows progress during execution
8. Upon completion, results are shown in the `visualization` dialog if applicable

## Signal Connections

The UI components use Qt signals/slots for communication:
- `processSelected` signals connect process selection between panels
- `addToWorkflowRequested` signal adds processes to the workflow
- `runWorkflowRequested` signal triggers workflow execution
- `visualizationRequested` signal shows visualization dialog

## Design Pattern

The UI follows a Model-View-Controller pattern:
- Models: Core process and workflow data structures
- Views: UI panels and dialogs
- Controllers: Main window and workflow controller

This separation allows for clear responsibility boundaries and easier maintenance.