# BETA — Device sync

## Current prototype
app/player-transfer.html: explicit JSON export/import, version 1. Additive merging of remote favorites and playlists, optional whitelisted preferences; no server or account. Audio files, photos, listening history, queue and device volume stay local. Current cap 500 saved tracks / 200 playlists. Test in browser and on two devices before release.

## Real automatic synchronization — not yet implemented
- Introduce authenticated per-user cloud storage behind HTTPS, not a public JSON endpoint. Provider choice and any cost require approval. Use an account ID, never device ID or email supplied by the client as authorization.
- Persist favorites as per-track records and playlists with stable IDs. Include change IDs and server-assigned revisions. Retain tombstones for removals so reconnecting devices cannot resurrect deleted tracks. Define a deterministic conflict policy for playlist order and names; do not silently overwrite a whole collection.
- Client queues offline mutations in IndexedDB and retries idempotently; pull changes on login, reconnect and foreground. Preserve local-only files on every account transition. Show last successful sync time, offline status, and actionable error messages.
- Sync preferences per field. Keep volume, hardware EQ availability, device-specific layout and local audio paths local. Photo upload needs explicit opt-in, private storage and quotas; original files never upload by default.
- Test authorization isolation, two concurrent devices, offline mutations, deletion, retry, token expiry, account switch, export recovery, quota and storage errors. Verify real Android/browser behavior.
- Do not expose personal music history publicly. User-controlled export/delete and logout are acceptance criteria.

No cloud database, authentication or paid service has been provisioned by this change.
