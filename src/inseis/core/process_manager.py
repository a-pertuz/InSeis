"""Process management for Seismic Unix commands."""

import os
import re
import json
import subprocess

from ..utils.resources import list_resources, copy_resource_to_file, PROCESS_DEF_PACKAGE
from ..utils.path_utils import PathManager 
from ..config import settings

# Import configuration
CWPROOT = settings.CWPROOT
SU_BIN = settings.SU_BIN
PRESETS_DIR = settings.PRESETS_DIR

def check_wsl_available():
    """Check if WSL is available."""
    try:          
        result = subprocess.run('wsl echo OK', shell=True, text=True, capture_output=True, timeout=10)
        return result.returncode == 0 and "OK" in result.stdout
    except subprocess.TimeoutExpired:
        return True  
    except Exception:
        return False

def check_su_available(cwproot):
    """Check if Seismic Unix is available."""
    try:
        cmd = f'wsl bash -c "[ -d {cwproot}/bin ] && [ -f {cwproot}/bin/suplane ]"'
        result = subprocess.run(cmd, shell=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False

def set_cwproot(path):
    """Update the CWPROOT path."""
    global CWPROOT, SU_BIN
    CWPROOT = path
    SU_BIN = f"{CWPROOT}/bin"
    
    config = settings.load_config()
    config["cwproot"] = path
    settings.save_config(config)
    return check_su_available(path)

class Process:
    """Class representing a seismic process loaded from JSON definition."""
    
    def __init__(self, definition):
        """Initialize from a process definition dictionary."""
        self.definition = definition
        self.name = definition.get("display_name", "Unknown Process")
        self.su_name = definition.get("su_command", "")
        self.su_abbr = definition.get("name", "")
        self.description = definition.get("description", "")
        self.category = definition.get("category", "Uncategorized")
        
        # Initialize parameters
        self.parameters = {}
        self.parameter_types = {}
        self.required_params = set(definition.get("required_params", []))
        self.console = None
        
        # Process all parameters from definition
        if "parameters" in definition and isinstance(definition["parameters"], dict):
            for param_name, default_value in definition["parameters"].items():
                self.parameters[param_name] = default_value
                
                # Set parameter type
                param_type = definition.get("parameter_types", {}).get(param_name, "str")
                if param_type == "boolean" or param_type == "bool":
                    self.parameter_types[param_name] = bool
                    if isinstance(default_value, str):
                        self.parameters[param_name] = default_value.lower() == "true"
                elif param_type == "file":
                    self.parameter_types[param_name] = "file"
                else:
                    self.parameter_types[param_name] = str
    
    def get_parameters(self):
        """Return a copy of the parameters dictionary."""
        return self.parameters.copy()
    
    def validate_parameters(self):
        """Validate all parameters and return list of validation errors."""
        errors = []
        
        # Check for required parameters
        for param_name in self.required_params:
            if not self.parameters.get(param_name):
                errors.append(f"Missing required parameter: {param_name}")
        
        return errors
    
    def set_parameters(self, params):
        """Set parameters with validation."""
        self.parameters.update(params)
        return self.validate_parameters()
    
    def get_su_command(self, infile=None, outfile=None):
        """Returns the SU command with parameters."""
        cmd_parts = []
        
        # Special handling for segyread which doesn't use stdin redirection
        if self.su_name == "segyread":
            cmd_parts.append(self.build_command_parameters())
        else:
            # Add input redirection if provided
            if infile:
                wsl_infile = PathManager.windows_to_wsl(infile)
                cmd_parts.append(f"< {wsl_infile}")
                
            cmd_parts.append(self.build_command_parameters())
        
        # Add output redirection if provided
        if outfile:
            wsl_outfile = PathManager.windows_to_wsl(outfile)
            cmd_parts.append(f"> {wsl_outfile}")
            
        return " ".join(cmd_parts)
    
    def build_command_parameters(self):
        """Build SU command parameters string."""
        # Build command string with non-empty parameters
        params = []
        for key, value in self.parameters.items():
            if value:
                if self.parameter_types.get(key) == "file":
                    wsl_path = PathManager.windows_to_wsl(value)
                    params.append(f"{key}={wsl_path}")
                else:
                    params.append(f"{key}={value}")
        
        return f"{self.su_name} {' '.join(params)}"
    
    def build_command(self, input_file=None, output_file=None):
        """Build the command to execute this process."""
        # Start with basic command
        command = f"{SU_BIN}/{self.su_name}"
        
        # Add parameters
        for param, value in self.parameters.items():
            # Skip empty parameters
            if value == "":
                continue
                
            # Format the parameter
            if isinstance(value, bool):
                if value:  # Only include if True
                    command += f" {param}=1"
            elif self.parameter_types.get(param) == "file":
                # Convert file paths to WSL format
                wsl_path = PathManager.windows_to_wsl(str(value))
                command += f" {param}={wsl_path}"
            else:
                command += f" {param}={value}"
        
        # Add input redirect if provided
        if input_file:
            command += f" < {input_file}"
        
        # Add output redirect if provided
        if output_file:
            command += f" > {output_file}"
        
        return command
    
    def execute(self, infile, outfile, console=None):
        """Execute the SU process."""
        command = self.get_su_command(infile, outfile)
        console_output = console or self.console
        
        # Use full path to SU commands
        if self.su_name != "cat":
            command = command.replace(self.su_name, f"{SU_BIN}/{self.su_name}")
        
        # Execute command with environment setup
        wsl_command = f'wsl bash -c "export CWPROOT={CWPROOT} && {command}"'
        
        # Log command to console if available
        if console_output:
            console_output.append("\n----- Executing Command -----")
            console_output.append(command)
            console_output.append("-----------------------------\n")
        
        try:
            result = subprocess.run(wsl_command, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                error_msg = f"Command failed: {result.stderr}"
                if console_output:
                    console_output.append(f"ERROR: {error_msg}")
                raise Exception(error_msg)
                
            # Log any output
            if console_output and result.stdout:
                console_output.append("Command output:")
                console_output.append(result.stdout)
                
            if console_output:
                console_output.append("Command completed successfully.")
            return True
            
        except Exception as e:
            error_msg = f"Failed to execute command: {str(e)}"
            if console_output:
                console_output.append(f"ERROR: {error_msg}")
            raise Exception(error_msg)

    def get_preset_file_path(self):
        """Get the path to the preset file for this process."""
        return os.path.join(PRESETS_DIR, f"{self.su_name}_presets.json")
    
    def load_presets(self):
        """Load available presets for this process."""
        preset_path = self.get_preset_file_path()
        if os.path.exists(preset_path):
            try:
                with open(preset_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                pass
        return {}
    
    def save_preset(self, preset_name, parameter_values=None):
        """Save current parameters as a preset."""
        if not preset_name:
            return False, "Preset name cannot be empty"
            
        # Use provided parameter values or current parameters
        params_to_save = parameter_values or self.get_parameters()
        
        # Load existing presets
        presets = self.load_presets()
        
        # Add/update preset
        presets[preset_name] = params_to_save
        
        # Save back to file
        preset_path = self.get_preset_file_path()
        try:
            with open(preset_path, 'w') as f:
                json.dump(presets, f, indent=4)
            return True, f"Preset '{preset_name}' saved successfully"
        except Exception as e:
            return False, f"Error saving preset: {str(e)}"
    
    def delete_preset(self, preset_name):
        """Delete a saved preset."""
        presets = self.load_presets()
        if preset_name in presets:
            del presets[preset_name]
            preset_path = self.get_preset_file_path()
            try:
                with open(preset_path, 'w') as f:
                    json.dump(presets, f, indent=4)
                return True, f"Preset '{preset_name}' deleted"
            except Exception as e:
                return False, f"Error deleting preset: {str(e)}"
        return False, f"Preset '{preset_name}' not found"
    
    def apply_preset(self, preset_name):
        """Apply a preset to this process parameters."""
        presets = self.load_presets()
        if preset_name in presets:
            # Create a copy of the current parameters
            current_params = self.get_parameters()
            
            # Update with preset values
            preset_params = presets[preset_name]
            for key, value in preset_params.items():
                if key in self.parameters:
                    # Convert boolean strings to actual booleans if needed
                    if self.parameter_types.get(key) == bool and isinstance(value, str):
                        value = value.lower() == "true"
                    self.parameters[key] = value
            
            return True, "Preset applied successfully"
        return False, f"Preset '{preset_name}' not found"

def load_process_definitions():
    """Load process definitions from the process_definitions directory"""
    available_processes = {}
    categorized_processes = {}
    
    # Ensure directory exists
    settings.ensure_directories()
    
    # First, check if we need to copy default definitions
    if not os.listdir(settings.PROCESS_DEFINITIONS_DIR):
        copy_default_definitions()
    
    # Load definitions from user data directory
    definition_files = [f for f in os.listdir(settings.PROCESS_DEFINITIONS_DIR) if f.endswith('.json')]
    
    for filename in definition_files:
        try:
            file_path = os.path.join(settings.PROCESS_DEFINITIONS_DIR, filename)
            with open(file_path, 'r') as f:
                definition = json.load(f)
            
            # Create process object
            process = Process(definition)
            available_processes[process.name] = process
            
            # Categorize the process
            category = process.category.lower()
            if category not in categorized_processes:
                categorized_processes[category] = {}
            categorized_processes[category][process.name] = process
            
        except Exception as e:
            pass
    
    return available_processes, categorized_processes

def copy_default_definitions():
    """Copy default process definitions from package resources to user data directory"""
    try:
        # Use importlib.resources to list and copy default definitions
        resource_files = list_resources(PROCESS_DEF_PACKAGE)
        
        for resource in resource_files:
            if resource.endswith('.json'):
                destination = os.path.join(settings.PROCESS_DEFINITIONS_DIR, resource)
                copy_resource_to_file(PROCESS_DEF_PACKAGE, resource, destination)
    except Exception:
        pass

def load_config():
    """Load configuration file"""
    return settings.load_config()

def save_config(config):
    """Save configuration file"""
    settings.save_config(config)