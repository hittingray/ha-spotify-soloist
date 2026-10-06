# Spotify Soloist

## Configuration

### Device name

The Spotify Connect device name advertised by Soloist.

### API key

Your Spotify Soloist API key from Spotify for Developers. Treat this as a secret and do not commit it to source control.

### WebSocket port

The TCP port used by Soloist's local WebSocket API. The default is `9090`.

### Initial volume

Initial volume from `0` to `100`.

## First startup

The first startup downloads Spotify Soloist from Spotify's official CDN. The download happens inside the running container and is stored in `/data/soloist/soloist`.

No Spotify Soloist binary is included in the Docker image or repository.

## Updates

Spotify Soloist builds expire after 90 days. At startup, this app runs:

```text
soloist --version
```

and uses the reported build timestamp to refresh a build when it reaches 76 days of age, providing a 14-day safety margin.

If the timestamp cannot be parsed, the existing binary is retained. Spotify Soloist itself exits with code `10` when its build has expired.

## Audio

The app declares `audio: true`, allowing Home Assistant to provide its internal PulseAudio setup to the container. Spotify Soloist can use PipeWire or PulseAudio.

## WebSocket security

The WebSocket server is bound to `0.0.0.0` because the port is explicitly exposed by the Home Assistant app. Spotify documents this API as a local integration surface and it does not provide client authentication, authorization, TLS, Origin validation, or other browser-facing security controls. Do not expose this port to an untrusted network.
