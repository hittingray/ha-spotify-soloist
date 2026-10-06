#!/usr/bin/env bash

set -Eeuo pipefail

CONFIG="/data/options.json"
SOLOIST_ROOT="/data/soloist"
SOLOIST_BIN="${SOLOIST_ROOT}/soloist"
SOLOIST_DATA="${SOLOIST_ROOT}/data"
SOLOIST_CACHE="${SOLOIST_ROOT}/cache"
DOWNLOAD_BASE="https://soloist-builds.spotifycdn.com"

# Spotify Soloist builds are valid for 90 days. Refresh two weeks before expiry.
BUILD_LIFETIME_DAYS=90
REFRESH_THRESHOLD_DAYS=14
REFRESH_AFTER_DAYS=$((BUILD_LIFETIME_DAYS - REFRESH_THRESHOLD_DAYS))

log() {
    echo "[spotify-soloist] $*"
}

fatal() {
    echo "[spotify-soloist] ERROR: $*" >&2
    exit 1
}

detect_architecture() {
    case "$(uname -m)" in
        x86_64)
            SOLOIST_ARCH="x86_64"
            SOLOIST_ARCHIVE="soloist_release_x86_64.tar.gz"
            ;;
        aarch64|arm64)
            SOLOIST_ARCH="aarch64"
            SOLOIST_ARCHIVE="soloist_release_arm64.tar.gz"
            ;;
        armv7l|armv7)
            SOLOIST_ARCH="armv7l"
            SOLOIST_ARCHIVE="soloist_release_arm32.tar.gz"
            ;;
        *)
            fatal "Unsupported architecture: $(uname -m)"
            ;;
    esac

    log "Detected architecture: ${SOLOIST_ARCH}"
}

download_soloist() {
    local archive_url="${DOWNLOAD_BASE}/${SOLOIST_ARCHIVE}"
    local temp_dir archive extracted

    temp_dir="$(mktemp -d)"
    archive="${temp_dir}/${SOLOIST_ARCHIVE}"
    extracted="${temp_dir}/soloist"

    cleanup_download() {
        trap - RETURN
        rm -rf "${temp_dir}"
    }
    trap cleanup_download RETURN

    log "Downloading Spotify Soloist for ${SOLOIST_ARCH}..."

    curl \
        --fail \
        --show-error \
        --location \
        --retry 3 \
        --retry-delay 2 \
        --output "${archive}" \
        "${archive_url}"

    tar \
        --extract \
        --gzip \
        --file "${archive}" \
        --directory "${temp_dir}"

    [[ -f "${extracted}" ]] || \
        fatal "Downloaded archive did not contain a soloist executable"

    chmod 0755 "${extracted}"

    # Atomic replacement prevents a failed update from destroying a working binary.
    install -m 0755 "${extracted}" "${SOLOIST_BIN}.new"
    mv -f "${SOLOIST_BIN}.new" "${SOLOIST_BIN}"

    log "Spotify Soloist installed at ${SOLOIST_BIN}."
}

get_version() {
    "${SOLOIST_BIN}" --version 2>&1
}

build_is_expiring() {
    local version_output
    local build_epoch
    local now_epoch
    local age_days

    version_output="$(get_version)" || {
        log "Unable to execute soloist --version."
        return 0
    }

    log "Installed Soloist:"
    echo "${version_output}"

    # Expected format:
    #
    # soloist 1.3.7.517 build 1788242495 (20260901) (gb24005ef46) (linux/x86_64)
    #
    # The build number is a Unix epoch timestamp.
    build_epoch="$(
        printf '%s\n' "${version_output}" |
        sed -nE 's/.*build ([0-9]+) .*/\1/p'
    )"

    if [[ -z "${build_epoch}" ]]; then
        log "Could not extract Soloist build epoch from --version."
        log "Expected format: ... build <epoch> (YYYYMMDD) ..."
        log "Keeping existing Soloist build."
        return 1
    fi

    now_epoch="$(date +%s)"

    # A future build timestamp should trigger a refresh.
    if (( build_epoch > now_epoch )); then
        log "Soloist build timestamp is in the future: ${build_epoch}"
        return 0
    fi

    age_days=$(( (now_epoch - build_epoch) / 86400 ))

    log "Soloist build epoch: ${build_epoch}"
    log "Soloist build age: ${age_days} days"

    if (( age_days >= REFRESH_AFTER_DAYS )); then
        log "Soloist build is approaching its 90-day expiry."
        return 0
    fi

    return 1
}

ensure_soloist() {
    mkdir -p "${SOLOIST_ROOT}" "${SOLOIST_DATA}" "${SOLOIST_CACHE}"

    if [[ ! -x "${SOLOIST_BIN}" ]]; then
        log "No cached Spotify Soloist binary found."
        download_soloist
        return
    fi

    if build_is_expiring; then
        log "Refreshing Spotify Soloist."
        download_soloist
    else
        log "Cached Spotify Soloist build is current."
    fi
}

read_config() {
    [[ -f "${CONFIG}" ]] || fatal "Missing ${CONFIG}"

    DEVICE_NAME="$(jq -r '.device_name' "${CONFIG}")"
    API_KEY="$(jq -r '.api_key' "${CONFIG}")"
    WS_PORT="$(jq -r '.websocket_port' "${CONFIG}")"
    INITIAL_VOLUME="$(jq -r '.initial_volume' "${CONFIG}")"

    [[ -n "${DEVICE_NAME}" && "${DEVICE_NAME}" != "null" ]] || fatal "device_name is required"
    [[ -n "${API_KEY}" && "${API_KEY}" != "null" ]] || fatal "api_key is required"

    log "Device name: ${DEVICE_NAME}"
    log "WebSocket port: ${WS_PORT}"
}

start_soloist() {
    log "Starting Spotify Soloist..."

    # Docker/Supervisor provides the init process because config.yaml has
    # init: true. exec makes Soloist the direct child of that init process.
    exec "${SOLOIST_BIN}" \
        --device-name "${DEVICE_NAME}" \
        --api-key "${API_KEY}" \
        --data-dir "${SOLOIST_DATA}" \
        --cache-dir "${SOLOIST_CACHE}" \
        --initial-volume "${INITIAL_VOLUME}" \
        --ws "0.0.0.0:${WS_PORT}"
}

detect_architecture
read_config
ensure_soloist
start_soloist
