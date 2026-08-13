# Application Store Publish Record

Keep this file in the application project root. Update it when package
metadata, listing copy, assets, privacy choices, or submission status changes.

Portal: <https://dev.cardputer.cc/#/upload>

## Package

- Debian package path: `dist/cardputerzero-radio_0.2.0-3_arm64.deb`
- Package: `cardputerzero-radio`
- Version: `0.2.0-3`
- Architecture: `arm64`
- Maintainer: `churchja <jason.a.church@gmail.com>`
- APPLaunch desktop path: `/usr/share/APPLaunch/applications/cardputerzero-radio.desktop`
- Executable path: `/usr/share/APPLaunch/bin/cardputerzero-radio`

## Source and Ownership

- Public source repository: <https://github.com/churchja/cardputerzero-radio>
- Expected GitHub uploader/owner: `churchja`
- Hide uploader email: `true`

## Listing

- Application name: Radio
- One-line summary (maximum 80 characters):
  `Internet radio with station search, favourites, sleep timer and alarm`
- Description: see the `store.description` field in `app-builder.json`
- Categories (maximum 6): Audio, Music, Internet, Utilities

## Assets

- 256 x 256 source icon: `packaging/icon.png`
- Icon packaged in `.deb`: `/usr/share/APPLaunch/share/images/cardputerzero-radio.png`
- Screenshot 1 (320 x 170): `store/screenshots/01-now-playing.png` — primary view, playing
- Screenshot 2 (320 x 170): `store/screenshots/02-stations.png` — station list
- Screenshot 3 (320 x 170): `store/screenshots/03-search.png` — search input workflow
- Screenshot 4 (320 x 170): `store/screenshots/04-settings.png` — settings/management
- Optional screenshot 5 (portal supports up to 6): not used
- Optional screenshot 6 (portal supports up to 6): not used

## Preflight

- [x] `.deb` exists and can be parsed.
- [x] Control fields contain Package, Version, Architecture, and Maintainer.
- [x] Architecture is appropriate for the package (`arm64`).
- [x] APPLaunch `.desktop`, executable, and PNG icon exist inside the package.
- [x] Package name ownership and update version are valid (new package, first upload).
- [x] Listing copy and categories have been reviewed.
- [x] Four clean 320 x 170 baseline screenshots exist.
- [x] No credentials, tokens, or private server details are embedded.
- [x] The user explicitly approved external submission.

## Known gaps

- **Not yet run on CardputerZero hardware.** The framebuffer blit, evdev
  keyboard node and ALSA output are written against the documented platform and
  verified in the desktop simulator and CI, but never on a device.
- Station stream URLs in `data/stations.toml` have not been reachability-tested
  from a network with outbound access.

## Submission Result

- Status: `submitted - awaiting server validation`
- Submitted at: `2026-08-13T07:02:05Z`
- Submitted version: `0.2.0-3` (arm64)
- Portal message: "Submitted, server is performing final validation; a release PR
  will be automatically generated upon approval."
- Actions URL:
  <https://github.com/CardputerZero/packages/actions/workflows/process-web-submission.yml>
- Tracking or pull-request URL:
  <https://github.com/CardputerZero/packages/pulls?q=is%3Apr+in%3Atitle+cardputerzero-radio+0.2.0-3>

### Follow-up

- Package name `cardputerzero-radio` is claimed first-come by `churchja` on this
  first accepted submission; later versions must come from the same login.
- Next version must be strictly newer than `0.2.0-3`.
- Watch for a review comment about runtime dependencies: the package depends on
  `mpv`, `python3-pil`, `python3-evdev`, `python3-numpy`, `alsa-utils` and
  `fonts-dejavu-core`. These are stock Debian/Raspberry Pi OS packages, but the
  install only succeeds if the device image's apt sources carry them.
