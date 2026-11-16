# AstroMenace daletop-to-GitHub reconciliation (16 Nov 2026)

The 1 November local snapshot is `~/AmiCradle-dev/neverball-finish-20261101/ports/astromenace`. This was compared read-only against `DalsinAI/amigaastromenace` main. No local source, lab, or build output was overwritten, moved or removed.

The 1 November snapshot contains 14 differently hashed *same-path* source/docs, all requiring history-aware comparison rather than uploading an old snapshot over newer code. Three additional old-name files were found: `audio_amigachrome.cpp`, `glu_amigachrome.cpp`, `malloc_amigachrome.cpp`. They correspond to the renamed GitHub `*_amicradle.cpp` files.

- `glu_amigachrome.cpp` and `glu_amicradle.cpp` have identical Git blob hashes (`79dd485f`).
- The audio file in GitHub has additional decoding-thread, PCM queuing and reserved-music-channel support; the older disk audio is missing that newer code. Do not restore the older audio file.
- The malloc old-name variant differs from the current file in branding and the exit function name. Do not restore the older source over the renamed code.

The active PR #5 adds **new** VFS integrity checks and six synthetic host tests for canonical paths, escaping links, duplicate entries, truncated tables, and an end-to-end 101-entry VFS. It is not a claim that native runtime qualification passed.

The following offloaded historical work was *located but not traversed*, pending the applicable DevDrive read-only gate: `astromenace-runtime-labs`, `astromenace-recovery-quarantine`. Earlier launcher, AHI close, and mixer-close lab folders were identified but no unpublished source changes from them were merged. Keep those records until fully inspected and compared; do not delete the old work.

Remaining gates: fresh pinned source build with approved OpenGPU SDK, title, workshop, first mission, controller/input, audible music/effects, clean quit, and representative frame times. Historical lab output must be linked to an exact executable hash.
