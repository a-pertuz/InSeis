import subprocess

# Get the home directory of the WSL user
command = ["wsl", "bash", "-c", "echo $HOME"]
result = subprocess.run(command, capture_output=True, text=True)
home_dir = result.stdout.strip()

# Construct the SeismicUnix path
su_path = f"{home_dir}/SeismicUnix"
print(f"Seismic Unix path: {su_path}")

# Verify the path exists
verify_cmd = ["wsl", "bash", "-c", f"[ -d '{su_path}' ] && echo 'Directory exists' || echo 'Directory not found'"]
verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
print(verify_result.stdout.strip())

# You can also get this path in Windows format if needed
win_path_cmd = ["wsl", "wslpath", "-w", su_path]
win_path_result = subprocess.run(win_path_cmd, capture_output=True, text=True)
win_su_path = win_path_result.stdout.strip()
print(f"Windows path: {win_su_path}")