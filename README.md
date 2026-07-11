# EXIF Date Fixer

EXIF Date Fixer is a local, browser-based tool for repairing and organizing photo capture times when some photos have reliable timestamps and others do not.

It is especially useful for large photo batches where a camera clock was wrong, timestamps were lost, or only a few photos contain usable EXIF/XMP dates. Photos with known dates act as “anchors”; photos placed between anchors receive interpolated timestamps based on their position in the timeline.

## What it does

- Reads EXIF/XMP timestamps from image files.
- Places photos with known timestamps into a chronological timeline.
- Keeps photos without usable timestamps in an unplaced pool.
- Lets you manually assign or clear anchor timestamps, and restore cleared metadata timestamps.
- Interpolates timestamps for unmarked photos between anchors.
- Supports multi-selection, keyboard movement, drag-and-drop, undo/redo, and a full-screen viewer.
- Exports a CSV without modifying the original image files.
- Stores sessions locally in the browser using IndexedDB.

The app does not upload photos to a server. Original files remain available only for the current browser session and are used for full-resolution viewing and source verification. Small thumbnails and photo metadata are saved locally so a session can be restored later.

## Typical workflow

1. Open `main.html` in a modern browser.
2. Select or drop a batch of photos into the loading area.
3. Review photos with existing timestamps in the timeline and photos without timestamps in the unplaced pool.
4. Drag photos into the timeline and arrange them in the intended order.
5. Set manual timestamps on reliable photos to create anchors.
6. Use **Re-interpolate** after making broad changes, or let the app update interpolation automatically.
7. Export a CSV containing the resulting timestamps.

When importing photos again after a reload, select the original files so the app can reconnect runtime file access. Matching files are identified using stored fingerprints when available; a filename match with different source metadata is reported as a mismatch instead of silently replacing the existing photo.

## CSV export and timezones

CSV export asks for an IANA timezone, defaulting to `Asia/Jerusalem`. The timeline’s visible clock value is kept unchanged and the selected timezone is attached to it. The CSV includes:

- the filename;
- the timestamp with its timezone offset;
- the equivalent UTC timestamp;
- the timezone name;
- whether the timestamp was interpolated.

For example, a displayed time of `18:00:00` in `Asia/Jerusalem` may be exported as `18:00:00+03:00` in summer and `18:00:00+02:00` in winter, with the corresponding UTC value included. This output can be used as input when batch-updating image metadata with ExifTool or a similar tool.

## Import performance

Photo processing uses a bounded pool of Web Workers for fingerprinting, EXIF/XMP parsing, and thumbnail generation. The worker multiplier can be changed in **Settings**. Higher values may improve import speed but use more CPU and memory.

Incremental import rendering can also be disabled. When disabled, the app processes the full batch first and places the new photos into the lists in one final UI update. This can be useful when rendering thousands of cards is the bottleneck.

The application is designed for collections of thousands of photos. It uses incremental DOM updates for selection, timeline movement, transfers, and history restoration rather than rebuilding every card for each interaction.

## Browser requirements

Use a modern browser with support for:

- Web Workers;
- `OffscreenCanvas`;
- `createImageBitmap`;
- Web Crypto;
- IndexedDB.

These features are used to keep large imports responsive. The app reports an error when required import capabilities are unavailable.

## Documentation

See [ARCHITECTURE.md](ARCHITECTURE.md) for the application state model, persistence behavior, worker-based importing, rendering paths, performance considerations, and guidance for modifying the code.
