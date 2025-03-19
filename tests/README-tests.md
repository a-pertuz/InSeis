# inseis Tests

This directory contains test and utility scripts for the inseis application.

## Available Test Scripts

### 1. WSL Integration Test (`test_wsl.py`)

This script verifies the WSL (Windows Subsystem for Linux) configuration and checks if Seismic Unix is properly installed.

**Usage:**
```bash
python test_wsl.py
```

### 2. Debug Script (`debug_inseis.py`)

Intended to run the main inseis application from source

**Usage:**
```bash
python debug_inseis.py
```

### 3. Configuration Cleanup (`cleanup.py`)

Utility script to remove all inseis configuration files. Useful during uninstallation or for resetting the application

**Usage:**
```bash
python cleanup.py
```

## Running Tests

To run a specific test, navigate to the tests directory and execute the Python script:

```bash
cd /path/to/inseis/tests
python test_wsl.py
```


