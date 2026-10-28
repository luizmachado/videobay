#!/usr/bin/env bash
# Swaps current and previous installs; running it twice rolls forward again.
set -euo pipefail
source "$(dirname "$0")/videobay_symlink_switch_functions.sh"

videobay_previous_installed_sha="$(read_videobay_recorded_git_sha previous_sha)"
videobay_currently_installed_sha="$(read_videobay_recorded_git_sha current_sha)"
videobay_previous_binary="$videobay_install_root_directory/$videobay_previous_installed_sha/videobay-gui"

if [ -z "$videobay_previous_installed_sha" ] || [ ! -x "$videobay_previous_binary" ]; then
  echo "No previous videobay-gui install to roll back to" >&2
  exit 1
fi

switch_videobay_symlink_atomically "$videobay_previous_binary"
echo "$videobay_previous_installed_sha" > "$videobay_install_state_directory/current_sha"
echo "$videobay_currently_installed_sha" > "$videobay_install_state_directory/previous_sha"
echo "Rolled back videobay-gui to $videobay_previous_installed_sha"
