# Spotify Soloist Home Assistant integration

This custom integration connects Home Assistant to the Spotify Soloist app over its WebSocket API.

## Default connection

The default host is:

`local-spotify-soloist`

This is Home Assistant's internal DNS hostname for an app installed from the local app repository when the app slug is `spotify_soloist`. Home Assistant generates app names as `{repository}_{slug}` and DNS names by replacing underscores with hyphens.

If the app is installed from a GitHub repository rather than the local repository, Home Assistant uses a repository-specific identifier. In that case, enter the generated app hostname during integration setup.

The default WebSocket port is `9090`.
