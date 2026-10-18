# BGA Title Tray video

## Goal

Show the everyday use case: Will can start matchmaking, switch to another window, and keep the BGA waiting status visible in the KDE panel instead of watching the browser tab. When a game is ready, the panel alerts him; clicking its title brings the existing BGA window and tab to the front, without hunting through windows and tabs. Use a short, silent, captioned video on the Indri product page. The panel frames came from version 0.4.7 on Will's desktop, while the 3 → 2 → 1 → 0 searching titles, Play alert, generic move alert, and pointer click are composited illustrations. The final frame uses Will's one-tab BGA browser screenshot. The sequence is not a recording of one live game. The edit holds each flash state for 0.5 seconds; the installed widget retains its 0.1-second flash timing.

## Storyboard

The frame is 1280 × 720, with Indri's dark surface, lime accent, readable cream captions, a captured KDE panel strip, and a final BGA browser frame. These screen mockups show the current cut:

```text
0–3 s  ┌──────────────────────────────────────────────┐
       │ INDRI  /  BOARD GAME ARENA TITLE TRAY        │
       │                                              │
       │ Waiting for a game? Keep doing your thing.  │
       │ BGA stays visible beside the system tray.    │
       └──────────────────────────────────────────────┘

3–6 s ┌──────────────────────────────────────────────┐
       │ Your game stays in sight.                    │
       │ Illustrative queue countdown                │
       │ [panel: Searching for 3 → 2 → 1 → 0]         │
       └──────────────────────────────────────────────┘

6–10s ┌──────────────────────────────────────────────┐
       │ An alert you can actually notice.            │
       │ [Play • Board Game Arena flashes]            │
       │ The Play alert catches your eye.             │
       └──────────────────────────────────────────────┘

10–14s┌──────────────────────────────────────────────┐
       │ One click brings BGA to you.                 │
       │ [other window in front]                      │
       │ [panel title] ← pointer clicks               │
       │       ↓ existing BGA window and tab appear   │
       └──────────────────────────────────────────────┘

14–18s┌──────────────────────────────────────────────┐
       │ Stay in the game.                            │
       │ [You must make your move • BGA flashes]      │
       │ Turn alert stays in sight while you browse.  │
       └──────────────────────────────────────────────┘

18–22s┌──────────────────────────────────────────────┐
       │ [pointer clicks panel title]                 │
       │             ↓ cut                            │
       │ [BGA open in the single-tab browser shot]    │
       │ Back to the BGA tab.                         │
       └──────────────────────────────────────────────┘
```

## Viewer flow

```text
Product page
┌───────────────────────────────────────────────────────┐
│ Video poster: Play title on real panel                 │
│ Large centered Play button                             │
│ Silent demo · illustrative title sequence             │
│ Brief note: captured panel, composited titles         │
└───────────────────────────────────────────────────────┘
       │ click Play
       ▼
Muted inline playback fades in → controls → product details → download link
```

```mermaid
flowchart LR
    A[Indri BGA page poster] --> B[Play silent video]
    B --> C[Wait for a game while using another window]
    C --> D[See searching count down 3 to 0]
    D --> H[See Play title flash]
    H --> G[See generic move alert flash]
    G --> E[Pointer clicks panel title]
    E --> F[Cut to BGA browser screenshot]
    F --> I[Download current release]
```

## Production and checks

- [x] Capture the installed panel's normal and white flash frames without including desktop content in the published sources.
- [x] Build an H.264 MP4 and poster with a readable alert sequence.
- [x] Inspect frames at the start, flash, and end; verify captions and absence of private desktop content.
- [x] Add the video and a text description to the Indri product page.
- [x] Preview desktop and mobile layout, build, publish, and verify the live asset.

Will found the original 0.1-second video flashing too fast. The video edit now holds each frame for 0.5 seconds; the installed app is unchanged. Indri v0.1.219 serves the revised MP4, whose SHA-256 matches the local build (`138c67f3390f49c9a7e1eed4cf5c31ca79a83f28e3467d586409c21681e580c6`).

Will also rejected the “No separate tray icon” line: it distracted from the point of an app that lives beside the tray. Indri v0.1.220 replaces it with “No window or tab hunting.” The live MP4 matches the revised build (`05648648f6f1792399d56fbfd1d7de289e4288740aeb762f08f30e9fb00a62ff`).

