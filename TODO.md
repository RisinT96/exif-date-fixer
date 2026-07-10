# TODO

## Large-collection performance

### 1. Measure the current bottlenecks

- [x] Test selecting, dragging, reordering, and scrolling with approximately 1,000 photos.
- [x] Record interaction behavior and approximate tab memory usage.
- [x] Identify the current bottlenecks: undo/redo, pool↔timeline moves, and separator feedback.
- [ ] Measure loading and behavior at 5,000 photos.

### 2. Reduce unnecessary work during rendering

- [x] Avoid rebuilding the entire timeline and unplaced-photo pool for selection changes.
- [x] Update only selection classes when selection changes.
- [ ] Avoid recalculating sorting and membership checks repeatedly during one render.
- [ ] Limit or disable card transition animations for large collections.

### 3. Make thumbnails cheaper to display

- [ ] Store thumbnails as compressed blobs instead of base64 data URLs.
- [ ] Create object URLs only for thumbnails currently needed by the UI.
- [x] Lazy-load thumbnail images as their cards approach the viewport.
- [ ] Release object URLs and decoded image resources when cards leave the active window.

### 4. Add low-risk browser rendering optimizations

- [x] Add CSS containment and `content-visibility` to photo-card containers.
- [ ] Replace per-card inline event handlers with delegated events from the timeline and pool containers.
- [x] Use direct DOM moves or equivalent batched DOM updates for timeline changes.

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
- [ ] Move cards between the pool and timeline incrementally, without rebuilding both lists.
- [ ] Update timestamp edits incrementally instead of rebuilding every card.
- [ ] Replace separator hover feedback with one stable insertion indicator positioned from the current drag location.
- [ ] Delegate card and drag events from the list containers instead of embedding handlers on every card.
- [ ] Re-test 1,000-photo interactions after each change and compare memory and response latency.
