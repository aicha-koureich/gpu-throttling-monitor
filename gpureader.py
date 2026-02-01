"""
GPUReader: Multi-GPU Metrics Detection

This module provides GPU detection and metrics collection for NVIDIA and AMD GPUs on Linux and Windows.
It supports multi-GPU systems, allowing monitoring of multiple GPUs simultaneously.

Features:
    - Detects NVIDIA and AMD GPUs and selects the appropriate API
    - Returns live metrics per GPU: temperature, GPU/VRAM usage, GPU/VRAM clocks, GPU power consumption
    - Works with multiple GPUs at once

Requirements:
🚨 Warning: AMD Windows support is experimental and may be unstable
    NVIDIA: pynvml
    AMD Linux: pyamdgpuinfo
    AMD Windows: pynvml_amd_windows

Author: Aïcha Koureich
Date: 2026-01-30
"""
import time
from dataclasses import dataclass
import platform

@dataclass
class GPUStats:
    """Dataclass storing metrics for a single GPU at a specific timestamp."""
    gpu_index: int
    temperature: int
    gpu_utilization: int
    memory_utilization: int
    power_usage: int
    gpu_clock: int
    memory_clock: int
    timestamp: float

class GPUReader:
    """Detect GPU type and provide per-GPU metrics for NVIDIA and AMD GPUs."""
    def __init__(self):
        self.mode: str = ''
        self.n_gpus: int = 0
        self.api = None

        print("for NVIDIA: install pynvml, for AMD on Linux: install pyamdgpuinfo, for AMD on Windows: install pynvml_amd_windows")

        #Attempt to detect NVIDIA GPU
        try:
            import pynvml
            pynvml.nvmlInit()
            count: int = pynvml.nvmlDeviceGetCount()
            if count > 0:
                self.mode = 'nvidia'
                self.n_gpus = count
                self.api = pynvml
                print(f"{self.n_gpus} GPU(s) detected on {self.mode}")
                return
        except ImportError:
            print("pynvml package not installed. Please install it to access NVIDIA GPUs")
            pynvml = None
            pass

        # Attempt to detect AMD GPUs (distinguish by OS)
        system = platform.system()
        if system == 'Linux':
            try:
                import pyamdgpuinfo
                count = pyamdgpuinfo.detect_gpus()
                if count > 0:
                    self.mode = 'amd_Linux'
                    self.n_gpus = count
                    self.api = pyamdgpuinfo
                    print(f"{self.n_gpus} GPU(s) detected on {self.mode}")
                    return
            except ImportError:
                print("pyamdgpuinfo package not installed. Please install it to access AMD GPUs on Linux")
                pyamdgpuinfo = None
                pass
        elif system == 'Windows':
            try:
                import pynvml_amd_windows
                count = pynvml_amd_windows.nvmlDeviceGetCount()
                if count > 0:
                    self.mode = 'amd_Windows'
                    self.n_gpus = count
                    self.api = pynvml_amd_windows
                    print(f"{self.n_gpus} GPU(s) detected on {self.mode}")
                    return
            except ImportError:
                print("pynvml_amd_windows package not installed. Please install it to access AMD GPUs on Windows")
                pynvml_amd_windows = None
                pass

        raise RuntimeError("No compatible GPU detected or required package not installed")

    def get_metrics(self):
        """ Return metrics for all detected GPUs.
            - For multi-GPU systems, returns one GPUStats object per GPU
        """
        metrics_list = []
        for gpu_idx in range(self.n_gpus):
            try:
                if self.mode in ('nvidia', 'amd_Windows'):
                    handle = self.api.nvmlDeviceGetHandleByIndex(gpu_idx)
                    stats = GPUStats(gpu_index=gpu_idx,
                                temperature=self.api.nvmlDeviceGetTemperature(handle,self.api.NVML_TEMPERATURE_GPU),
                                gpu_utilization=self.api.nvmlDeviceGetUtilizationRates(handle).gpu,
                                memory_utilization=self.api.nvmlDeviceGetUtilizationRates(handle).memory,
                                power_usage=self.api.nvmlDeviceGetPowerUsage(handle)/1000,
                                gpu_clock=self.api.nvmlDeviceGetClockInfo(handle,self.api.NVML_CLOCK_GRAPHICS),
                                memory_clock = self.api.nvmlDeviceGetClockInfo(handle,self.api.NVML_CLOCK_MEM),
                                timestamp=time.time())

                elif self.mode == 'amd_Linux':
                    handle = self.api.get_gpu(gpu_idx)
                    stats = GPUStats(gpu_index=gpu_idx,
                                temperature=int(handle.query_temperature()),
                                gpu_utilization=int(handle.query_load()),
                                memory_utilization=handle.query_vram_usage(),
                                power_usage=handle.query_power(),
                                gpu_clock=handle.query_sclk(),
                                memory_clock =handle.query_mclk(),
                                timestamp=time.time())

                metrics_list.append(stats)
            # Catch any read errors per GPU (e.g., driver issues or dead GPU) and continue
            except Exception as e:
                print(f"Warning: could not read metrics for GPU {gpu_idx}: {e}, check for drivers issues or dead GPU(s)")
        return metrics_list