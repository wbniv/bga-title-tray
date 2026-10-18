"""Render the silent 22-second BGA Title Tray product film.

The window cards and searching/alert titles are illustrations. The tray pixels
and final BGA browser frame come from the supplied captures. Run with:

  python3 render_video.py --still 5.2 --output /tmp/preview.png
  python3 render_video.py --output bga-title-tray-demo.mp4
"""

import argparse
import math
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(__file__).resolve().parent
W, H, FPS, DURATION = 1280, 720, 30, 22
INK = "#151515"
PAPER = "#f5f0e8"
LIME = "#b8ef00"
MUTED = "#b9b6ae"
FONT = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
normal = Image.open(ROOT / "source/panel-normal.png").convert("RGBA")
flash = Image.open(ROOT / "source/panel-flash.png").convert("RGBA")
browser = Image.open(ROOT / "source/bga-browser-crop.png").convert("RGBA")
cursor = Image.open(ROOT / "source/click-cursor.png").convert("RGBA")


def clamp(value, low=0, high=1):
    return max(low, min(high, value))


def ease(value):
    x = clamp(value)
    return 1 - (1 - x) ** 3


def smooth(value):
    x = clamp(value)
    return x * x * (3 - 2 * x)


def mix(a, b, value):
    return a + (b - a) * value


@lru_cache(maxsize=32)
def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def text(draw, xy, value, size, color=PAPER, bold=False, anchor=None):
    draw.text(xy, value, font=font(size, bold), fill=color, anchor=anchor,
              stroke_width=0)


def box(draw, rect, fill, radius=0, outline=None, width=1):
    draw.rounded_rectangle(tuple(int(v) for v in rect), radius=radius,
                           fill=fill, outline=outline, width=width)


def paste_scaled(canvas, source, rect, opacity=1):
    x, y, width, height = (int(v) for v in rect)
    if width < 1 or height < 1 or opacity <= 0:
        return
    layer = source.resize((width, height), Image.Resampling.LANCZOS)
    if opacity < 1:
        layer.putalpha(layer.getchannel("A").point(lambda a: round(a * opacity)))
    canvas.alpha_composite(layer, (x, y))


def shadow(canvas, rect, radius=22, alpha=85):
    x, y, width, height = [int(v) for v in rect]
    layer = Image.new("RGBA", (W, H))
    draw = ImageDraw.Draw(layer)
    box(draw, (x + 6, y + 14, x + width + 6, y + height + 14),
        (0, 0, 0, alpha), radius)
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(23)))


def foundation():
    canvas = Image.new("RGBA", (W, H), "#171714")
    draw = ImageDraw.Draw(canvas)
    for y in range(H):
        shade = int(28 + 11 * y / H)
        draw.line((0, y, W, y), fill=(shade, shade - 1, shade - 4, 255))
    for x in range(0, W + 1, 160):
        draw.line((x, 0, x, H), fill="#30302c", width=1)
    for y in range(0, H + 1, 160):
        draw.line((0, y, W, y), fill="#30302c", width=1)
    box(draw, (0, 0, W, 10), LIME)
    return canvas


def brand(draw, section):
    text(draw, (66, 37), "INDRI", 27, LIME, True)
    text(draw, (174, 44), "BOARD GAME ARENA TITLE TRAY", 17, MUTED, True)
    text(draw, (1212, 42), section, 15, MUTED, anchor="ra")


def caption(draw, heading, sub, x=66, y=92, heading_size=55):
    text(draw, (x, y), heading, heading_size, PAPER, True)
    text(draw, (x, y + heading_size + 22), sub, 24, MUTED)


def tray(canvas, x, y, width, title, white=False, opacity=1):
    height = round(width * 54 / 590)
    base = (flash if white else normal).resize((width, height),
                                               Image.Resampling.LANCZOS)
    # The original panel text is replaced with an explicitly illustrative
    # title, leaving the captured widget and desktop tray icons intact.
    draw = ImageDraw.Draw(base)
    text_width = round(width * 365 / 590)
    box(draw, (0, 0, text_width, height), PAPER if white else "#050505")
    title_size = round(width * 12 / 590)
    text(draw, (round(width * 16 / 590), round(height * .28)), title,
         max(12, title_size), INK if white else PAPER)
    paste_scaled(canvas, base, (x, y, width, height), opacity)
    return height


