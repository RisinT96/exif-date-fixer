# TODO

## Features

- [x] When viewing fullscreen, it should track which photo is moved and scroll the timeline to try an keep it in the center (handle begin/end edge cases), updating the current selection to match the currently viewed photo.
- [ ] Explore option of updating exif metadata in-place, and not just exporting it via a CSV.

## Large-collection performance

### 1. Measure the current bottlenecks

- [x] Test selecting, dragging, reordering, and scrolling with approximately 1,000 photos.
- [x] Record interaction behavior and approximate tab memory usage.
- [x] Identify the current bottlenecks: undo/redo, pool↔timeline moves, and separator feedback.
- [x] Measure loading and behavior at 5,000 photos.

### 2. Reduce unnecessary work during rendering

- [x] Avoid rebuilding the entire timeline and unplaced-photo pool for selection changes.
- [x] Update only selection classes when selection changes.
- [ ] Avoid recalculating sorting and membership checks repeatedly during one render.
- [x] Limit or disable card transition animations for large collections - rejected, animations are quick and don't pose issues.

### 3. Make thumbnails cheaper to display

- [ ] Store thumbnails as compressed blobs instead of base64 data URLs.
- [ ] Create object URLs only for thumbnails currently needed by the UI.
- [x] Lazy-load thumbnail images as their cards approach the viewport.
- [ ] Release object URLs and decoded image resources when cards leave the active window.

### 4. Add low-risk browser rendering optimizations

- [x] Add CSS containment and `content-visibility` to photo-card containers.
- [x] Replace per-card inline event handlers with delegated events from the timeline and pool containers.
- [x] Use direct DOM moves or equivalent batched DOM updates for timeline changes.

### 5. Virtualize the unplaced-photo pool

- [ ] Render only visible pool rows plus a small overscan buffer.
- [ ] Preserve the total scroll height with spacer elements.
- [ ] Reuse pool-card elements while scrolling instead of creating thousands of nodes.

### 6. Virtualize the timeline

- [x] Move the timeline toward a predictable fixed-size grid or row layout.
- [x] Calculate visible timeline rows from scroll position and viewport size.
- [x] Render only visible rows plus overscan while preserving drop-target behavior.
- [x] Ensure drag-and-drop, selection, keyboard movement, and timestamp editing work across virtualized rows.

### 7. Optimize data processing

- [x] Replace repeated timeline scans in interpolation with linear forward/backward passes.
- [x] Use sets or maps for photo membership and lookup operations.
- [x] Keep undo snapshots lightweight and avoid copying runtime-only file references.
- [ ] Batch progress updates and expensive UI work during large imports.

### 8. Re-measure and set practical limits

- [ ] Repeat the benchmark suite after each major optimization.
- [ ] Verify behavior with thousands of photos, mixed image sizes, and missing thumbnails.
- [ ] Document supported collection sizes and any browser-specific limitations.

### 9. Next optimization order

- [x] Optimize undo/redo with compact history and incremental timeline/timestamp restoration.
- [x] Move cards between the pool and timeline incrementally, including batched large transfers.
- [x] Update timestamp edits incrementally instead of rebuilding every card.
- [x] Replace separator hover feedback with a stable pointer-driven insertion indicator and expanded separator zones.
- [x] Delegate card and pointer-drag events from the list containers instead of embedding handlers on every card.
- [x] Re-test large-collection interactions: 4,000 timeline photos and 1,500 unplaced photos remained responsive.
