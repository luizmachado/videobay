#!/usr/bin/env bash
# Usage: install_videobay_gui_binary_by_git_sha.sh <git-sha> <built-binary-path>
set -euo pipefail
source "$(dirname "$0")/videobay_symlink_switch_functions.sh"

videobay_git_sha_to_install="$1"
videobay_built_binary_path="$2"

if [ ! -x "$videobay_built_binary_path" ]; then
  echo "Binary not found or not executable: $videobay_built_binary_path (run 'make binary' first)" >&2
  exit 1
fi

videobay_versioned_binary="$videobay_install_root_directory/$videobay_git_sha_to_install/videobay-gui"
mkdir -p "$(dirname "$videobay_versioned_binary")" "$videobay_install_state_directory"
install -m 0755 "$videobay_built_binary_path" "$videobay_versioned_binary"

videobay_currently_installed_sha="$(read_videobay_recorded_git_sha current_sha)"
if [ -n "$videobay_currently_installed_sha" ] && [ "$videobay_currently_installed_sha" != "$videobay_git_sha_to_install" ]; then
  echo "$videobay_currently_installed_sha" > "$videobay_install_state_directory/previous_sha"
fi

switch_videobay_symlink_atomically "$videobay_versioned_binary"
echo "$videobay_git_sha_to_install" > "$videobay_install_state_directory/current_sha"
echo "Installed videobay-gui $videobay_git_sha_to_install -> $videobay_user_binary_symlink"
