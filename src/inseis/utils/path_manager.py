"""Unified path handling for Windows and WSL paths."""

import os
import re

class PathManager:
    """Handles path conversions and command wrapping for WSL compatibility."""
    
    @staticmethod
    def windows_to_wsl(windows_path):
        """Convert a Windows path to WSL format."""
        if not windows_path:
            return ""
            
        # First replace backslashes with forward slashes
        unix_path = windows_path.replace('\\', '/')
        
        # If the path starts with a drive letter, convert to WSL format
        if re.match(r'^[A-Za-z]:', unix_path):
            drive_letter = unix_path[0].lower()
            unix_path = f'/mnt/{drive_letter}/{unix_path[3:]}'
            
        # Escape spaces
        unix_path = unix_path.replace(' ', '\\ ')
        
        return unix_path
    
    @staticmethod
    def ensure_wsl_path(path):
        """Ensure a path is in WSL format."""
        if not path:
            return path
            
        # If already in WSL format, return as is
        if path.startswith('/'):
            return path
            
        return PathManager.windows_to_wsl(path)
    
    @staticmethod
    def join_wsl_paths(*paths):
        """Join paths and ensure WSL format."""
        # First join normally
        joined = os.path.join(*paths)
        # Then convert to WSL format
        return PathManager.windows_to_wsl(joined)
    
    @staticmethod
    def to_wsl(windows_path):
        """Convert a Windows path to WSL format (alias for windows_to_wsl)."""
        return PathManager.windows_to_wsl(windows_path)
    
    @staticmethod
    def wrap_command(command, input_file=None, output_file=None):
        """
        Wrap a command with appropriate input/output redirections.
        Automatically converts Windows paths to WSL paths.
        """
        wrapped_cmd = command
        
        if input_file:
            wsl_input = PathManager.to_wsl(input_file)
            wrapped_cmd = f"{wrapped_cmd} < {wsl_input}"
        
        if output_file:
            wsl_output = PathManager.to_wsl(output_file)
            wrapped_cmd = f"{wrapped_cmd} > {wsl_output}"
        
        return wrapped_cmd
    
    @staticmethod
    def prepare_wsl_command(command):
        """Prepare a command to be executed in WSL."""
        return f'wsl bash -c "{command}"'
