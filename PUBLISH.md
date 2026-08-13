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
- [ ] The user explicitly approved external submission.

## Known gaps

- **Not yet run on CardputerZero hardware.** The framebuffer blit, evdev
  keyboard node and ALSA output are written against the documented platform and
  verified in the desktop simulator and CI, but never on a device.
- Station stream URLs in `data/stations.toml` have not been reachability-tested
  from a network with outbound access.

## Submission Result

- Status: `not submitted`
- Submitted at: TODO
- Portal message: TODO
- Actions URL: TODO
- Tracking or pull-request URL: TODO
