# TODO

## Large-collection performance

### 1. Measure the current bottlenecks

- [ ] Test loading, scrolling, dragging, and selecting 1,000–5,000 photos.
- [ ] Record render time, scroll smoothness, memory usage, and browser heap usage.
- [ ] Identify whether DOM size, image decoding, layout, sorting, or interpolation is the dominant cost.

### 2. Reduce unnecessary work during rendering

- [ ] Avoid rebuilding the entire timeline and unplaced-photo pool after every small change.
- [ ] Update only cards and counters affected by a change where practical.
- [ ] Avoid recalculating sorting and membership checks repeatedly during one render.
- [ ] Limit or disable card transition animations for large collections.

### 3. Make thumbnails cheaper to display

- [ ] Store thumbnails as compressed blobs instead of base64 data URLs.
- [ ] Create object URLs only for thumbnails currently needed by the UI.
- [ ] Lazy-load thumbnail images as their cards approach the viewport.
- [ ] Release object URLs and decoded image resources when cards leave the active window.

### 4. Add low-risk browser rendering optimizations

- [ ] Add CSS containment and `content-visibility` to photo-card containers.
- [ ] Replace per-card inline event handlers with delegated events from the timeline and pool containers.
- [ ] Use document fragments or equivalent batched DOM updates for visible-card changes.

### 5. Virtualize the unplaced-photo pool

- [ ] Render only visible pool rows plus a small overscan buffer.
- [ ] Preserve the total scroll height with spacer elements.
- [ ] Reuse pool-card elements while scrolling instead of creating thousands of nodes.

### 6. Virtualize the timeline

- [ ] Move the timeline toward a predictable fixed-size grid or row layout.
- [ ] Calculate visible timeline rows from scroll position and viewport size.
- [ ] Render only visible rows plus overscan while preserving drop-target behavior.
- [ ] Ensure drag-and-drop, selection, keyboard movement, and timestamp editing work across virtualized rows.

### 7. Optimize data processing

- [ ] Replace repeated timeline scans in interpolation with linear forward/backward passes.
- [ ] Use sets or maps for photo membership and lookup operations.
- [ ] Keep undo snapshots lightweight and avoid copying runtime-only file references.
- [ ] Batch progress updates and expensive UI work during large imports.

### 8. Re-measure and set practical limits

- [ ] Repeat the benchmark suite after each major optimization.
- [ ] Verify behavior with thousands of photos, mixed image sizes, and missing thumbnails.
- [ ] Document supported collection sizes and any browser-specific limitations.
