#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
normal_frame="$root_dir/source/panel-normal.png"
flash_frame="$root_dir/source/panel-flash.png"
output_file="$root_dir/bga-title-tray-demo.mp4"
poster_file="$root_dir/bga-title-tray-demo-poster.jpg"
font_bold="/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
font_regular="/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"

for required in "$normal_frame" "$flash_frame" "$font_bold" "$font_regular"; do
  test -f "$required"
done

filter_script="$root_dir/filter.ffmpeg"
cat > "$filter_script" <<EOF
[0:v]format=rgba,
drawbox=x=0:y=0:w=1280:h=12:color=0xb8ef00:t=fill,
drawbox=x=0:y=650:w=1280:h=1:color=0x56514b:t=fill,
drawbox=x=134:y=350:w=1012:h=166:color=0x171614:t=fill:enable='gte(t,3)',
drawbox=x=134:y=350:w=1012:h=2:color=0x77716a:t=fill:enable='gte(t,3)',
drawtext=fontfile=$font_bold:text='INDRI':fontsize=30:fontcolor=0xb8ef00:x=90:y=52,
drawtext=fontfile=$font_regular:text='BOARD GAME ARENA TITLE TRAY':fontsize=21:fontcolor=0xc8c0b8:x=205:y=59,
drawtext=fontfile=$font_bold:text='Never miss your next move.':fontsize=58:fontcolor=0xf5f0e8:x=90:y=222:enable='lt(t,3)',
drawtext=fontfile=$font_regular:text='A small KDE panel companion for BGA.':fontsize=30:fontcolor=0xc8c0b8:x=90:y=316:enable='lt(t,3)',
drawtext=fontfile=$font_bold:text='Your game stays in sight.':fontsize=55:fontcolor=0xf5f0e8:x=90:y=185:enable='between(t,3,6)',
drawtext=fontfile=$font_regular:text='The tab title lives beside the system tray.':fontsize=28:fontcolor=0xc8c0b8:x=90:y=275:enable='between(t,3,6)',
drawtext=fontfile=$font_bold:text='An alert you can actually notice.':fontsize=50:fontcolor=0xf5f0e8:x=90:y=185:enable='between(t,6,10)',
drawtext=fontfile=$font_regular:text='Real panel frames; flash slowed for clarity.':fontsize=27:fontcolor=0xc8c0b8:x=90:y=275:enable='between(t,6,10)',
drawtext=fontfile=$font_bold:text='One click takes you back.':fontsize=55:fontcolor=0xf5f0e8:x=90:y=185:enable='between(t,10,14)',
drawtext=fontfile=$font_regular:text='No window or tab hunting.':fontsize=28:fontcolor=0xc8c0b8:x=90:y=275:enable='between(t,10,14)',
drawtext=fontfile=$font_bold:text='Stay in the game.':fontsize=59:fontcolor=0xf5f0e8:x=90:y=180:enable='gte(t,14)',
drawtext=fontfile=$font_regular:text='Linux  /  KDE Plasma 6  /  Chrome or Chromium':fontsize=27:fontcolor=0xc8c0b8:x=90:y=275:enable='gte(t,14)',
drawtext=fontfile=$font_bold:text='indri.studio/apps/bga-title-tray':fontsize=30:fontcolor=0xb8ef00:x=90:y=565:enable='gte(t,14)',
drawtext=fontfile=$font_regular:text='Independent companion for Board Game Arena':fontsize=20:fontcolor=0x9f9991:x=90:y=670[base];
[1:v]scale=944:86:flags=lanczos,format=rgba[normal];
[2:v]scale=944:86:flags=lanczos,format=rgba[flash];
[base][normal]overlay=x=168:y=389:enable='gte(t,3)'[with_panel];
[with_panel][flash]overlay=x=168:y=389:enable='between(t,6,9.5)*lt(mod(t-6,1),0.5)',format=yuv420p[out]
EOF

ffmpeg -y -hide_banner -loglevel error \
  -f lavfi -i "color=c=0x2a2723:s=1280x720:r=30:d=18" \
  -loop 1 -framerate 30 -i "$normal_frame" \
  -loop 1 -framerate 30 -i "$flash_frame" \
  -filter_complex_script "$filter_script" -map '[out]' \
  -t 18 -an -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p \
  -movflags +faststart -metadata title='Board Game Arena Title Tray demo' \
  -metadata comment='Real installed panel frames; manual flash preview slowed for clarity, not a live offer.' \
  "$output_file"

ffmpeg -y -hide_banner -loglevel error -ss 7 -i "$output_file" -frames:v 1 -q:v 2 "$poster_file"
printf '%s\n%s\n' "$output_file" "$poster_file"
