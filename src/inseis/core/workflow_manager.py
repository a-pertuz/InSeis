"""Workflow management for Seismic Unix processes."""

import os
import json
import subprocess
import threading
import select
import io
from datetime import datetime

from ..config import settings
from .process_manager import Process
from ..utils.path_utils import PathManager 

# Import paths from settings
WORKFLOW_DIR = settings.WORKFLOW_DIR
JOBS_DIR = settings.JOBS_DIR

def convert_to_wsl_path(windows_path):
    """Convert Windows path to WSL path format."""
    return PathManager.windows_to_wsl(windows_path)

def validate_workflow(workflow_processes):
    """Validate the entire workflow before execution."""
    errors = []
    
    if not workflow_processes:
        errors.append("Workflow is empty")
        return errors
        
    first_process = workflow_processes[0]
    
    for i, process in enumerate(workflow_processes):
        process_errors = process.validate_parameters()
        if process_errors:
            for err in process_errors:
                errors.append(f"Process {i+1} ({process.name}): {err}")
    
    if isinstance(first_process, Process):
        if first_process.su_name == "cat":
            input_path = first_process.parameters.get('input_file', '')
            if not input_path:
                errors.append("Input file not specified for Load SU process")
            elif not os.path.exists(input_path):
                errors.append(f"Input file not found: {input_path}")
        elif first_process.su_name == "segyread":
            input_path = first_process.parameters.get('tape', '')
            if not input_path:
                errors.append("SEGY file not specified for SEGY Read process") 
            elif not os.path.exists(input_path):
                errors.append(f"SEGY file not found: {input_path}")
    
    return errors

def extract_input_base_name(process):
    """Extract base name from the input file of the first process."""
    if process.su_name == "segyread":
        input_file = process.parameters.get('tape', '')
    elif process.su_name == "cat":
        input_file = process.parameters.get('input_file', '')
    else:
        return None
        
    if input_file:
        # Extract the base name without extension
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        return base_name
    return None

