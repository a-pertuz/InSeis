# InSeis

InSeis is a graphical user interface design in Python for creating and running Seismic Unix workflows on Windows through the Windows Subsystem for Linux (WSL).

[![DOI](https://zenodo.org/badge/DOI/zenodo.15053545.svg)](https://doi.org/10.5281/zenodo.15053545)
[![PyPI](https://img.shields.io/pypi/v/segyrecover)](https://pypi.org/project/inseis/)
[![Last Commit](https://img.shields.io/github/last-commit/a-pertuz/inseis)](https://github.com/a-pertuz/inseis/commits/main)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0.en.html)
[![Python Version](https://img.shields.io/badge/Python-3.12+-yellow)](https://www.python.org/downloads/)

## Features

- **User-Friendly Interface**: Easily create, edit, and run Seismic Unix workflows
- **Workflow Management**: Save, load, and manage your processing workflows
- **Visualization**: View seismic data directly in the application
- **Process Library**: Extensive library of pre-configured Seismic Unix processes
- **Windows Integration**: Use Seismic Unix on Windows through WSL

## Citation

If you use this software in your research, please cite it as:

```
Pertuz, A. (2025). InSeis: Simplifying Seismic Unix workflows on Windows using WSL and Python. Zenodo. https://doi.org/10.5281/zenodo.15053545
```

Find this software in the Zenodo Archive: [https://doi.org/10.5281/zenodo.15053545](https://doi.org/10.5281/zenodo.15053545)


## Requirements

- Windows 10/11 with WSL installed
- Seismic Unix installed in WSL
- Python 3.12 or higher

## Installation

### 1. Install WSL
 
- Open Command Prompt (search for "cmd" in Windows search)
- Type the following command and press Enter:

```
wsl --install
```

### 2. Install Seismic Unix

- Run the [Seismic Unix Installation script](https://gist.github.com/a-pertuz/2b341bc8af2a37cde820d829f2789d99). Originally developed by the BotoSeis team. Tested for Ubuntu 22.04 LTS

- Open WSL, type the following command and press Enter:

```bash
bash -c "$(wget -qO- https://gist.githubusercontent.com/a-pertuz/2b341bc8af2a37cde820d829f2789d99/raw/install_seismic_unix.sh)"
```
This script automates the installation and configuration of Seismic Unix release 44R28. [Official guide](https://wiki.seismic-unix.org/sudoc:su_installation).

### 3. Install InSeis

 - Open Command Prompt (cmd) and type one of the following options:

```bash
pip install inseis
```

```bash
pip install git+https://github.com/a-pertuz/inseis.git
```

## How to Use

1. **Launch InSeis**: Open the application from your Start menu or run `inseis` in Command Prompt
2. **Create a new workflow**: The main interface displays available processes on the left and your current workflow on the right
3. **Load data**: Add a data loading process to your workflow (e.g., "Load SU File")
4. **Add processing steps**: Select and configure processing operations from the available processes list
5. **Run your workflow**: Click "Run Workflow" to execute all steps in sequence
6. **View results**: Results will be displayed automatically upon completion

> **Important note**: Seismic Unix uses **SU** files as its native format. If you need **SEGY** files for external applications, use the **"Convert SU to SEGY"** utility in the menu bar after processing.

### Saving and Loading Workflows

To save your workflow:
1. Click "Workflows" > "Save Workflow..."
2. Enter a name and description

To load a workflow:
1. Click "Workflows" > "Load Workflow..."
2. Select from your saved workflows

### Troubleshooting

**WSL Connection Issues**
- Ensure WSL is installed and running
- Try restarting the WSL service: `wsl --shutdown` and then restart

**Seismic Unix Not Found**
- Check your CWPROOT path in the Configuration menu
- Verify Seismic Unix is properly installed in WSL

**Input/Output File Issues**
- Check file permissions
- Ensure paths don't contain special characters
- Use forward slashes in file paths

## License

InSeis is licensed under the **GNU General Public License v3 (GPLv3)**. This means:  

- You are free to **use, modify, and distribute** the software.  
- Any modified or distributed versions **must remain open-source** under the same GPLv3 license.  
- There is **no warranty**, and the software is provided **"as-is"**.  

For full details, see the [GPLv3 License](https://www.gnu.org/licenses/gpl-3.0.html).
