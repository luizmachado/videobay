#!/usr/bin/env bash
# Usage: fetch_pinned_deno_executable.sh <version> <zip-sha256> <target-directory>
# PROVENANCE: ADR-0008. The checksum is pinned in the Makefile; a mismatch aborts the build.
set -euo pipefail
pinned_deno_version="$1"
pinned_deno_zip_sha256="$2"
deno_target_directory="$3"
deno_release_zip_url="https://github.com/denoland/deno/releases/download/v${pinned_deno_version}/deno-x86_64-unknown-linux-gnu.zip"
downloaded_deno_zip="$(mktemp --suffix=.zip)"
trap 'rm -f "$downloaded_deno_zip"' EXIT

curl --fail --location --silent --show-error --output "$downloaded_deno_zip" "$deno_release_zip_url"
echo "${pinned_deno_zip_sha256}  ${downloaded_deno_zip}" | sha256sum --check --quiet
mkdir -p "$deno_target_directory"
python3 -m zipfile -e "$downloaded_deno_zip" "$deno_target_directory"
chmod 0755 "$deno_target_directory/deno"
echo "Fetched deno ${pinned_deno_version} -> $deno_target_directory/deno"
