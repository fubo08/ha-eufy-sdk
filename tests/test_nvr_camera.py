# ruff: noqa: D100, D102, INP001, PT009

import unittest
from types import SimpleNamespace

from custom_components.eufy_sdk.camera import EufySdkCamera, camera_sensors


class NvrCameraTests(unittest.IsolatedAsyncioTestCase):
    """Keep entity identities stable while adding the second optical view."""

    def test_old_bridge_and_other_models_keep_one_camera(self) -> None:
        self.assertEqual(camera_sensors({"model": "T8E00"}), [None])
        self.assertEqual(
            camera_sensors(
                {"model": "T8P00", "streams": [{"sensor": 0}, {"sensor": 1}]}
            ),
            [None],
        )
        self.assertEqual(
            camera_sensors(
                {"model": "T8E00", "streams": [{"sensor": 0}, {"sensor": 1}]}
            ),
            [1, 0],
        )

    async def test_lenses_share_device_but_have_separate_sources(self) -> None:
        coordinator = SimpleNamespace(data={"CAM1": {"model": "T8E00"}})
        primary = EufySdkCamera(coordinator, "CAM1", "bridge", 3000, 8554, sensor=1)
        fixed = EufySdkCamera(coordinator, "CAM1", "bridge", 3000, 8554, sensor=0)
        self.assertEqual(primary.unique_id, "CAM1_camera")
        self.assertEqual(fixed.unique_id, "CAM1_camera_sensor_0")
        self.assertEqual(primary.device_info, fixed.device_info)
        self.assertEqual(await primary.stream_source(), "rtsp://bridge:8554/CAM1")
        self.assertEqual(await fixed.stream_source(), "rtsp://bridge:8554/CAM1_fixed")
