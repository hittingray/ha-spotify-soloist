# Spotify Soloist Home Assistant integration

This custom integration connects Home Assistant to the Spotify Soloist app over its WebSocket API.

## Connection

Use the Home Assistant host's LAN IP address or a hostname that resolves to it, with port `9090` by default.

The app uses host networking so Spotify Connect's mDNS discovery is visible on the local network. Its internal app hostname is not available in this mode. Re-add an existing integration with the Home Assistant host address after updating the app.
