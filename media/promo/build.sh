#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
normal_frame="$root_dir/source/panel-normal.png"
flash_frame="$root_dir/source/panel-flash.png"
browser_frame="$root_dir/source/bga-browser-crop.png"
cursor_frame="$root_dir/source/click-cursor.png"
click_ring="$root_dir/source/click-ring.png"
motion_file="$root_dir/motion-pass.webm"
output_file="$root_dir/bga-title-tray-demo.mp4"
poster_file="$root_dir/bga-title-tray-demo-poster.jpg"
font_bold="/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
font_regular="/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"

for required in "$normal_frame" "$flash_frame" "$browser_frame" "$cursor_frame" "$click_ring" "$motion_file" "$font_bold" "$font_regular"; do
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
drawtext=fontfile=$font_regular:text='Illustrative countdown; no tab watching needed.':fontsize=28:fontcolor=0xc8c0b8:x=90:y=275:enable='between(t,3,6)',
drawtext=fontfile=$font_bold:text='An alert you can actually notice.':fontsize=50:fontcolor=0xf5f0e8:x=90:y=185:enable='between(t,6,10)',
drawtext=fontfile=$font_regular:text='The Play alert catches your eye.':fontsize=27:fontcolor=0xc8c0b8:x=90:y=275:enable='between(t,6,10)',
drawtext=fontfile=$font_bold:text='One click takes you back.':fontsize=55:fontcolor=0xf5f0e8:x=90:y=185:enable='between(t,10,14)',
drawtext=fontfile=$font_regular:text='No window or tab hunting.':fontsize=28:fontcolor=0xc8c0b8:x=90:y=275:enable='between(t,10,14)',
drawtext=fontfile=$font_bold:text='Stay in the game.':fontsize=59:fontcolor=0xf5f0e8:x=90:y=180:enable='between(t,14,18)',
drawtext=fontfile=$font_regular:text='A turn alert stays in sight while you browse.':fontsize=27:fontcolor=0xc8c0b8:x=90:y=275:enable='between(t,14,18)',
drawtext=fontfile=$font_bold:text='Click the panel title.':fontsize=55:fontcolor=0xf5f0e8:x=90:y=180:enable='between(t,18,19.2)',
drawtext=fontfile=$font_regular:text='BGA comes back to you.':fontsize=28:fontcolor=0xc8c0b8:x=90:y=275:enable='between(t,18,19.2)',
drawtext=fontfile=$font_bold:text='indri.studio/apps/bga-title-tray':fontsize=30:fontcolor=0xb8ef00:x=90:y=565:enable='between(t,14,19.2)',
drawtext=fontfile=$font_regular:text='Independent companion for Board Game Arena':fontsize=20:fontcolor=0x9f9991:x=90:y=670[base];
[1:v]scale=944:86:flags=lanczos,format=rgba[normal];
[2:v]scale=944:86:flags=lanczos,format=rgba[flash];
[3:v]scale=1280:653:flags=lanczos,pad=1280:720:0:33:color=0x171614[browser];
[4:v]format=rgba[cursor];
[5:v]format=rgba[click_ring];
[6:v]format=yuva420p[motion];
[base][normal]overlay=x=168:y=389:enable='gte(t,3)',
drawbox=x=178:y=402:w=578:h=61:color=0x050505:t=fill:enable='gte(t,3)'[clean_panel];
[clean_panel][flash]overlay=x=168:y=389:enable='between(t,6,10)*lt(mod(t-6,1),0.5)+between(t,14,18)*lt(mod(t-14,1),0.5)'[with_flash];
[with_flash]drawbox=x=178:y=402:w=578:h=61:color=white:t=fill:enable='between(t,6,10)*lt(mod(t-6,1),0.5)+between(t,14,18)*lt(mod(t-14,1),0.5)',
drawtext=fontfile=$font_regular:text='Searching for 3 player(s)... • Board Game Arena':fontsize=22:fontcolor=white:x=195:y=416:enable='between(t,3,3.75)',
drawtext=fontfile=$font_regular:text='Searching for 2 player(s)... • Board Game Arena':fontsize=22:fontcolor=white:x=195:y=416:enable='between(t,3.75,4.5)',
drawtext=fontfile=$font_regular:text='Searching for 1 player(s)... • Board Game Arena':fontsize=22:fontcolor=white:x=195:y=416:enable='between(t,4.5,5.25)',
drawtext=fontfile=$font_regular:text='Searching for 0 player(s)... • Board Game Arena':fontsize=22:fontcolor=white:x=195:y=416:enable='between(t,5.25,6)',
drawtext=fontfile=$font_regular:text='Play • Board Game Arena':fontsize=22:fontcolor=white:x=195:y=416:enable='between(t,6,10)*gte(mod(t-6,1),0.5)+between(t,10,14)',
drawtext=fontfile=$font_regular:text='Play • Board Game Arena':fontsize=22:fontcolor=black:x=195:y=416:enable='between(t,6,10)*lt(mod(t-6,1),0.5)',
drawtext=fontfile=$font_regular:text='You must make your move • Board Game Arena':fontsize=20:fontcolor=white:x=195:y=416:enable='between(t,14,18)*gte(mod(t-14,1),0.5)+between(t,18,19.2)',
drawtext=fontfile=$font_regular:text='You must make your move • Board Game Arena':fontsize=20:fontcolor=black:x=195:y=416:enable='between(t,14,18)*lt(mod(t-14,1),0.5)'[panel_titles];
[panel_titles][click_ring]overlay=x=367:y=392:enable='between(t,18.6,18.9)'[with_click];
[with_click][cursor]overlay=x='if(lt(t,18.6),820-(t-18)*700,400)':y='if(lt(t,18.6),555-(t-18)*208,430)':enable='between(t,18,19.2)'[with_cursor];
[with_cursor][browser]overlay=x=0:y=0:enable='gte(t,19.2)',
drawtext=fontfile=$font_regular:text='Back to the BGA tab.':fontsize=24:fontcolor=0xb8ef00:x=90:y=690:enable='gte(t,19.2)'[picture];
[picture][motion]overlay=x=0:y=0:format=auto,format=yuv420p[out]
EOF

ffmpeg -y -hide_banner -loglevel error \
  -f lavfi -i "color=c=0x2a2723:s=1280x720:r=30:d=22" \
  -loop 1 -framerate 30 -i "$normal_frame" \
  -loop 1 -framerate 30 -i "$flash_frame" \
  -loop 1 -framerate 30 -i "$browser_frame" \
  -loop 1 -framerate 30 -i "$cursor_frame" \
  -loop 1 -framerate 30 -i "$click_ring" \
  -c:v libvpx-vp9 -i "$motion_file" \
  -filter_complex_script "$filter_script" -map '[out]' \
  -t 22 -an -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p \
  -movflags +faststart -metadata title='Board Game Arena Title Tray demo' \
  -metadata comment='Real installed panel frames with illustrative titles and Blender motion; click cuts to Will-provided BGA welcome screenshot. Not a live offer.' \
  "$output_file"

ffmpeg -y -hide_banner -loglevel error -ss 7 -i "$output_file" -frames:v 1 -q:v 2 "$poster_file"
printf '%s\n%s\n' "$output_file" "$poster_file"
