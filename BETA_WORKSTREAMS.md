# BETA — coordination / ZERO FLAWS

## Current baseline
- Identity preview: branch beta-identity, docs/index.html, https://mingalevd88-stack.github.io/BETA./
- Identity 0.6: visual studio, existing local profile editor, global glass, pointer sliders, six categories and three presets. Browser/real-device QA pending.
- Original Liquid: app/liquid.html, v40; do not replace the approved Pure Mercury HD+ v24 material or v31 physics.
- Original player: app/player.html, Signature Catalog v2.
- Approved reference: design/approved.html. Main branch remains unchanged by Identity preview.

## Workstreams
Each separate chat should begin by reading the current files and this plan. A chat is not an autonomous background worker. Create a separate branch from an inspected current baseline before changing shared code; never overwrite another workstream's files. Do not merge before review and tests.

| Stream | Scope | Suggested branch |
|---|---|---|
| Identity | Profile, personalization studio, shared materials and component motion | beta-identity (existing) |
| Liquid | Original onboarding cores, performance, search and selection retention | beta-liquid |
| Player | Playback, EQ, lyrics, queue, system media controls with OS limits | beta-player |
| Experience | Navigation, onboarding-to-player connection, cross-device layout and icon editor | beta-experience |
| Core | Accounts, legal catalog and import, storage and sync | beta-core |
| Zero Flaws | Regression, real device performance, accessibility, security, independent reviews | beta-qa |
| Early Access | Release criteria, feedback, staged distribution | beta-early-access |

The approved dependency order is Identity → Liquid → Player → Experience → Core → Zero Flaws → Early Access. Parallel work is suitable for isolated research, tests and prototypes; integration depends on upstream decisions. Branch names except beta-identity are suggestions, not claims that branches already exist.

## Rules
- User benefit before revenue; subscription later.
- Preserve approved 3D cores, one active mood, persistent selections, My Flow on home, no "world ready" banner.
- Motion inspired by Telegram/iOS, in Beta's own dark glass and liquid metal design.
- Keep a direct browser preview link for each review. Do not overwrite the Identity Pages preview from another stream.
- Report actual checks and failures; no fake passing tests or claims of 11/10 quality.
- Avoid putting secrets or personal data in the public repository.
