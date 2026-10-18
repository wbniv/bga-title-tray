# Live Play-offer cancellation, 2026-10-18

The 0.4.7 host was installed and restarted while the Board Game Arena page stayed open. A one-shot local watcher sampled host status every 100 ms through the existing control socket. It recorded state changes without changing the page.

- [x] At 08:16:48.031 Asia/Bangkok, the selected tab reported a visible offer (`selectedOfferVisible: true`) and an active Play flash (`flashActive: true`).
- [x] At 08:16:54.885, after the offer ended, the selected tab reported `selectedOfferVisible: false`, `selectedLobbyVisible: true`, and `flashActive: false`.
- [x] Chrome's raw title still said “Play”; the panel status label changed to “Play now! • Board Game Arena”.
- [ ] Confirm the white/black panel animation stopped visually. The host and widget status prove the alert cleared, but the panel itself was not captured at that instant.

The raw local watcher record is `/tmp/bga-title-tray-next-offer-2026-10-18.jsonl`. It includes unrelated game and player titles, so it is not part of the public repository.

The first watcher run exited at the ordinary “Play now!” lobby before this offer. The watcher now requires an offer candidate before treating a Play title as the target transition; the second run captured the offer and exited after it ended.