def window(canvas, rect, label, kind="work", opacity=1):
    x, y, width, height = [int(v) for v in rect]
    shadow(canvas, rect, 18)
    layer = Image.new("RGBA", (width, height))
    d = ImageDraw.Draw(layer)
    box(d, (0, 0, width - 1, height - 1), "#f1f0ec", 17)
    box(d, (0, 0, width - 1, 45), "#242524", 17)
    d.rectangle((0, 29, width - 1, 46), fill="#242524")
    for i, color in enumerate(("#d8d2c8", "#9d9991", "#66645e")):
        d.ellipse((16 + i * 19, 17, 26 + i * 19, 27), fill=color)
    text(d, (84, 12), label, 15, PAPER, True)
    if kind == "bga":
        box(d, (24, 70, width - 24, height - 26), "#e7edf1", 13)
        box(d, (42, 93, width - 42, 145), "#345a77", 8)
        text(d, (62, 104), "BOARD GAME ARENA", 29, PAPER, True)
        for i, color in enumerate(("#80a9bc", "#b5d1dc", "#6b93a5")):
            x0 = 43 + i * ((width - 102) // 3)
            box(d, (x0, 166, x0 + (width - 130) // 3, height - 51),
                color, 7)
        text(d, (48, height - 46), "Find a game  ·  Keep your place", 17,
             "#384e59")
    else:
        text(d, (37, 82), "Keep doing your thing.", 34, "#262626", True)
        for i, length in enumerate((.78, .62, .83, .49)):
            box(d, (38, 153 + i * 44, 38 + int((width - 78) * length),
                    168 + i * 44), "#b8bebd", 7)
        box(d, (38, height - 62, 216, height - 33), "#c3dfd3", 7)
    paste_scaled(canvas, layer, rect, opacity)


def overlay(canvas, opacity, color=(18, 18, 16)):
    if opacity <= 0:
        return
    layer = Image.new("RGBA", (W, H), (*color, int(255 * clamp(opacity))))
    canvas.alpha_composite(layer)


def draw_intro(canvas, t):
    d = ImageDraw.Draw(canvas)
    brand(d, "01 / THE PROBLEM")
    enter = ease(t / .65)
    text(d, (68 + int((1 - enter) * 70), 164), "A game can start", 69,
         PAPER, True)
    text(d, (68 + int((1 - ease((t - .32) / .65)) * 95), 249),
         "while you're elsewhere.", 69, PAPER, True)
    text(d, (72, 373), "Stay on top of the wait without watching a tab.",
         27, MUTED)
    travel = ease((t - 1.05) / .75)
    x = int(mix(1380, 175, travel))
    shadow(canvas, (x, 500, 930, 86), 7)
    tray(canvas, x, 500, 930, "Searching for 3 player(s)... • Board Game Arena")
    if t > 2.45:
        overlay(canvas, ease((t - 2.65) / .35))


def draw_wait(canvas, t):
    d = ImageDraw.Draw(canvas)
    brand(d, "02 / WAITING")
    caption(d, "Start a game. Then move on.",
            "The BGA status stays beside your system tray.", y=85)
    window(canvas, (70, 237, 670, 343), "Board Game Arena", "bga")
    p = ease((t - 3.8) / .8)
    window(canvas, (int(mix(1340, 426, p)), int(mix(245, 214, p)),
                    610, 335), "Another window", "work", p)
    # This is the scene transition: the active window covers BGA while the
    # actual tray capture remains in front and continues reporting the queue.
    count = max(0, 3 - int((t - 3) / .83))
    pulse = (t - 3) % .83
    count_y = int(336 - 28 * (1 - ease(pulse / .24)))
    box(d, (1040, 242, 1218, 431), "#272a26", 22)
    text(d, (1129, count_y), str(count), 115, LIME, True, "mm")
    text(d, (1129, 403), "SEARCHING", 17, MUTED, True, "mm")
    box(d, (69, 604, 1211, 690), "#0b0b0b", 8)
    tray(canvas, 160, 615, 950,
         f"Searching for {count} player(s)... • Board Game Arena")
    if t > 6.45:
        overlay(canvas, ease((t - 6.58) / .42))


def draw_play(canvas, t):
    d = ImageDraw.Draw(canvas)
    brand(d, "03 / READY")
    arrival = ease((t - 7) / .65)
    headline_y = int(mix(203, 128, arrival))
    text(d, (64, headline_y), "GAME READY.", 92, PAPER, True)
    text(d, (67, headline_y + 121), "A visible Play alert pulls you back in.",
         28, MUTED)
    # Large panel motion carries the status change instead of an ornamental
    # border. It lands, settles, then holds through the readable flash cycle.
    scale = mix(.68, 1.0, arrival) + .045 * math.sin(clamp((t - 7) / .8) * math.pi)
    width = int(1070 * scale)
    x = (W - width) // 2
    y = int(mix(520, 387, arrival))
    shadow(canvas, (x, y, width, width * 54 / 590), 8, 130)
    tray(canvas, x, y, width, "Play • Board Game Arena",
         white=t >= 7.7 and (t - 7.7) % 1 < .5)
    text(d, (66, 603), "The wait ends. The tray tells you.", 25, LIME, True)
    if t > 10.55:
        overlay(canvas, ease((t - 10.65) / .35))


def draw_context(canvas, t, move=False):
    d = ImageDraw.Draw(canvas)
    brand(d, "04 / IN THE GAME" if move else "04 / ONE CLICK")
    caption(d, "Your move." if move else "BGA stays one click away.",
            "Even when another window is in front." if move
            else "No window or tab hunting.", y=84)
    window(canvas, (75, 248, 710, 340), "Board Game Arena", "bga")
    slide = ease((t - (15 if move else 11)) / .7)
    window(canvas, (int(mix(1350, 448, slide)), 218, 718, 350),
           "Another window", "work", slide)
    box(d, (63, 600, 1217, 686), "#050505", 9)
    title = ("You must make your move • Board Game Arena"
             if move else "Play • Board Game Arena")
    white = move and t >= 15.6 and (t - 15.6) % 1 < .5
    tray(canvas, 167, 612, 944, title, white)
    if move:
        text(d, (67, 198), "The alert stays visible until you return.",
             24, LIME)
    if t > (18.2 if move else 14.55):
        overlay(canvas, ease((t - (18.3 if move else 14.65)) / .35))


def draw_finish(canvas, t):
    d = ImageDraw.Draw(canvas)
    brand(d, "05 / BACK TO BGA")
    if t < 19.1:
        caption(d, "Click the tray title.", "BGA comes back to you.", y=100)
        window(canvas, (83, 245, 725, 337), "Board Game Arena", "bga")
        window(canvas, (422, 225, 735, 349), "Another window", "work")
        box(d, (60, 602, 1219, 690), "#050505", 9)
        tray(canvas, 166, 614, 948,
             "You must make your move • Board Game Arena")
        p = ease((t - 18.55) / .5)
        paste_scaled(canvas, cursor, (int(mix(970, 560, p)),
                                      int(mix(560, 625, p)), 50, 65))
        if t >= 19:
            radius = int(12 + 65 * ease((t - 19) / .15))
            d.ellipse((560 - radius, 625 - radius, 560 + radius,
                       625 + radius), outline=LIME, width=5)
        return
    # The actual BGA screenshot grows from the background window into the
    # foreground, making the click-to-focus result spatially explicit.
    p = ease((t - 19.1) / .85)
    scale = mix(.56, 1.0, p)
    width = int(W * scale)
    height = int(653 * scale)
    x = int(mix(100, 0, p))
    y = int(mix(235, 0, p))
    shadow(canvas, (x, y, width, height), 10)
    paste_scaled(canvas, browser, (x, y, width, height))
    if t >= 20:
        box(d, (0, 654, W, H), "#191919")
        text(d, (62, 669), "YOUR GAME, RIGHT WHERE YOU LEFT IT.", 23,
             PAPER, True)
        text(d, (1217, 670), "indri.studio/apps/bga-title-tray", 17, LIME,
             anchor="ra")


def render(t):
    canvas = foundation()
    if t < 3:
        draw_intro(canvas, t)
    elif t < 7:
        draw_wait(canvas, t)
    elif t < 11:
        draw_play(canvas, t)
    elif t < 15:
        draw_context(canvas, t)
    elif t < 18.5:
        draw_context(canvas, t, move=True)
    else:
        draw_finish(canvas, t)
    return canvas.convert("RGB")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--still", type=float)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.still is not None:
        render(args.still).save(args.output)
        return
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size",
        f"{W}x{H}", "-framerate", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-metadata", "title=Board Game Arena Title Tray demo",
        "-metadata", "comment=Captured tray and browser with illustrative window cards and titles",
        str(args.output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for frame in range(FPS * DURATION):
            process.stdin.write(render(frame / FPS).tobytes())
            if frame % 150 == 0:
                print(f"Rendered {frame}/{FPS * DURATION} frames", flush=True)
    finally:
        process.stdin.close()
    if process.wait() != 0:
        raise SystemExit("FFmpeg encode failed")


if __name__ == "__main__":
    main()
