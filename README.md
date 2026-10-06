# Home Assistant Spotify Soloist App

This repository contains the Home Assistant app wrapper for Spotify Soloist.

See [`spotify_soloist/README.md`](spotify_soloist/README.md) for installation and configuration details.

## Home Assistant integration

The repository also contains a custom Home Assistant integration under `custom_components/spotify_soloist`.

The app uses host networking for Spotify Connect mDNS discovery. Configure the integration with the Home Assistant host's LAN IP address (or a hostname that resolves to it) and the app's WebSocket port, `9090` by default. The internal app hostname is not available in host network mode. After updating an existing installation, remove and add the integration again with the host address.
