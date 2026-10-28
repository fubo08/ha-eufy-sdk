"""Camera platform — a live camera per streaming device, via the bridge's go2rtc."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONF_GO2RTC_RTSP_PORT,
    CONF_HOST,
    CONF_PORT,
    DEFAULT_GO2RTC_RTSP_PORT,
    DOMAIN,
)
from .entity import device_offline
from .preload import async_check_preload, on_battery_power
from .snapshot_policy import snapshot_url

if TYPE_CHECKING:
    from homeassistant.components.stream import Stream
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import EufySdkDataUpdateCoordinator
    from .data import EufySdkConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: EufySdkConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create a camera for every device the bridge marked with a `stream` path."""
    coordinator = entry.runtime_data.coordinator
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    rtsp_port = int(entry.data.get(CONF_GO2RTC_RTSP_PORT, DEFAULT_GO2RTC_RTSP_PORT))
    async_add_entities(
        EufySdkCamera(coordinator, sn, host, port, rtsp_port, sensor=sensor)
        for sn, dev in coordinator.data.items()
        if dev.get("stream")
        for sensor in camera_sensors(dev)
    )


def camera_sensors(dev: dict) -> list[int | None]:
    """Offer both S4 lenses only when the bridge advertises their streams."""
    sensors = {
        item.get("sensor")
        for item in dev.get("streams", []) or []
        if isinstance(item, dict) and type(item.get("sensor")) is int
    }
    return [1, 0] if dev.get("model") == "T8E00" and sensors == {0, 1} else [None]


class EufySdkCamera(CoordinatorEntity["EufySdkDataUpdateCoordinator"], Camera):
    """A camera via the bridge: live via go2rtc RTSP, stills via snapshot."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(  # noqa: PLR0913
        self,
        coordinator: EufySdkDataUpdateCoordinator,
        sn: str,
        host: str,
        port: int,
        rtsp_port: int,
        *,
        sensor: int | None = None,
    ) -> None:
        """Bind to a device serial + the bridge address."""
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._sn = sn
        self._host = host
        self._port = port
        self._rtsp_port = rtsp_port
        self._sensor = sensor
        self._stream_id = f"{sn}_fixed" if sensor == 0 else sn
        self._attr_unique_id = f"{sn}_camera"
        if sensor is not None:
            self._attr_translation_key = "fixed" if sensor == 0 else "movable"
        else:
            self._attr_name = None
        if sensor == 0:
            self._attr_unique_id = f"{sn}_camera_sensor_0"
        dev = coordinator.data.get(sn, {})
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, sn)},
            name=dev.get("name") or sn,  # the user's device name (e.g. "Dining room")
            manufacturer="eufy",
            model=dev.get("model") or dev.get("codec"),  # the model code, not the codec
            serial_number=sn,
        )

    async def async_added_to_hass(self) -> None:
        """Flag stream preloading on a battery camera once the entity is registered."""
        await super().async_added_to_hass()
        await async_check_preload(
            self.hass, self.entity_id, self._sn, self.coordinator.data.get(self._sn)
        )

    @property
    def available(self) -> bool:
        """Available while the bridge still reports this camera and it isn't offline."""
        return (
            super().available
            and self._sn in self.coordinator.data
            and not device_offline(self.coordinator.data.get(self._sn))
        )

    async def stream_source(self) -> str:
        """Return the go2rtc RTSP URL — HA's stream component + go2rtc do the work."""
        return f"rtsp://{self._host}:{self._rtsp_port}/{self._stream_id}"

    async def async_create_stream(self) -> Stream | None:
        """
        Skip Home Assistant's stream worker for a battery camera.

        That worker retries a failed or closed source forever, and every retry makes
        the bridge wake the camera over P2P. A battery camera was drained flat that way
        after one live view (ha-eufy-sdk#83). Live view then runs through Home
        Assistant's go2rtc (WebRTC) on the same RTSP restream, so there is no HLS
        fallback and no camera.record for battery cameras.
        """
        if on_battery_power(self.coordinator.data.get(self._sn)):
            return None
        return await super().async_create_stream()

    async def async_camera_image(
        self,
        width: int | None = None,  # noqa: ARG002
        height: int | None = None,  # noqa: ARG002
    ) -> bytes | None:
        """Return a still from the bridge's /snapshot endpoint."""
        session = async_get_clientsession(self.hass)
        url = snapshot_url(
            self._host,
            self._port,
            self._sn,
            self.coordinator.config_entry.runtime_data.snapshot_policy.get(self._sn),
        )
        if self._sensor is not None:
            url = (
                f"http://{self._host}:{self._port}"
                f"/nvr-snapshot/{self._sn}/{self._sensor}"
            )
        try:
            async with session.get(url, timeout=20) as resp:
                if resp.status == HTTPStatus.OK:
                    return await resp.read()
        except (TimeoutError, OSError):
            return None
        return None
