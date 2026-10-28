#!/usr/bin/env bash
# WHY: the line limit keeps every file readable in a single agent read (CLAUDE.md, clean code rules).
set -euo pipefail
max_lines_per_videobay_source_file="${1:-300}"
oversized_videobay_source_files=$(git ls-files -co --exclude-standard -- 'src/*.py' 'tests/*.py' | xargs -r wc -l | awk -v max="$max_lines_per_videobay_source_file" '$2 != "total" && $1 > max')
if [ -n "$oversized_videobay_source_files" ]; then
  echo "Files above $max_lines_per_videobay_source_file lines:"; echo "$oversized_videobay_source_files"; exit 1
fi
echo "File length OK (<= $max_lines_per_videobay_source_file lines)"
