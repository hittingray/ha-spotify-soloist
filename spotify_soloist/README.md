# Spotify Soloist for Home Assistant

A Home Assistant app (formerly add-on) wrapper for [Spotify Soloist](https://developer.spotify.com/documentation/soloist).

The Docker image **does not contain Spotify Soloist**. Spotify's architecture-specific release is downloaded at runtime, on the final Home Assistant host, and stored under `/data/soloist`.

## Features

- Architecture-neutral multi-platform Docker image.
- Uses Docker's built-in init via `init: true`.
- Downloads the correct Spotify Soloist release at runtime.
- Persists the Soloist binary, state, and cache under `/data/soloist`.
- Checks `soloist --version` at startup and refreshes a build when it is within 14 days of its 90-day lifetime.
- Uses host networking so Spotify Connect mDNS discovery can reach the local network.
- Listens for the Spotify Soloist WebSocket API on TCP port 9090 by default.
- Uses Home Assistant's audio integration (`audio: true`) for PulseAudio.

## Important Spotify requirements

You need a Spotify for Developers account and a Spotify Soloist API key. Spotify says not to redistribute Soloist archives or binaries; this app therefore downloads the binary directly from Spotify at runtime rather than including it in the image.

See the official documentation:

- [Spotify Soloist](https://developer.spotify.com/documentation/soloist)
- [Downloads and updates](https://developer.spotify.com/documentation/soloist/reference/downloads-and-updates)
- [Command line reference](https://developer.spotify.com/documentation/soloist/reference/command-line)

## Installation

1. Replace `YOUR_USERNAME` in `repository.yaml` and `spotify_soloist/config.yaml` with your GitHub username/organization.
2. Publish the image as `ghcr.io/YOUR_USERNAME/ha-spotify-soloist`.
3. Add this repository to Home Assistant's app repository list.
4. Install **Spotify Soloist**.
5. Enter your Spotify Soloist API key and desired device name.
6. Start the app.

On first start, the app detects the host architecture and downloads the matching Spotify Soloist archive from Spotify.

## WebSocket API

The app uses host networking for Spotify Connect's mDNS multicast discovery. Its WebSocket API is therefore bound directly on the Home Assistant host, on the configured `websocket_port` (9090 by default), rather than published through a Docker port mapping.

The app starts Soloist with:

```text
--ws 0.0.0.0:9090
```

The WebSocket port is bound directly on the host, using `websocket_port` (9090 by default).

The WebSocket API has no built-in authentication or TLS. Keep the Home Assistant host and this port on a trusted local network and do not expose it directly to the Internet. If another service already uses the selected port on the host, choose a different `websocket_port`.

For Spotify Connect discovery to work, the network must allow mDNS multicast (UDP port 5353) between the Home Assistant host and the clients. Host networking cannot bypass multicast filtering by a router, VLAN, or Wi-Fi access point.

## Home Assistant integration

Because the app uses host networking, the integration should connect to the Home Assistant host's LAN IP address or a hostname that resolves to that address, using the configured WebSocket port. The old app-only hostname `local-spotify-soloist` is not available in host network mode. Remove and add the integration again with the host address after updating the app.

## Persistent files

```text
/data/soloist/
├── soloist       # downloaded Spotify Soloist executable
├── data/         # persistent device/session state
└── cache/        # playback cache
```

Deleting `/data/soloist/data` resets the stored Spotify Soloist device/session state.

## Supported architectures

| Home Assistant architecture | Linux architecture | Spotify archive |
|---|---|---|
| `amd64` | `x86_64` | `soloist_release_x86_64.tar.gz` |
| `aarch64` | `aarch64` | `soloist_release_arm64.tar.gz` |
| `armv7` | `armv7l` | `soloist_release_arm32.tar.gz` |

## License

The wrapper code in this repository is licensed under the MIT License. Spotify Soloist is Spotify software and is downloaded directly from Spotify at runtime; see Spotify's terms and third-party license notices for Soloist.
