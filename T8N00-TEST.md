# T8N00 / PoE S4 test integration 0.3.1b1

Use with [fubo08/eufy-t8n00-test-addon](https://github.com/fubo08/eufy-t8n00-test-addon) 0.3.0 or later. This experimental fork is based on upstream `dev` at e51af8b2f3b4aacea08d8ba50e80e2c8c1c12f1e.

The bridge advertises two T8E00 optical views. HA keeps the existing camera unique ID for the movable view and adds a fixed camera under the same physical device. Four PTZ direction buttons use the existing SDK actions. Preset selection is not offered for the S4 because its preset commands are not verified.

Install the release ZIP by replacing `custom_components/eufy_sdk` with the enclosed `eufy_sdk` folder (keep a backup of the previous folder), then restart Home Assistant. Do not delete the existing integration entry or devices. The domain is unchanged: this replaces the upstream integration, it cannot be installed alongside it. Alternatively use this fork as a HACS custom integration repository and enable prerelease versions; remove the upstream repository from HACS tracking first, without deleting the integration in HA.

Keep bridge/RTSP ports 3000/8554. Update the bridge first. After both updates, open the device and check the cameras named Fixed/Movable (Fest/Beweglich). Try each lens separately before simultaneous viewing. Test one small PTZ step while watching the movable view. Enable sound manually in the camera player (browsers mute autoplay).

Arming and a single RTC video view worked on the owner's T8N00 before this release. The second view, PTZ direction steps and audio still need confirmation on this hardware. This version adds received audio playback, not two-way talk. AAC-LC with ADTS framing and G.711 A-law are supported by the bridge; other framing logs a video-only fallback. A successful synthetic mux test does not prove the camera's microphone has supplied audio.

To revert, restore the previous integration folder and restart HA; select the previous bridge release. The original camera unique ID and device identifiers stay the same.
