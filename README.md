# InSeis

[![DOI](https://zenodo.org/badge/DOI/zenodo.15053545.svg)](https://doi.org/10.5281/zenodo.15053545)
[![PyPI](https://img.shields.io/pypi/v/segyrecover)](https://pypi.org/project/inseis/)
[![Last Commit](https://img.shields.io/github/last-commit/a-pertuz/inseis)](https://github.com/a-pertuz/inseis/commits/main)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0.en.html)
[![Python Version](https://img.shields.io/badge/Python-3.12+-yellow)](https://www.python.org/downloads/)

A GUI-based application designed in Python for creating and running Seismic Unix workflows on Windows through the Windows Subsystem for Linux (WSL). InSeis bridges the gap between powerful Linux-based seismic processing and the Windows environment.

InSeis is part of a collection of open source tools to digitize and enhance vintage seismic sections. See https://a-pertuz.github.io/REVSEIS/ for more information.

<details open>
<summary><h2>📖 Table of Contents</h2></summary>

- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Complete Tutorial](#complete-tutorial)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Citation](#citation)
- [License](#license)

</details>

<details open>
<summary><h2>✨ Features</h2></summary>

- **User-Friendly Interface**: Easily create, edit, and run Seismic Unix workflows through an intuitive GUI
- **Workflow Management**: Save, load, and manage your processing workflows with full parameter preservation
- **Process Library**: Extensive library of pre-configured Seismic Unix processes organized by category
- **Visualization**: View seismic data directly in the application with built-in plotting capabilities
- **Windows Integration**: Use Seismic Unix on Windows through WSL without command-line complexity
- **Format Conversion**: Convert between SU and SEG-Y formats seamlessly
- **Real-time Monitoring**: Track workflow execution with detailed logging and progress indicators

</details>

<details>
<summary><h2>💻 System Requirements</h2></summary>

- **Operating System**: Windows 10/11 with WSL installed
- **Memory**: At least 8GB RAM recommended
- **Python**: 3.12 or higher
- **Dependencies**: Seismic Unix installed in WSL
- **Disk Space**: Sufficient space for seismic data processing and temporary files

</details>

<details>
<summary><h2>⚙️ Installation</h2></summary>

InSeis requires Windows Subsystem for Linux (WSL) to run. This allows you to use Linux tools directly on Windows.

### Install WSL

1. Open Command Prompt **as Administrator** (right-click, select "Run as administrator")
2. Run the following command: `wsl --install`
3. Wait for the installation to complete
4. Restart your computer when prompted
5. After restart, search for "Ubuntu" in the Start menu and launch it
6. Follow the prompts to set up your new Linux environment. You may be asked to create a user account and password
7. Run `sudo apt update` to ensure all packages are up to date

**Note:** If you encounter any issues, please refer to the official WSL installation guide: https://learn.microsoft.com/windows/wsl/install

### Install Seismic Unix

1. Open the Ubuntu terminal (search for "Ubuntu" in Windows Start menu)
2. Copy and paste this entire command:
3. `bash -c "$(wget -qO- https://gist.githubusercontent.com/a-pertuz/2b341bc8af2a37cde820d829f2789d99/raw/install_seismic_unix.sh)"`
4. Press Enter and wait for the installation to complete. It may take several minutes

**Important:** Read and **accept** the Seismic Unix license agreement when prompted.

### Install InSeis

```bash
pip install inseis
```

</details>

<details>
<summary><h2>🚀 Quick Start</h2></summary>

1. **Launch InSeis**: Open the application from your Start menu or run `inseis` in Command Prompt
2. **Create a new workflow**: The main interface displays available processes on the left and your current workflow on the right
3. **Load data**: Add a data loading process to your workflow (e.g., "SEGYREAD")
4. **Add processing steps**: Select and configure processing operations from the available processes list
5. **Run your workflow**: Click "Run Workflow" to execute all steps in sequence
6. **View results**: Results will be displayed automatically upon completion

**Important note**: Seismic Unix uses **SU** files as its native format. If you need **SEGY** files for external applications, use the **"Convert SU to SEGY"** utility in the menu bar after processing.

</details>

<details>
<summary><h2>📚 Complete Tutorial</h2></summary>

### Interface Overview

![InSeis GUI](images/is_gui_workflow.png)

The main application window consists of:

- **Process Library Panel (Left)**: Contains all available Seismic Unix processes organized by category
- **Workflow Canvas (Center)**: Where you build and configure your processing workflow
- **Parameters Panel (Right)**: Shows parameters for the currently selected process
- **Log Window (Bottom)**: Displays output and error messages from workflow execution
- **Results Viewer (Tab)**: Visualizes processing results

### Creating Workflows

#### Basic Workflow Structure

1. **Input**: Data loading processes (e.g., "Load SU File", "SEGYREAD")
2. **Processing**: Processing operations (filtering, deconvolution, migration, etc.)
3. **Output**: Results are saved as SU files and displayed within the application

#### Saving and Loading Workflows

**To save your workflow:**
1. Click **"Workflows"** > **"Save Workflow..."**
2. Enter a name and description

**To load a workflow:**
1. Click **"Workflows"** > **"Load Workflow..."**
2. Select from your saved workflows

#### Workflow Example: Post-stack Migration and SNR Enhancement

![Workflow Results](images/is_workflow_steps.png)

1. **Add SEGYREAD**: Set input file path
   ```
   tape=<input_file.segy>
   ```

2. **Add SEGYCLEAN**: Clean unused headers in the SU file

3. **Add SUAGC**: Automatic gain control
   ```
   panel=1, agc=1, wagc=0.75
   ```

4. **Add SUMIX**: Compute weighted moving average - trace mix
   ```
   mix=.6,1,1,1,.6
   ```

5. **Add SUKTMIG2D**: Kirchhoff post-stack time migration
   ```
   vfile=<velocity_model.bin>, hoffset=0, dx=25
   ```
   *Requires a velocity model in binary format (see [VelRecover](https://a-pertuz.github.io/REVSEIS/))**

6. **Add SUPEF**: Spike deconvolution for improved vertical resolution
   ```
   minlag=0.004, maxlag=0.12, pnoise=0.01
   ```

7. **Add SUFXDECON**: Random noise attenuation
   ```
   fmin=12, fmax=60, twlen=0.3, ntrw=30, ntrf=4
   ```

8. **Add SUTVBAND**: Time-variant bandpass filtering
   ```
   tf=0,1.5,2.5 f=10,12,55,60 f=14,16,50,55 f=14,16,45,50
   ```

</details>

<details>
<summary><h2>🔧 Troubleshooting</h2></summary>

### WSL Connection Issues

- **Ensure WSL is installed**: Open PowerShell and type `wsl --list`. If no distributions are listed, install one using `wsl --install`
- **Verify WSL is running**: Open PowerShell and type `wsl --list --running`
- **Restart WSL service**: `wsl --shutdown` and then launch WSL again
- **Check network settings** if you're accessing remote data

### Seismic Unix Not Found

- **Check your CWPROOT path** in the Configuration menu
- **Verify Seismic Unix installation**: Run `suplane | suximage` in WSL
- **Check environment variable**: `echo $CWPROOT` should show the SU installation path
- **Reinstall if needed** using the installation script

### Input/Output File Issues

- Check file permissions
- Ensure paths don't contain special characters
- Use forward slashes in file paths
- Verify file formats are supported

### Command Failures

- Check the log window for specific error messages
- Verify all required parameters are set
- Ensure input files exist and are accessible
- Check that all processes in the workflow are properly connected

</details>

<details>
<summary><h2>❓ FAQ</h2></summary>

### Is InSeis compatible with all versions of Seismic Unix?

InSeis works with Seismic Unix versions 43 and newer. The installer script automatically installs the latest compatible version. If you have an existing installation of Seismic Unix, InSeis will attempt to use it if the path is correctly set in your `.bashrc` file.

### How do I integrate results from SEGYRecover and VELRecover?

To use data from other REV-SEIS tools:
- SEGY files from SEGYRecover can be directly loaded using the "SEGYREAD" process
- Velocity models from VELRecover should be exported in binary format and can be loaded using the "Load Velocity Model" where necessary, for example during migration
- Use the workspace data directory structure to keep your project organized

### Does InSeis work on macOS or Linux?

InSeis is designed specifically for Windows with WSL. On macOS or Linux, you can install Seismic Unix directly and use its native command-line interface or GUI alternatives like OpenSeaSeis or BotoSeis.

### What is the difference between SU files and SEG-Y files?

SU (Seismic Unix) files and SEG-Y files are both formats for storing seismic data, but with key differences:
- **SU files** are the native format for Seismic Unix, with a simpler header structure and no EBCDIC header
- **SEG-Y files** are the industry standard with more extensive headers, including text headers with acquisition information
- InSeis can convert between these formats using the "SEGYREAD" and "SEGYWRITE" processes

### Can I run batch processing?

Currently, InSeis processes one workflow at a time. However, you can save workflows and reuse them with different datasets. For batch processing, consider using saved workflows with different input parameters.

</details>

<details>
<summary><h2>📄 Citation</h2></summary>

If you use this software in your research, please cite it as:

```
Pertuz, A., Benito, M. I., Llanes, P., Suárez-González, P., & García-Martín, M. (2025c). InSeis: A Python GUI-based application that brings Seismic Unix routines to Windows using the Linux subsystem. Zenodo. https://doi.org/10.5281/zenodo.15053545
```

Find this software in the Zenodo Archive: [https://doi.org/10.5281/zenodo.15053545](https://doi.org/10.5281/zenodo.15053545)

</details>

<details>
<summary><h2>⚖️ License</h2></summary>

This software is licensed under the GNU General Public License v3.0 (GPL-3.0).

You may copy, distribute and modify the software as long as you track changes/dates in source files. 
Any modifications to or software including (via compiler) GPL-licensed code must also be made available 
under the GPL along with build & installation instructions.

For the full license text, see [LICENSE](LICENSE) or visit https://www.gnu.org/licenses/gpl-3.0.en.html

</details>

---

*For questions, support, or feature requests, please contact Alejandro Pertuz at apertuz@ucm.es*
