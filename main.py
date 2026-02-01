"""
Multi-GPU support Monitoring and Throttling Detection

This script continuously monitors GPU metrics (temperature, GPU load, GPU clock, GPU power usage, VRAM usage and clock speed)
for NVIDIA and AMD GPUs on Linux or Windows.
It prints live stats when the GPU is under load, and detects possible thermal throttling
based on elevated temperature and drops in GPU core clock relative to previous measurements.

Supports multi-GPU systems for simultaneous monitoring.

Usage: python main.py

Requirements:
🚨 Warning: AMD Windows support is experimental and may be unstable
    NVIDIA: pynvml
    AMD Linux: pyamdgpuinfo
    AMD Windows: pynvml_amd_windows

Configuration:
    The following constants can be tuned according to your needs:
    - TEMP_THRESHOLD       : temperature (°C) where throttling detection starts
    - MONITORING_LOAD      : GPU load (%) required to start printing metrics
    - THROTTLING_LOAD      : GPU load (%) to start throttling detection
    - DROP_FACTOR          : relative GPU clock drop threshold (e.g. 0.85 -> 15% drop)
    - PERSISTENCE          : consecutive drops required to trigger throttling warning
    - MAX_HISTORY          : maximum number of clock values stored per GPU (if exceeded the first value is deleted)
    - PREV_VAL             : number of previous clocks used for averaging

Author: Aïcha Koureich
date : 2026-01-30
"""
import time
from gpureader import GPUReader

#Configuration of Constants
TEMP_THRESHOLD = 90
MONITORING_LOAD = 30
THROTTLING_LOAD = 70
DROP_FACTOR = 0.85
PERSISTENCE = 3
MAX_HISTORY = 20
PREV_VAL = 5

#Initialization of global lists
gpu_clock_list = []
counter = []

#Throttling detection
def throttling(gpu):
    """Detect potential GPU throttling based on high temperature and recent and continuous drops in core clock."""
    clocks = gpu_clock_list[gpu.gpu_index]
    #High temperature detection
    if gpu.temperature >= TEMP_THRESHOLD:
        print(f"Warning :High temperature {gpu.gpu_index}: {gpu.temperature} °C")

        if len(clocks) >= PREV_VAL + 1:
            # Compute average of previous gpu clock's value
            prev = clocks[-(PREV_VAL+1):-1]
            mean_prev = sum(prev)/len(prev)
            drop = (mean_prev - clocks[-1])*100 / mean_prev

            #Increment or reset counter based on drop relative to average
            if clocks[-1] <= DROP_FACTOR * mean_prev:
                counter[gpu.gpu_index] += 1
            else:
                counter[gpu.gpu_index] = 0

            #If drop persisted over PERSISTENCE consecutive readings, print the warning
            if counter[gpu.gpu_index] >= PERSISTENCE:
                print(f"Warning: Possible temperature throttling for GPU {gpu.gpu_index}: GPU temperature : {gpu.temperature} °C, "
                      f"Last GPU clock : {clocks[-1]}, Mean of previous GPU clock : {mean_prev:.1f}, Drop : {drop:.1f} %")

def start_monitoring():
    """Continuously monitor GPU metrics and check for throttling."""
    #Create the object gpu_reader and the list of stats for each GPU
    gpu_reader = GPUReader()
    metrics_list = gpu_reader.get_metrics()

    #Initialize clock history and the
    for gpu in metrics_list:
        gpu_clock_list.append([])
        counter.append(0)

    while True:
        time.sleep(1)
        metrics_list = gpu_reader.get_metrics()

        for gpu in metrics_list:
            #Print GPU metrics if above monitoring load threshold
            if gpu.gpu_utilization >= MONITORING_LOAD:
                print(f"GPU id :{gpu.gpu_index}, GPU temperature :{gpu.temperature}°C, GPU load : {gpu.gpu_utilization}%,GPU clock :{gpu.gpu_clock} MHz,"
                      f"GPU power usage :{gpu.power_usage} W, VRAM load : {gpu.memory_utilization}%, VRAM clock :{gpu.memory_clock} MHz")
            #Track core clock and check for throttling if load is high
            if gpu.gpu_utilization >= THROTTLING_LOAD:
                gpu_clock_list[gpu.gpu_index].append(gpu.gpu_clock)
                # Maintain history length
                if len(gpu_clock_list[gpu.gpu_index]) > MAX_HISTORY:
                    gpu_clock_list[gpu.gpu_index].pop(0)
                throttling(gpu)


if __name__ == '__main__':
    try:
        start_monitoring()
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")