def execute_workflow(processes, job_name, console=None):
    """
    Execute a workflow of processes.
    """
    # Create job directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_dir = os.path.join(JOBS_DIR, f"{job_name}_{timestamp}")
    os.makedirs(job_dir, exist_ok=True)
    
    # Create log file at the beginning
    history_file = os.path.join(job_dir, "workflow_history.txt")
    with open(history_file, 'w') as f:
        f.write(f"Workflow: {job_name}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Steps: {len(processes)}\n\n")
        
        # Write a detailed summary of the workflow that will be executed
        f.write(f"{'='*40}\n")
        f.write("WORKFLOW EXECUTION PLAN\n")
        f.write(f"{'='*40}\n\n")
        
        for i, process in enumerate(processes):
            step_num = i + 1
            process_name = process.name
            process_type = process.su_name
            
            f.write(f"Step {step_num}: {process_name} ({process_type})\n")
            
            # Write the parameters for this process
            params = process.get_parameters()
            if params:
                f.write("  Parameters:\n")
                for param_name, param_value in params.items():
                    if param_value:  # Only show non-empty parameters
                        f.write(f"    - {param_name}: {param_value}\n")
            else:
                f.write("  No parameters set\n")
            
            # Add a separator between steps
            if i < len(processes) - 1:
                f.write("\n" + "-"*30 + "\n\n")
        
        # End of workflow plan
        f.write(f"\n{'='*40}\n")
        f.write("EXECUTION LOG\n")
        f.write(f"{'='*40}\n\n")
    
    # Results dictionary
    results = {
        "success": False,
        "job_dir": job_dir,
        "total_steps": len(processes),
        "steps_completed": 0,
        "errors": [],
        "commands": [],
        "outputs": [],  # Store command outputs for history
        "output_files": [],  # Store output file paths for visualization
        "history_file": history_file  # Store the history file path
    }
    
    # Get base file name for inputs/outputs - first try to get from the first process's input file
    if processes:
        base_file_name = extract_input_base_name(processes[0])
        if not base_file_name:
            base_file_name = job_name.replace(" ", "_")
    else:
        base_file_name = job_name.replace(" ", "_")
    
    if console:
        console.append(f"Created job directory: {job_dir}")
        console.append(f"Using base file name: {base_file_name}")
    
    # Log this information to the history file
    _append_to_history(history_file, f"Created job directory: {job_dir}\n")
    _append_to_history(history_file, f"Using base file name: {base_file_name}\n\n")
    
    # Track previous output for chaining and process chain naming
    previous_output = None
    process_chain = []
    
    try:
        # Process each step
        for i, process in enumerate(processes):
            step_num = i + 1
            step_header = f"Step {step_num}/{len(processes)}: Running {process.name}"
            
            if console:
                # Format step message with proper numbering
                console.append(step_header)
            
            # Log step beginning to history file
            _append_to_history(history_file, f"\n{'='*40}\n{step_header}\n{'='*40}\n")
            
            # Get process name without "su" prefix for the file naming
            process_name = process.su_name
            if process_name.startswith("su"):
                process_name = process_name[2:]
            
            # Add this process to the chain
            process_chain.append(process_name)
            
            # Output file with descriptive name stored directly in job folder
            output_filename = f"{base_file_name}_{'_'.join(process_chain)}.su"
            output_file = os.path.join(job_dir, output_filename)
            
            # Save output file information for visualization
            display_name = f"Step {step_num}: {process.name}"
            results["output_files"].append((display_name, output_file))
            
            # Convert to WSL path
            wsl_output = PathManager.windows_to_wsl(output_file)
            
            # Prepare command
            try:
                command = process.build_command(previous_output, wsl_output)
                
                # Log command to both console and history file
                if console:
                    console.append(f"Command: {command}")
                _append_to_history(history_file, f"Command: {command}\n\n")
                
                # Store command for history
                results["commands"].append(command)
                
                # Execute command with output handling - using Popen for real-time output
                if console:
                    console.append("Executing command...")
                
                # Start the process
                process_obj = subprocess.Popen(
                    f'wsl bash -c "{command}"',
                    shell=True,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Set up variables to collect output
                stdout_data = []
                stderr_data = []
                
                # Function to efficiently read from pipe and handle output in chunks
                def read_output(pipe, data_list, prefix):
                    """Read data from pipe and collect it in chunks for efficient processing."""
                    buffer = io.StringIO()
                    
                    while True:
                        line = pipe.readline()
                        if not line:
                            break
                            
                        # Add to our buffer
                        buffer.write(line)
                        data_list.append(line)
                        
                        # If we've accumulated enough lines or the line is very long, send to console
                        if buffer.tell() > 1024:  # Send in ~1KB chunks
                            content = buffer.getvalue()
                            if console:
                                console.append(f"{prefix}: {content.strip()}")
                            buffer = io.StringIO()  # Reset buffer
                    
                    # Get any remaining content
                    remaining = buffer.getvalue()
                    if remaining and console:
                        console.append(f"{prefix}: {remaining.strip()}")
                
                # Create and start output reader threads
                stdout_thread = threading.Thread(
                    target=read_output, 
                    args=(process_obj.stdout, stdout_data, "OUT")
                )
                stderr_thread = threading.Thread(
                    target=read_output, 
                    args=(process_obj.stderr, stderr_data, "ERR")
                )
                
                stdout_thread.daemon = True
                stderr_thread.daemon = True
                stdout_thread.start()
                stderr_thread.start()
                
                # Wait for process to complete
                return_code = process_obj.wait()
                
                # Wait for output threads to finish
                stdout_thread.join()
                stderr_thread.join()
                
                # Combine the output data
                stdout_text = ''.join(stdout_data)
                stderr_text = ''.join(stderr_data)
                
                # Store the command output for the history file
                output = {
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "return_code": return_code
                }
                results["outputs"].append(output)
                
                # Log command output to history file
                _append_to_history(history_file, "Command Output:\n")
                if stdout_text:
                    _append_to_history(history_file, "--- STDOUT ---\n")
                    _append_to_history(history_file, stdout_text)
                    _append_to_history(history_file, "\n\n")
                
                if stderr_text:
                    _append_to_history(history_file, "--- STDERR ---\n")
                    _append_to_history(history_file, stderr_text)
                    _append_to_history(history_file, "\n\n")
                
                _append_to_history(history_file, f"Return Code: {return_code}\n\n")
                
                if return_code != 0:
                    error_msg = f"Command failed: {stderr_text or 'Unknown error'}"
                    if console:
                        console.append(f"ERROR: {error_msg}")
                    results["errors"].append(error_msg)
                    _append_to_history(history_file, f"ERROR: {error_msg}\n")
                    _append_to_history(history_file, "Workflow execution aborted due to error.\n")
                    break
                
                # Update previous output for chaining
                previous_output = wsl_output
                results["steps_completed"] += 1
                
                if console:
                    console.append(f"Step {step_num} completed successfully.")
                _append_to_history(history_file, f"Step {step_num} completed successfully.\n")
                
            except Exception as e:
                error_msg = str(e)
                if console:
                    console.append(f"ERROR: {error_msg}")
                results["errors"].append(error_msg)
                _append_to_history(history_file, f"ERROR: {error_msg}\n")
                _append_to_history(history_file, "Workflow execution aborted due to exception.\n")
                break
            
        # If we have remaining steps, mark them as skipped
        for i in range(results["steps_completed"], len(processes)):
            step_num = i + 1
            skip_msg = f"Skipping step {step_num}: {processes[i].name} (previous step failed)"
            if console:
                console.append(skip_msg)
            _append_to_history(history_file, f"{skip_msg}\n")
        
        # Write workflow summary
        _append_to_history(history_file, f"\n{'='*40}\nWORKFLOW SUMMARY\n{'='*40}\n")
        _append_to_history(history_file, f"Steps completed: {results['steps_completed']}/{results['total_steps']}\n")
        _append_to_history(history_file, f"Success: {len(results['errors']) == 0}\n")
        if results["errors"]:
            _append_to_history(history_file, "Errors:\n")
            for err in results["errors"]:
                _append_to_history(history_file, f"- {err}\n")
        
        # Set success flag
        results["success"] = len(results["errors"]) == 0
        
        if console:
            console.append(f"Workflow execution completed: {results['steps_completed']}/{results['total_steps']} steps successful")
            console.append(f"Results saved in: {job_dir}")
            
        # Explicitly ensure all resources are released
        import gc
        gc.collect()
            
        return results
    
    except Exception as e:
        # Catch any unexpected exceptions during workflow execution
        error_msg = f"Unexpected error in workflow execution: {str(e)}"
        import traceback
        error_details = traceback.format_exc()
        
        # Log to history file
        _append_to_history(history_file, f"\n{'='*40}\nUNEXPECTED ERROR\n{'='*40}\n")
        _append_to_history(history_file, f"{error_msg}\n\n")
        _append_to_history(history_file, f"Error details:\n{error_details}\n")
        
        # Log to console
        if console:
            console.append(f"ERROR: {error_msg}")
        
        # Add to results
        if "errors" in results:
            results["errors"].append(error_msg)
        
        # Set success flag
        results["success"] = False
        
        return results

def _append_to_history(history_file, text):
    """
    Append text to history file with error handling.
    This ensures logs are written even if the program crashes later.
    """
    try:
        with open(history_file, 'a') as f:
            f.write(text)
    except Exception as e:
        print(f"Error writing to history file: {e}")

def save_workflow(workflow_processes, name, description=""):
    """Save a workflow to file."""
    if not workflow_processes:
        return False, "No workflow to save"
    
    if not name.strip():
        return False, "Workflow name cannot be empty"
    
    workflow_data = {
        "name": name,
        "description": description,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "processes": []
    }
    
    for process in workflow_processes:
        process_data = {
            "type": process.__class__.__name__,
            "name": process.name,
            "parameters": process.get_parameters()
        }
        workflow_data["processes"].append(process_data)
    
    safe_name = "".join(c if c.isalnum() else "_" for c in name)
    filename = os.path.join(WORKFLOW_DIR, f"{safe_name}.json")
    
    try:
        with open(filename, 'w') as f:
            json.dump(workflow_data, f, indent=2)
        return True, f"Workflow '{name}' saved successfully"
    except Exception as e:
        return False, f"Failed to save workflow: {str(e)}"

def get_available_workflows():
    """Get list of available workflows."""
    workflows = []
    
    for filename in os.listdir(WORKFLOW_DIR):
        if filename.endswith('.json'):
            try:
                file_path = os.path.join(WORKFLOW_DIR, filename)
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                workflows.append({
                    'name': data.get('name', os.path.splitext(filename)[0]),
                    'description': data.get('description', ''),
                    'created': data.get('created', ''),
                    'process_count': len(data.get('processes', [])),
                    'file_path': file_path
                })
            except:
                continue
                
    return sorted(workflows, key=lambda w: w['name'])

def load_workflow(file_path, available_processes):
    """Load workflow from file."""
    workflow_processes = []
    
    try:
        with open(file_path, 'r') as f:
            workflow_data = json.load(f)
        
        loaded_count = 0
        skipped_count = 0
        
        for proc_data in workflow_data.get('processes', []):
            process_type = proc_data.get('type')
            if not process_type:
                skipped_count += 1
                continue
            
            found = False
            
            # Handle the available_processes being a tuple (flat_processes, categorized_processes)
            processes_to_check = available_processes
            if isinstance(available_processes, tuple) and len(available_processes) > 0:
                processes_to_check = available_processes[0]
            
            for display_name, process in processes_to_check.items():
                if isinstance(process, Process) and process_type == "Process":
                    if display_name == proc_data.get('name'):
                        new_process = Process(process.definition)
                        new_process.set_parameters(proc_data.get('parameters', {}))
                        workflow_processes.append(new_process)
                        found = True
                        loaded_count += 1
                        break
            
            if not found:
                skipped_count += 1
        
        result = {
            "success": True,
            "name": workflow_data.get('name', ''),
            "loaded_count": loaded_count,
            "skipped_count": skipped_count,
            "processes": workflow_processes
        }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processes": []
        }

def delete_workflow(file_path):
    """Delete a workflow file."""
    try:
        os.remove(file_path)
        return True, "Workflow deleted successfully"
    except Exception as e:
        return False, f"Could not delete workflow: {str(e)}"