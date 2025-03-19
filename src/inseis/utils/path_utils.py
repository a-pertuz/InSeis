"""Path utilities for handling WSL and Windows paths."""

import os
import re

class PathConverter:
    """Utility class for converting between Windows and WSL paths."""
    
    @staticmethod
    def windows_to_wsl(windows_path):
        """Convert Windows path to WSL path format."""
        if not windows_path:
            return windows_path
            
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
            
        return PathConverter.windows_to_wsl(path)
    
    @staticmethod
    def join_wsl_paths(*paths):
        """Join paths and ensure WSL format."""
        # First join normally
        joined = os.path.join(*paths)
        # Then convert to WSL format
        return PathConverter.windows_to_wsl(joined)
