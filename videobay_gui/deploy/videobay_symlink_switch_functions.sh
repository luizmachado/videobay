# Shared by the install and rollback scripts (ADR-0005). Sourced, never executed directly.
videobay_install_root_directory="${XDG_DATA_HOME:-$HOME/.local/share}/videobay"
videobay_install_state_directory="${XDG_STATE_HOME:-$HOME/.local/state}/videobay"
videobay_user_binary_symlink="$HOME/.local/bin/videobay-gui"

switch_videobay_symlink_atomically() {
  local videobay_symlink_target_binary="$1"
  local videobay_temporary_symlink="${videobay_user_binary_symlink}.switching.$$"
  mkdir -p "$(dirname "$videobay_user_binary_symlink")"
  # WHY: rename(2) via `mv -T` swaps the link in one syscall; `ln -sfn` alone unlinks first and leaves a gap.
  ln -sfn "$videobay_symlink_target_binary" "$videobay_temporary_symlink"
  mv -T "$videobay_temporary_symlink" "$videobay_user_binary_symlink"
}

read_videobay_recorded_git_sha() {
  local videobay_sha_record_name="$1"
  cat "$videobay_install_state_directory/$videobay_sha_record_name" 2>/dev/null || true
}
