# BETA Player — Android system controls
Status: web v2 preview implemented; native integration pending (not a compiled APK).

## Design
- Android owns the native media card layout and colors. Preserve transport controls.
- Expanded layout: two optional extra slots for favorite and EQ, with independent toggles. Compact mode keeps standard transport controls.
- Artwork: track, BETA mark or no artwork; system may choose fallback.
- Mercury/Obsidian/Ice are preview tones, not guaranteed native colors.

## Native integration
One Media3 ExoPlayer + MediaSessionService as playback owner.
- Define SessionCommand BETA_TOGGLE_FAVORITE; allow trusted controllers. Use heart filled/unfilled CommandButton in SLOT_OVERFLOW; refresh preferences after track transition, favorites and settings changes.
- Resolve currentMediaItem.mediaId when invoked. Reject missing track. Toggle through the same persisted library repository used by UI; report success only after persistence.
- BETA_OPEN_EQ (overflow): route to EQ activity via platform-permitted user-initiated launch or PendingIntent flow; validate background-launch limitations. Session activity is fallback. No arbitrary UI in shade.
- EQ should use active supported audio session; release effects on session changes, disclose unsupported routes.
- Local preferences; explicit migration from web state; no duplicate audio players.

## Acceptance
Real phone: playback while locked, card correct on next/previous, favorite persists and matches library, toggles preserve transport, no wrong-track favorite on rapid changes, EQ opens correct session or transparent fallback, compact layout, audio focus. Verify TECNO firmware separately.
Web v2: Settings > System card, play imported file, test artwork, material, optional controls, favorite, seek, EQ. System artwork support varies; optional actions are in-app preview only.

References:
https://developer.android.com/media/implement/surfaces/mobile
https://developer.android.com/media/media3/session/control-playback
https://developer.mozilla.org/en-US/docs/Web/API/MediaSession/setActionHandler
