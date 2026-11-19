from unittest import TestCase
from unittest.mock import Mock, patch

from pipeline import gpu_workload_pacing as pacing


class Clock:
    def __init__(self):
        self.seconds = 0

    def now(self):
        return self.seconds

    def advance(self, seconds):
        self.seconds += seconds


class WorkloadPacingTests(TestCase):
    def test_short_cuda_blocks_accrue_idle_time_and_count_completed_work(self):
        clock = Clock()
        pacer = pacing.Pacer(lambda: clock.advance(.1), .7, clock=clock.now, sleeper=clock.advance)
        for _ in range(10):
            with pacer.block():
                clock.advance(.6)
        pacer.wait()
        result = pacer.summary()
        self.assertAlmostEqual(result["synchronized_block_seconds"], 7)
        self.assertAlmostEqual(result["deliberate_wait_seconds"], 3)
        self.assertAlmostEqual(clock.now(), 10)
        self.assertEqual(result["completed_blocks"], 10)
        self.assertIsNone(result["device_telemetry"])

    def test_intervening_cpu_work_counts_toward_required_idle_time(self):
        clock = Clock()
        synchronize = Mock()
        pacer = pacing.Pacer(synchronize, .5, clock=clock.now, sleeper=clock.advance)
        with pacer.block():
            clock.advance(2)
        clock.advance(1.6)
        with pacer.block():
            clock.advance(1)
        self.assertAlmostEqual(pacer.summary()["deliberate_wait_seconds"], .4)
        self.assertEqual(synchronize.call_count, 2)
        with self.assertRaises(ValueError):
            with pacer.block():
                raise ValueError("failed CUDA work")
        self.assertEqual(pacer.summary()["failed_blocks"], 1)
        self.assertEqual(pacer.summary()["completed_blocks"], 2)

    def test_sampler_lifecycle_retains_measured_summary_without_raw_trace(self):
        reader, monitor = Mock(), Mock()
        monitor.thread = object()
        monitor.finish.return_value = {"sample_count": 3, "mean_gpu_percent": 31, "samples": [{"gpu_percent": 31}]}
        with patch.object(pacing, "DeviceTelemetry", return_value=reader), patch(
                "pipeline.gpu_asr_multilingual.Monitor", return_value=monitor):
            with pacing.pace_cuda(pci_bus_id="0000:01:00.0", synchronize=lambda: None) as pacer:
                with pacer.block():
                    pass
            self.assertEqual(pacer.summary()["device_telemetry"], {"sample_count": 3, "mean_gpu_percent": 31})
            monitor.begin.assert_called_once()
            monitor.guard.assert_called_once()
            monitor.finish.assert_called_once()
            reader.close.assert_called_once()

    def test_missing_sensor_uses_time_pacing_and_rejects_invalid_target(self):
        reader = Mock()
        reader.sample.side_effect = RuntimeError("unavailable")
        with patch.object(pacing, "DeviceTelemetry", return_value=reader):
            with pacing.pace_cuda(pci_bus_id="0000:01:00.0", synchronize=lambda: None) as pacer:
                with pacer.block():
                    pass
        self.assertEqual(pacer.summary()["pacing_mode"], "block_duty_only")
        self.assertIsNone(pacer.summary()["device_telemetry"])
        for value in (0, .71, float("nan"), True, "70"):
            with self.assertRaises(ValueError):
                pacing.Pacer(lambda: None, value)
