# T8N00 integration compatibility release 0.6.1b1

I rebased my integration on upstream `dev` at
`775560f561b76bd4a13da762a5d8e9cf4ca32ad9`, including release 0.6.0 and the
subsequent official fixes. This is my compatibility fork, not an official release.

I retain the existing test-bridge contract only when the device record advertises
T8E00 optical sensors 0 and 1: two camera entities, their existing unique IDs and
RTSP names, and separate `/nvr-snapshot` requests. Other devices and bridges retain
one camera. The upstream battery-worker protection and preload repairs remain.
S4 directional PTZ controls remain available; my prior exclusion of unverified S4
preset controls remains local to this fork.

The bridge, media codecs, audio, ports and existing configuration entry are not
changed by this integration update. Do not delete devices or recreate the entry.
Take a backup before installing, restart Home Assistant, then check both S4 views,
the E40 cameras, snapshots and directional controls. Rollback uses the prior
0.3.1b1 integration package followed by another Home Assistant restart.

The official bridge still needs to advertise and forward the SDK optical views.
This compatibility adapter does not claim the private test-bridge endpoints are
already an official protocol. Native NVR NAS/RTSP is separate: the tested endpoint
provided only the fixed optic at 1080p, while my existing RTC path retains both views.

Created with Codex.
