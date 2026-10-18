#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
output_file="$root_dir/bga-title-tray-demo.mp4"
poster_file="$root_dir/bga-title-tray-demo-poster.jpg"

python3 "$root_dir/render_video.py" --output "$output_file"
ffmpeg -y -hide_banner -loglevel error -ss 8.2 -i "$output_file" \
  -frames:v 1 -q:v 2 "$poster_file"
printf '%s\n%s\n' "$output_file" "$poster_file"
