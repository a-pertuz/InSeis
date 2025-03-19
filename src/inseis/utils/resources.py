"""Utilities for accessing application resources."""

import os
import json
import importlib.resources
import importlib.util
from typing import Optional, List, Dict, Union, Any

# Define the resource locations
PACKAGE_NAME = "inseis"
PROCESS_DEF_PACKAGE = f"{PACKAGE_NAME}.data.process_definitions"
THEME_PACKAGE = f"{PACKAGE_NAME}.ui"

def is_packaged() -> bool:
    """Check if running from installed package or source."""
    return importlib.util.find_spec(PACKAGE_NAME) is not None

def get_resource_path(package_name: str, resource_name: str) -> Optional[str]:
    """Get the path to a resource file whether running from source or installed."""
    try:
        # First try to access as a package resource
        if is_packaged():
            with importlib.resources.path(package_name, resource_name) as path:
                return str(path)
        else:
            # Fallback to local source structure
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            package_parts = package_name.split('.')
            local_path = os.path.join(script_dir, *package_parts[1:], resource_name)
            if os.path.exists(local_path):
                return local_path
    except Exception:
        pass
    return None

def get_data(package_name: str, resource_name: str) -> Optional[bytes]:
    """Read data from a resource file."""
    try:
        # Try package resource first
        if is_packaged():
            return importlib.resources.read_binary(package_name, resource_name)
        else:
            # Fallback to file access
            path = get_resource_path(package_name, resource_name)
            if path and os.path.exists(path):
                with open(path, 'rb') as f:
                    return f.read()
    except Exception:
        pass
    return None

def get_text(package_name: str, resource_name: str) -> Optional[str]:
    """Read text from a resource file."""
    data = get_data(package_name, resource_name)
    if data:
        return data.decode('utf-8')
    return None

def get_json(package_name: str, resource_name: str) -> Optional[Dict]:
    """Read JSON from a resource file."""
    text = get_text(package_name, resource_name)
    if text:
        return json.loads(text)
    return None

def list_resources(package_name: str) -> List[str]:
    """List resources in a package."""
    try:
        return list(importlib.resources.contents(package_name))
    except (ModuleNotFoundError, ImportError):
        return []

def copy_resource_to_file(package_name: str, resource_name: str, destination_path: str) -> bool:
    """Copy a resource to a file on disk."""
    try:
        resource = importlib.resources.files(package_name).joinpath(resource_name)
        with importlib.resources.as_file(resource) as path:
            # Read from resource path
            with open(path, 'rb') as src_file:
                data = src_file.read()
            
            # Write to destination
            with open(destination_path, 'wb') as dest_file:
                dest_file.write(data)
            return True
    except Exception as e:
        print(f"Error copying resource {resource_name}: {str(e)}")
        return False

def get_process_definitions() -> List[Dict]:
    """Get all process definition files."""
    definitions = []
    
    # Get list of definition files
    json_files = [f for f in list_resources(PROCESS_DEF_PACKAGE) if f.endswith('.json')]
    
    # Load each JSON file
    for filename in json_files:
        try:
            definition = get_json(PROCESS_DEF_PACKAGE, filename)
            if definition:
                definitions.append(definition)
        except Exception:
            pass
    
    return definitions

def get_theme_stylesheet() -> str:
    """Get the theme stylesheet."""
    return get_text(THEME_PACKAGE, 'theme.qss') or ""
