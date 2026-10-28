# ruff: noqa: ANN201, D100, D101, D102, INP001, PT009

import unittest
from types import SimpleNamespace
from typing import Self
from unittest.mock import Mock, patch

from custom_components.eufy_sdk.camera import async_setup_entry


def _entry(devices: dict) -> SimpleNamespace:
    runtime = SimpleNamespace(snapshot_policy={})
    entry = SimpleNamespace(data={"host": "bridge", "port": 3000}, runtime_data=runtime)
    runtime.coordinator = SimpleNamespace(data=devices, config_entry=entry)
    return entry


def _s4() -> dict:
    return {
        "sn": "EXAMPLE-POE-S4",
        "name": "PoE Cam S4",
        "model": "T8E00",
        "codec": "camera",
        "capabilities": ["camera", "ptz"],
        "power": "wired",
        "stream": "/stream/EXAMPLE-POE-S4",
        "streams": [{"sensor": 0}, {"sensor": 1}],
    }


class NvrViewsCompatibilityTests(unittest.IsolatedAsyncioTestCase):
    async def _entities(self, devices: dict) -> list:
        added = Mock()
        await async_setup_entry(Mock(), _entry(devices), added)
        return list(added.call_args.args[0])

    async def test_setup_preserves_both_lenses_on_the_existing_bridge(self):
        entities = await self._entities({"EXAMPLE-POE-S4": _s4()})
        self.assertEqual(len(entities), 2)
        self.assertEqual(
            {camera.unique_id for camera in entities},
            {"EXAMPLE-POE-S4_camera", "EXAMPLE-POE-S4_camera_sensor_0"},
        )
        self.assertEqual(entities[0].device_info, entities[1].device_info)
        self.assertEqual(
            {await camera.stream_source() for camera in entities},
            {
                "rtsp://bridge:8554/EXAMPLE-POE-S4",
                "rtsp://bridge:8554/EXAMPLE-POE-S4_fixed",
            },
        )

    async def test_snapshot_requests_keep_each_lens_separate(self):
        entities = await self._entities({"EXAMPLE-POE-S4": _s4()})
        urls = []

        class Response:
            status = 200

            async def __aenter__(self) -> Self:
                return self

            async def __aexit__(self, *_args: object) -> None:
                return None

            async def read(self) -> bytes:
                return b"jpeg"

        def get(url: str, **_kwargs: object) -> Response:
            urls.append(url)
            return Response()

        with patch(
            "custom_components.eufy_sdk.camera.async_get_clientsession",
            return_value=SimpleNamespace(get=get),
        ):
            for camera in entities:
                camera.hass = Mock()
                self.assertEqual(await camera.async_camera_image(), b"jpeg")
        self.assertEqual(
            set(urls),
            {
                "http://bridge:3000/nvr-snapshot/EXAMPLE-POE-S4/0",
                "http://bridge:3000/nvr-snapshot/EXAMPLE-POE-S4/1",
            },
        )

    async def test_legacy_and_single_view_devices_keep_one_camera(self):
        for device in (
            {key: value for key, value in _s4().items() if key != "streams"},
            {**_s4(), "model": "T8P00"},
            {**_s4(), "streams": [{"sensor": 0}]},
        ):
            with self.subTest(device=device):
                entities = await self._entities({"EXAMPLE-POE-S4": device})
                self.assertEqual(len(entities), 1)
                self.assertEqual(entities[0].unique_id, "EXAMPLE-POE-S4_camera")
                self.assertEqual(
                    await entities[0].stream_source(),
                    "rtsp://bridge:8554/EXAMPLE-POE-S4",
                )
