#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
frames_dir="$(mktemp -d /tmp/bga-title-tray-motion.XXXXXX)"
trap 'rm -rf -- "$frames_dir"' EXIT

printf 'Rendering Blender frames in %s\n' "$frames_dir"
if ! blender -b --factory-startup --python "$root_dir/render_motion.py" -- \
    --output-dir "$frames_dir" >"$frames_dir/render.log" 2>&1; then
  tail -n 60 "$frames_dir/render.log" >&2
  exit 1
fi

ffmpeg -y -hide_banner -loglevel error -framerate 30 -start_number 1 \
  -i "$frames_dir/frame_%04d.png" -frames:v 660 \
  -vf scale=1280:720:flags=lanczos -c:v libvpx-vp9 -pix_fmt yuva420p \
  -crf 22 -b:v 0 -auto-alt-ref 0 -deadline good -cpu-used 5 \
  "$frames_dir/motion-pass.webm"

cp "$frames_dir/motion-pass.webm" "$root_dir/motion-pass.webm"
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name:stream_tags=alpha_mode \
  -of default=noprint_wrappers=1 "$root_dir/motion-pass.webm"
