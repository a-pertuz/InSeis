"""Configuration settings for the InSeis application."""

import os
import json
import subprocess
import appdirs
from ..utils.resources import get_resource_path, PROCESS_DEF_PACKAGE

# Global console reference
_console = None

def set_console(console):
    """Set the global console reference for logging."""
    global _console
    _console = console

def get_console():
    """Get the current console reference."""
    return _console

# Cache for WSL CWPROOT to avoid duplicate detection
_wsl_cwproot_cache = None

def detect_cwproot_from_wsl():
    """Detect CWPROOT environment variable from WSL."""
    global _wsl_cwproot_cache
    
    # Return cached result if available
    if _wsl_cwproot_cache is not None:
        return _wsl_cwproot_cache
    
    console = get_console()
    if console:
        console.log_info("Detecting Seismic Unix path from WSL...")
    
    try:
        # Get the home directory of the WSL user
        command = ["wsl", "bash", "-c", "echo $HOME"]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            if console:
                console.log_error(f"Failed to get WSL home directory: {result.stderr.strip()}")
            return None
            
        home_dir = result.stdout.strip()
        if not home_dir:
            if console:
                console.log_error("Empty home directory returned from WSL")
            return None
            
        # Construct the SeismicUnix path
        su_path = f"{home_dir}/SeismicUnix"
        if console:
            console.log_info(f"Expected Seismic Unix path: {su_path}")
        
        # Verify the path exists
        verify_cmd = ["wsl", "bash", "-c", f"[ -d '{su_path}' ] && echo 'exists' || echo ''"]
        verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
        
        if verify_result.stdout.strip() == "exists":
            if console:
                console.log_success(f"Confirmed SeismicUnix directory exists at: {su_path}")
            _wsl_cwproot_cache = su_path
            return su_path
        else:
            if console:
                console.log_warning(f"SeismicUnix directory not found at: {su_path}")
                
    except Exception as e:
        if console:
            console.log_error(f"Exception while detecting Seismic Unix path: {e}")
        
    if console:
        console.log_warning("Failed to detect Seismic Unix path from WSL")
    
    _wsl_cwproot_cache = None
    return None

# Use standard Windows directories
APP_NAME = "InSeis"

# Base directories
CONFIG_DIR = appdirs.user_config_dir(APP_NAME)
DATA_DIR = appdirs.user_data_dir(APP_NAME)
CACHE_DIR = appdirs.user_cache_dir(APP_NAME)

# Specific paths
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Get WSL CWPROOT if available
WSL_CWPROOT = detect_cwproot_from_wsl() 

# Default settings
DEFAULT_CONFIG = {
    "cwproot": WSL_CWPROOT,
    "first_run_completed": False,
    "data_dir": DATA_DIR
    }

# Default settings
DEFAULT_CONFIG = { 
    "first_run_completed": False,
    "data_dir": DATA_DIR
    }

def ensure_config_directory():
    """Ensure config directory exists"""
    os.makedirs(CONFIG_DIR, exist_ok=True)

def is_first_run():
    """Check if this is the first run of the application"""
    return not os.path.exists(CONFIG_FILE) or not load_config().get("first_run_completed", False)

def load_config():
    """Load configuration from file, creating default if necessary"""
    ensure_config_directory()
    
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        # If config is corrupted, restore defaults
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file"""
    ensure_config_directory()
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def update_data_dir(base_dir):
    """Update the data directory location"""
    global USER_DATA_DIR, PROCESS_DEFINITIONS_DIR, WORKFLOW_DIR, JOBS_DIR, PRESETS_DIR
    
    # Update config
    config = load_config()
    config["data_dir"] = base_dir
    config["first_run_completed"] = True
    save_config(config)
    
    # Re-initialize paths with new base directory
    initialize_paths(config)
    
    return USER_DATA_DIR

def complete_first_run_setup():
    """Mark first run as completed in the configuration"""
    config = load_config()
    config["first_run_completed"] = True
    save_config(config)

def ensure_directories():
    """Ensure all necessary directories exist"""
    directories = [CONFIG_DIR, DATA_DIR, CACHE_DIR, USER_DATA_DIR, 
                  PROCESS_DEFINITIONS_DIR, WORKFLOW_DIR, JOBS_DIR, PRESETS_DIR]
    
    for directory in directories:
        if directory:  # Check if the path is defined
            os.makedirs(directory, exist_ok=True)

def initialize_paths(config=None):
    """Initialize all path variables based on configuration"""
    global USER_DATA_DIR, PROCESS_DEFINITIONS_DIR, WORKFLOW_DIR, JOBS_DIR, PRESETS_DIR, PROCESS_DEF_DIR, CWPROOT, SU_BIN, WSL_CWPROOT
    
    if config is None:
        config = load_config()
    
    # Get the data directory from config or use default
    data_dir = config.get("data_dir", DATA_DIR)
    
    # Set up path structure consistently
    USER_DATA_DIR = os.path.join(data_dir, "user_data")
    PROCESS_DEFINITIONS_DIR = os.path.join(data_dir, "process_definitions")
    WORKFLOW_DIR = os.path.join(USER_DATA_DIR, "workflows")
    JOBS_DIR = os.path.join(USER_DATA_DIR, "jobs")
    PRESETS_DIR = os.path.join(USER_DATA_DIR, "presets")
    
    # Set Seismic Unix path (detect only once)
    if WSL_CWPROOT is None:
        WSL_CWPROOT = detect_cwproot_from_wsl() 
    
    CWPROOT = config.get("cwproot", WSL_CWPROOT)
    SU_BIN = f"{CWPROOT}/bin"
    
    # Process definitions directory - package resource location or user directory
    PROCESS_DEF_DIR = get_resource_path(PROCESS_DEF_PACKAGE, "") or PROCESS_DEFINITIONS_DIR
    
    # Ensure all directories exist
    ensure_directories()

# Initialize paths on module load
initialize_paths()