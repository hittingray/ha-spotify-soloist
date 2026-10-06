# Home Assistant Spotify Soloist App

This repository contains the Home Assistant app wrapper for Spotify Soloist.

See [`spotify_soloist/README.md`](spotify_soloist/README.md) for installation and configuration details.

## Home Assistant integration

The repository also contains a custom Home Assistant integration under `custom_components/spotify_soloist`.

Its default connection is `local-spotify-soloist:9090`, using Home Assistant's internal app-to-app network. For apps installed from a GitHub repository, the repository identifier is different; the integration allows the hostname to be overridden during setup.
