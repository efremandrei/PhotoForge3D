# Version 1.0.0 · build 1 verification

- 12 Python checks passed: millimetre scaling and STL readback, explicit opt-in for inferred repair, rejection of invalid sizes/crops, pairing authentication, real mesh export/download, malformed scan identifiers, and preservation of continuous surfaces in the simplified preview.
- COLMAP 4.2.1 CPU and OpenMVS v2.4.0 reconstructed the official 11-photo OpenMVG Sceaux Castle example. All 11 cameras registered. The original raw mesh has 146,332 triangles. Its explicitly sealed STL has 149,584 triangles, positive volume, watertight topology and maximum extent 100.0 mm after serialization/readback.
- Android release assembly and lint passed. APK metadata: `com.efremandrei.photoforge3d`, versionName `1.0.0`, versionCode `1`, min SDK 29, target SDK 35. V2 signature verified, RSA 3072, certificate SHA256 `47581bcdc90d04302786c170e084fcd0ca0a474597f292bc35bca35d2f2b2421`.
- The exact release APK was installed on the Android 15 emulator. Instrumentation passed the production flow: upload 11 sample photos, real CPU reconstruction, surface preview, explicit sealing, STL download, save callback and theme persistence. A separate system document-picker save produced a 5,185,084-byte STL whose SHA256 matched the PC output: `fcfeef3772711050193df35e6d89c5425f0462f5c96254593c625741cff99b6b`.
- The Windows x64 packaged executable passed its self-test: native Tk window creation and simplified mesh rendering, open-surface repair/export/readback, authenticated HTTP backend requests, and startup of the bundled COLMAP and OpenMVS executables.

The integration fixture is an architectural scene, not a precision object scan. No physical Samsung camera, Wi-Fi/firewall pairing on a phone, dimensional accuracy measurement, slicer print job, or physical printer test was performed. These remain practical validation steps with the user's photos and hardware. Thin features and unseen faces require particular care.

Only the release APK is published; the instrumentation APK and sample input photos are test fixtures. The PC package omits test executables, saved scans, pairing codes and private signing material.
