# Multi-GPU Monitoring and Throttling Detection
This is a personal project for my gaming PC (GPU: GTX 1660 super) .

It provides real-time monitoring for **NVIDIA/AMD** GPU(s) under load, with throttling detection based on temperature and GPU core clock drops. 
**Multi-GPU systems** are fully supported.

## Project Structure
. ├── main.py # Script to start GPU monitoring and throttling detection

├── gpureader.py # GPU detection and metrics collection for NVIDIA/AMD GPUs

└── README.md # Project documentation

## Command
```
# Run GPU monitoring and throttling detection
python main.py
```
## Requirements
- NVIDIA: pynvml
- AMD on Linux: pyamdgpuinfo
- AMD on Windows: pynvml_amd_windows (experimental)

## Configurations
You can adjust constants in main.py to customize monitoring. See the docstring in main.py for details.
