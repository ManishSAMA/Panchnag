# Plan: मुहूर्त tab, and Back that stays in the app

Status: **approved 2026-11-19** (the user's answers below).

## Context

After the phone check (2026-11-19) the user asked for two changes:

1. The bottom bar gets a **मुहूर्त** tab in place of the **पच्चक्खाण** tab. The user had asked for this before; the earlier work put the मुहूर्त band on Today instead.
2. **Back** must go back one screen and never close the app from inside it. On आज, Back must be pushed two times to close the app.

## The user's answers (2026-11-19)

| Question | Answer |
|---|---|
| Which tab | पच्चक्खाण → मुहूर्त. Tabs: आज, माह, मुहूर्त, पर्व. पच्चक्खाण opens from its Today tile, the yellow band and "सभी देखें", which stay. |
| Back on another tab | Goes to आज. |
| Back on आज | The first push shows "बाहर जाने के लिए फिर से वापस दबाएँ" ("Press back again to exit") for 2 s; a second push in that time closes the app. |
| Today's मुहूर्त tile and band | Open the मुहूर्त tab. |

## Changes (`mobile/app`)

- `router.dart`: `/muhurat` (and `/muhurat/:kind` under it) moves into the third shell branch; `/pachchakkhan` becomes a top-level pushed route, as `/choghadiya` is. The third destination is मुहूर्त with `NavpadGlyph.abhijit`.
- Today: the पच्चक्खाण tile, the yellow band and "सभी देखें" `push('/pachchakkhan')`, so Back returns to Today. The मुहूर्त tile and the band `go('/muhurat')`.
- `_TabShell`: a `PopScope` that, when the branch has nothing to pop, goes to `/today` from another tab, and on `/today` asks for a second Back within 2 s (a `SnackBar`) before it lets the app close.
- ARB: `pressBackAgainToExit`.
- Tests: Back from a pushed screen, from another tab, and on Today (one push stays, two close); the tab bar order; Pachchakkhan opens from Today and Back returns. Existing tests that open Pachchakkhan through the tab open it through Today.
- Docs: CLAUDE.md (Muhurat item, tabs), DESIGN.md (Navigation: four destinations).