## Queue and move-alert revision

Will pointed out that a flashing “Searching for 3 player(s)” title falsely suggests matchmaking itself is the alert. The revised edit shows searching count down 3 → 2 → 1 → 0 without flashing, then flashes “Play • Board Game Arena.” The closing “Stay in the game” frame flashes the generic illustrative title “You must make your move • Board Game Arena.” The real panel frames remain, with those titles composited and disclosed in the captions and transcript.

- [x] Build the countdown and both alert sequences; inspect white and normal frames for each.
- [x] Update the poster, transcript, and site video; publish and verify the live assets.

Indri v0.1.221 serves the countdown and two alert sequences. The live MP4 matches the local build by SHA-256 (`8bf23e2589b4bddd85b31dba7594baf6b3c30f364055ebb51309e751df1086dc`).

## Blender motion pass

The motion layer uses [Blender 5.0.1 keyframes](https://docs.blender.org/manual/en/5.0/animation/introduction.html) and a transparent VP9 export. The existing [FFmpeg filter build](https://ffmpeg.org/ffmpeg-filters.html) composites it over the captured panel frames and illustrative titles. The accents follow state changes and leave the panel text readable:

| Time | Motion cue |
|---|---|
| 0–3 s | Draw a lime underline below the opening copy. |
| 3–6 s | Fill a queue progress line in four steps alongside the 3 → 2 → 1 → 0 title changes. |
| 6–10 s | Draw lime corner brackets around the flashing Play panel. |
| 14–18 s | Hold the move alert and closing URL steady enough to read. |
| 18–22 s | Expand a ring from the pointer click, then draw a thin accent above the BGA browser frame. |

- [x] Prototype the Blender motion pass and export frames for the existing FFmpeg build.
- [x] Inspect motion at desktop and 390 px mobile player sizes before replacing the published cut.

The 22-second motion cut keeps the large captions readable at both sizes. The Blender source is `media/promo/render_motion.py`; `render-motion.sh` exports the transparent VP9 layer, and `build.sh` composites it with the panel and browser frames.

## Click-to-focus edit

The updated video shows a composited pointer click on the panel title, then cuts to Will's one-tab BGA browser screenshot. The browser frame illustrates the focus result; it is not a continuous live recording of the click. The screenshot is cropped to remove the desktop panel and unrelated notification.

```text
Panel alert and composited click      Browser screenshot after the cut
┌────────────────────────────┐       ┌────────────────────────────┐
│ You must make your move     │       │ One BGA tab in Chrome      │
│ [pointer → panel title]     │       │ BGA welcome page          │
├────────────────────────────┤ click ├────────────────────────────┤
│ KDE panel strip            │ ────▶ │ Browser viewport           │
└────────────────────────────┘       └────────────────────────────┘
```

```mermaid
flowchart LR
    A[Start matchmaking in BGA] --> B[Use another window]
    B --> C[Read waiting status in panel]
    C --> D[Game ready alert appears]
    D --> E[Click BGA panel title]
    E --> F[Existing BGA window and tab come forward]
    F --> G[Start the game]
```

- [x] Receive Will's one-tab BGA browser screenshot and crop unrelated desktop content.
- [x] Compose a pointer click at the end and cut to the BGA browser frame.
- [x] Verify the new video and poster, then update and publish the product page.

Indri v0.1.222 serves the 22-second cut. The deploy workflow passed, desktop and 390 px page previews showed the centered Play control, and the live MP4 matches the local source by SHA-256 (`47ea0947a5c35930bb52dfcc96bda71fc6e67bfc502a00ec20fa55d164ae878d`).

## Product page cleanup

Will asked to remove the expandable video transcript. The short caption under the player still identifies the panel frames and composited titles.

- [x] Remove the transcript block and its unused styling from the product page.
- [x] Publish the updated page and verify that the live transcript is gone.

Indri v0.1.223 is live. The published page retains the video player and short caption, and contains no transcript block.

AI assistance: Codex CLI 0.163.0, GPT-6; reasoning-effort metadata unavailable in this session.
