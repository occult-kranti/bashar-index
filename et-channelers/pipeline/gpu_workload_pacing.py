"""Pace synchronized CUDA batches and report device-wide utilization when available."""
from contextlib import contextmanager
import math
import re
import shutil
import subprocess
import time


class DeviceTelemetry:
    """Read the same physical device used by CUDA, including on multi-GPU hosts."""
    def __init__(self, bus_id):
        if isinstance(bus_id, bytes):
            bus_id = bus_id.decode("ascii")
        if not isinstance(bus_id, str) or not re.fullmatch(r"[0-9A-Fa-f]{4,8}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}\.[0-7]", bus_id):
            raise ValueError("A CUDA PCI bus ID is required for device telemetry")
        self.bus_id = bus_id
        self.nvml = None
        self.handle = None
        self.smi = shutil.which("nvidia-smi")
        try:
            import pynvml
            pynvml.nvmlInit()
        except (ImportError, OSError):
            return
        except Exception as error:
            if isinstance(error, pynvml.NVMLError):
                return
            raise
        self.nvml = pynvml
        try:
            self.handle = pynvml.nvmlDeviceGetHandleByPciBusId(bus_id.encode("ascii"))
        except pynvml.NVMLError:
            self.close()

    def sample(self):
        if self.handle is None:
            return self.fallback_sample()
        api = self.nvml
        return {"gpu_percent": api.nvmlDeviceGetUtilizationRates(self.handle).gpu,
                "vram_bytes": api.nvmlDeviceGetMemoryInfo(self.handle).used,
                "temperature_c": api.nvmlDeviceGetTemperature(self.handle, api.NVML_TEMPERATURE_GPU),
                "backend": "pynvml"}

    def fallback_sample(self):
        if self.smi is None:
            raise RuntimeError("NVIDIA management telemetry is unavailable")
        result = subprocess.run(
            [self.smi, "--id=" + self.bus_id, "--query-gpu=utilization.gpu,memory.used,temperature.gpu",
             "--format=csv,noheader,nounits"], check=True, capture_output=True, text=True, timeout=5)
        utilization, memory_mib, temperature = map(int, result.stdout.strip().split(","))
        return {"gpu_percent": utilization, "vram_bytes": memory_mib * 1024**2,
                "temperature_c": temperature, "backend": "nvidia-smi-nvml"}

    def close(self):
        if self.nvml is not None:
            self.nvml.nvmlShutdown()
            self.handle = self.nvml = None


class Pacer:
    def __init__(self, synchronize, target, monitor=None, *, clock=time.monotonic, sleeper=time.sleep):
        if not callable(synchronize) or isinstance(target, bool) or not isinstance(target, (int, float)) or not 0 < target <= .70:
            raise ValueError("CUDA pacing requires synchronization and a target fraction up to 0.70")
        self.synchronize = synchronize
        self.target = target
        self.monitor = monitor
        self.clock = clock
        self.sleeper = sleeper
        self.next_start = clock()
        self.blocks = 0
        self.failed_blocks = 0
        self.busy = self.idle = 0.0
        self.in_block = False
        self.telemetry = None

    def wait(self):
        delay = self.next_start - self.clock()
        if delay > 0:
            start = self.clock()
            self.sleeper(delay)
            self.idle += self.clock() - start

    @contextmanager
    def block(self):
        if self.in_block:
            raise RuntimeError("CUDA pacing blocks must be sequential")
        self.wait()
        if self.monitor is not None:
            start = self.clock()
            self.monitor.guard()
            self.idle += self.clock() - start
        start = self.clock()
        self.in_block = True
        try:
            try:
                yield
            finally:
                self.synchronize()
        except BaseException:
            self.failed_blocks += 1
            raise
        else:
            self.blocks += 1
        finally:
            end = self.clock()
            elapsed = end - start
            self.busy += elapsed
            self.next_start = end + elapsed * (1 - self.target) / self.target
            self.in_block = False

    def summary(self):
        return {"target_percent": self.target * 100, "completed_blocks": self.blocks, "failed_blocks": self.failed_blocks,
                "synchronized_block_seconds": self.busy, "deliberate_wait_seconds": self.idle,
                "device_telemetry": self.telemetry,
                "pacing_mode": "sampled_device_and_block_duty" if self.telemetry else "block_duty_only"}


@contextmanager
def pace_cuda(*, pci_bus_id, synchronize, target=.70):
    """Use the ASR monitor's 30-second window and spread even sub-second bursts."""
    from . import gpu_asr_multilingual

    pacer = Pacer(synchronize, target)
    reader = DeviceTelemetry(pci_bus_id)
    monitor = None
    try:
        try:
            reader.sample()
        except (ValueError, OSError, RuntimeError, subprocess.SubprocessError):
            telemetry_available = False
        except Exception as error:
            if reader.nvml is None or not isinstance(error, reader.nvml.NVMLError):
                raise
            try:
                reader.fallback_sample()
            except (ValueError, OSError, RuntimeError, subprocess.SubprocessError):
                telemetry_available = False
            else:
                telemetry_available = True
        else:
            telemetry_available = True
        if telemetry_available:
            # Callers check available GPU memory against the sizes of their own arrays.
            monitor = gpu_asr_multilingual.Monitor(reader, lambda: None, target * 100, math.inf)
            monitor.begin()
            pacer.monitor = monitor
        yield pacer
        pacer.wait()
    finally:
        try:
            if monitor is not None and hasattr(monitor, "thread"):
                measured = monitor.finish()
                measured.pop("samples", None)
                pacer.telemetry = measured
        finally:
            reader.close()
