from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import aiohttp
from homeassistant.components.media_player import MediaPlayerDeviceClass, MediaPlayerEntity, MediaPlayerEntityFeature, MediaPlayerState
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

RECONNECT_MIN = 1
RECONNECT_MAX = 60


class SpotifySoloistCoordinator:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.host = entry.data[CONF_HOST]
        self.port = entry.data[CONF_PORT]
        self.ws: aiohttp.ClientWebSocketResponse | None = None
        self.session: aiohttp.ClientSession | None = None
        self.task: asyncio.Task | None = None
        self.listeners: set[callable] = set()
        self.state: dict[str, Any] = {}
        self.position_anchor: float | None = None
        self.position_anchor_time: float | None = None
        self._stop = False
        self._send_lock = asyncio.Lock()

    async def async_start(self) -> None:
        self.task = self.hass.async_create_task(self._run())

    async def async_stop(self) -> None:
        self._stop = True
        if self.task:
            self.task.cancel()
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()

    @property
    def connected(self) -> bool:
        return self.ws is not None and not self.ws.closed

    def add_listener(self, listener: callable) -> None:
        self.listeners.add(listener)

    def remove_listener(self, listener: callable) -> None:
        self.listeners.discard(listener)

    @callback
    def _notify(self) -> None:
        for listener in tuple(self.listeners):
            listener()

    async def _run(self) -> None:
        delay = RECONNECT_MIN
        while not self._stop:
            try:
                if self.session is None:
                    self.session = aiohttp.ClientSession()
                url = f"ws://{self.host}:{self.port}"
                async with self.session.ws_connect(url, heartbeat=20) as ws:
                    self.ws = ws
                    delay = RECONNECT_MIN
                    await self._receive_loop()
            except asyncio.CancelledError:
                raise
            except (aiohttp.ClientError, OSError, asyncio.TimeoutError) as err:
                self.ws = None
                self._notify()
                await asyncio.sleep(delay)
                delay = min(delay * 2, RECONNECT_MAX)
            finally:
                self.ws = None
                self._notify()

    async def _receive_loop(self) -> None:
        assert self.ws is not None
        async for message in self.ws:
            if message.type == aiohttp.WSMsgType.TEXT:
                try:
                    payload = json.loads(message.data)
                except json.JSONDecodeError:
                    continue
                self._handle_event(payload)
            elif message.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                break

    def _handle_event(self, payload: dict[str, Any]) -> None:
        event = payload.get("event") or payload.get("type")
        data = payload.get("data", payload)

        if event == "playback_state":
            self.state.update(data if isinstance(data, dict) else {})
        elif event in {"playback_play", "playback_pause", "playback_stop"}:
            self.state["is_playing"] = event == "playback_play"
        elif event in {"track_changed", "track_changed_event"}:
            if isinstance(data, dict):
                self.state["track"] = data
        elif event == "position_sync":
            if isinstance(data, dict):
                self.position_anchor = float(data.get("position", data.get("position_ms", 0)))
                self.position_anchor_time = time.monotonic()
                self.state["position"] = self.position_anchor
                if "duration" in data:
                    self.state["duration"] = data["duration"]
        elif event == "volume_changed":
            if isinstance(data, dict):
                self.state["volume"] = data.get("volume", data.get("value"))
        elif event == "shuffle_changed":
            if isinstance(data, dict):
                self.state["shuffle"] = data.get("shuffle", data.get("enabled"))
        elif event == "repeat_changed":
            if isinstance(data, dict):
                self.state["repeat"] = data.get("repeat", data.get("mode"))

        self._notify()

    def position(self) -> float | None:
        if self.position_anchor is None:
            return None
        if self.position_anchor_time is None or not self.state.get("is_playing", False):
            return self.position_anchor
        return self.position_anchor + (time.monotonic() - self.position_anchor_time)

    async def command(self, command: str, **kwargs: Any) -> None:
        if not self.connected or self.ws is None:
            return
        message = {"command": command, **kwargs}
        async with self._send_lock:
            await self.ws.send_json(message)


class SpotifySoloistEntity(CoordinatorEntity[SpotifySoloistCoordinator], MediaPlayerEntity):
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_has_entity_name = True
    _attr_name = "Spotify Soloist"
    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.SEEK
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SHUFFLE_SET
        | MediaPlayerEntityFeature.REPEAT_SET
        | MediaPlayerEntityFeature.PLAY_MEDIA
    )

    def __init__(self, coordinator: SpotifySoloistCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Spotify Soloist",
            manufacturer="Spotify",
            model="Soloist",
        )

    @property
    def available(self) -> bool:
        return self.coordinator.connected

    @property
    def state(self) -> MediaPlayerState | None:
        if not self.available:
            return None
        return MediaPlayerState.PLAYING if self.coordinator.state.get("is_playing") else MediaPlayerState.PAUSED

    @property
    def media_title(self) -> str | None:
        track = self.coordinator.state.get("track", {})
        return track.get("name") or track.get("title")

    @property
    def media_artist(self) -> str | None:
        track = self.coordinator.state.get("track", {})
        artist = track.get("artist")
        if isinstance(artist, dict):
            return artist.get("name")
        return artist

    @property
    def media_album_name(self) -> str | None:
        track = self.coordinator.state.get("track", {})
        album = track.get("album")
        if isinstance(album, dict):
            return album.get("name")
        return album

    @property
    def media_duration(self) -> float | None:
        return self.coordinator.state.get("duration")

    @property
    def media_position(self) -> float | None:
        return self.coordinator.position()

    @property
    def volume_level(self) -> float | None:
        volume = self.coordinator.state.get("volume")
        return None if volume is None else float(volume) / 100

    @property
    def is_volume_muted(self) -> bool | None:
        return self.coordinator.state.get("muted")

    @property
    def shuffle(self) -> bool | None:
        return self.coordinator.state.get("shuffle")

    @property
    def repeat(self) -> str:
        repeat = self.coordinator.state.get("repeat", "off")
        if repeat in ("track", "context", "off"):
            return repeat
        return "off"

    async def async_media_play(self) -> None:
        await self.coordinator.command("play")

    async def async_media_pause(self) -> None:
        await self.coordinator.command("pause")

    async def async_media_stop(self) -> None:
        await self.coordinator.command("stop")

    async def async_media_next_track(self) -> None:
        await self.coordinator.command("skip_next")

    async def async_media_previous_track(self) -> None:
        await self.coordinator.command("skip_prev")

    async def async_set_volume_level(self, volume: float) -> None:
        await self.coordinator.command("set_volume", volume=round(volume * 100))

    async def async_mute_volume(self, mute: bool) -> None:
        await self.coordinator.command("set_mute", mute=mute)

    async def async_media_seek(self, position: float) -> None:
        await self.coordinator.command("seek", position=position)

    async def async_set_shuffle(self, shuffle: bool) -> None:
        await self.coordinator.command("set_shuffle", shuffle=shuffle)

    async def async_set_repeat(self, repeat: str) -> None:
        await self.coordinator.command("set_repeat", repeat=repeat)

    async def async_play_media(self, media_type: str, media_id: str, **kwargs: Any) -> None:
        await self.coordinator.command("play", uri=media_id)
