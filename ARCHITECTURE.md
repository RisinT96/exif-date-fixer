# Architecture and maintenance guide

This project is a single-file local web application. [`main.html`](main.html) contains the page structure, styles, and all application logic. This document explains how its parts fit together so changes can be made without accidentally defeating the large-collection optimizations.

## Application model

The editor has one canonical photo record for each photo and two ordered lists:

- `photos`: an object keyed by photo ID. It contains photo metadata, thumbnail data, source identity, timestamp state, and transient runtime-only file access.
- `timeline`: photo IDs in timeline order.
- `unplaced`: photo IDs currently in the left-side pool, in the selected pool sort order.

`photos[id].inTimeline` mirrors membership in `timeline`; it is stored for session compatibility and convenience, but the two arrays define ordering.

Each photo record can contain:

| Field | Purpose |
| --- | --- |
| `id`, `name`, `camera`, `modifiedTime` | Stable file metadata used by the UI and sorting. |
| `timestamp`, `timestampSource` | A real anchor time and where it came from: EXIF/XMP/manual. |
| `clearedTimestamp`, `clearedTimestampSource` | A cleared metadata anchor retained only so the user can restore it. |
| `_interpolated` | Calculated time for a non-anchor timeline photo. Never persisted as an input. |
| `thumbURL` | Small JPEG data URL saved in the session for persistent previews. |
| `sourceFile` | Runtime-only lazy `File` reference for full-resolution viewing. It is intentionally never persisted. |
| `sourceSize`, `sourceFingerprint` | Bounded source identity used to re-associate a file with an existing session photo. |

## Startup, persistence, and import/export

`initApp()` loads the IndexedDB session through `loadSession()`, enables saving, and calls `render()`.

`buildSessionState()` serializes only persistent fields. In particular, it excludes `sourceFile`, because browser-selected file access cannot safely survive a reload. `restoreSessionState()` accepts older sessions that lack source identity fields.

The Export Session button writes the same serializable state as JSON. CSV export contains the final display timestamp for each photo; it does not modify image files.

## Loading and identifying photos

`handleFiles()` processes selected or dropped files one at a time so a large selection is not duplicated into JavaScript memory.

For every new file it:

1. Reads EXIF/XMP date metadata.
2. Creates a reduced thumbnail.
3. Generates a bounded SHA-256 fingerprint from metadata plus first/last file samples.
4. Stores the photo and its lazy `sourceFile` reference.

If a session photo has the same filename, `sourceMatchesPhoto()` checks its fingerprint when available, otherwise falls back to stored size/modification metadata for legacy sessions. A match re-attaches the `File` without rebuilding the thumbnail; a mismatch is reported rather than silently replacing a photo.

## Timestamp calculation

`interpolateAll()` computes display times for the timeline. Anchors retain `timestamp`; non-anchors get `_interpolated`.

The implementation makes forward and backward anchor passes, then fills values in linear time. `estimateGap()` supplies a default gap when only one anchor exists. Keep this code linear: repeated searches through the timeline become expensive at thousands of photos.

## Selection, drag-and-drop, and timeline moves

`selectedIds` holds current selection and `selectionAnchor` supports shift-selection. `updateSelectionUI()` changes only existing card classes; it must not call a full render for ordinary selection changes.

For moves within the timeline, `moveSelectedTimeline()` and the timeline branch of `onDropTargetDrop()` update the `timeline` array first. `reorderTimelineDom()` then relocates only changed `.timeline-entry` DOM nodes, refreshes only the affected anchor span, and animates only that range.

Drop targets calculate their insertion index from their current DOM position. This avoids rewriting handlers after each reorder.

## Pool/timeline transfers

The transfer helpers avoid rebuilding both lists for normal moves:

- `removePoolCards()` / `insertPoolCards()` update just pool cards that changed.
- `removeTimelineEntries()` / `insertTimelineEntries()` update just changed timeline entries.
- `finalizeIncrementalTransfer()` refreshes timestamps only in anchor ranges affected by the move.

For a large transfer (more than 24 cards), `reconcilePoolCards()` and the bulk timeline helpers use a single DOM scan plus a `DocumentFragment`. This prevents quadratic repeated selector and insertion work, especially when removing all timeline photos.

## Rendering paths

`render()` is the safe full-render fallback. It rebuilds the relevant pool and timeline markup and is appropriate for initial load, import, clearing, or structural changes that cannot be updated incrementally.

Prefer these faster paths for frequent interactions:

| Change | Preferred renderer |
| --- | --- |
| Select/deselect | `updateSelectionUI()` |
| Reorder inside timeline | `reorderTimelineDom()` |
| Move pool ↔ timeline | transfer helpers plus `finalizeIncrementalTransfer()` |
| Undo/redo of timeline-only changes | incremental `restoreEditorState()` path |
| Undo/redo of pool membership changes | incremental transfer restore path |

Avoid adding unconditional calls to `render()` in these paths. They can recreate thousands of cards and cause multi-second delays.

## Undo and redo

`historyPast` and `historyFuture` contain editor snapshots. `historyPhotoRegistry` stores immutable photo fields once, including thumbnail data. Each history entry stores only photo IDs, timestamp-related mutable fields, and list ordering.

`restoreEditorState()` recognizes common restore shapes:

- Timeline order only: moves existing timeline entries incrementally.
- Timestamp changes only: refreshes changed timeline cards.
- Pool/timeline membership changes: uses the incremental transfer helpers.
- Photo additions/removals or other unusual state: falls back to `render()`.

This distinction keeps undo/redo fast without sacrificing correctness for less common operations.

## Full-screen viewer

Clicking a thumbnail calls `openPhotoViewer()`. If `sourceFile` is available, the viewer creates an object URL only for that photo and revokes it on close. If the session was restored and no original file has been reselected, the viewer falls back to the persisted thumbnail.

Arrow-key navigation follows `timeline` then `unplaced`. Escape closes the overlay.

## Memory and image rendering

Original images are not converted to data URLs or kept decoded. Thumbnails are intentionally small and use lazy asynchronous image decoding. CSS `content-visibility` reduces work for off-screen cards.

The remaining stored thumbnail data is still base64 text. Converting thumbnails to IndexedDB blobs and object URLs is a future memory optimization, but should preserve the current persistent-session behavior.

## Styling and accessibility notes

The CSS is grouped by major UI area: global layout, sidebar/pool, timeline, cards, modals, viewer, and processing status. Card status is represented by classes such as `anchored`, `interpolated`, and `selected`.

Buttons use titles or visible labels. Modal overlays handle Escape in the global key handler. When adding interactions, preserve existing keyboard behaviors for selection, Delete/Backspace, arrows, undo, and redo.

## Change checklist

When changing the app:

1. Update application state before changing the DOM.
2. Recalculate interpolation whenever timeline order, membership, or anchor timestamps change.
3. Choose the narrowest rendering path that keeps all affected cards correct.
4. Keep original files runtime-only and thumbnails persistent.
5. Test a large collection, multi-selection, undo/redo, an empty timeline, and restored sessions.
6. Update [`TODO.md`](TODO.md) after the user validates the behavior.
