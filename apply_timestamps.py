#!/usr/bin/env python3
"""Apply an EXIF Date Taken timestamp from an EXIF Date Fixer CSV export."""

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile

import click
from rich.console import Console
from rich.progress import Progress
from rich.text import Text


EXIF_TIME_FORMAT = "%Y:%m:%d %H:%M:%S"
console = Console()


def print_status(status: str, path: str, message: str, style: str,
                 message_style: str | None = None, message_first: bool = False) -> None:
    line = Text(f"[{status:<7}] ", style=style)
    if message_first:
        line.append(f"{message} ", style=message_style or style)
    line.append(f"[{path}] ", style="dim")
    if not message_first:
        line.append(message, style=message_style or style)
    console.print(line, highlight=False)


def parse_timestamp(value: str) -> tuple[str, str | None]:
    """Convert the CSV timestamp to EXIF wall time and its UTC offset."""
    value = value.strip()
    if len(value) >= 10 and value[4] == value[7] == ":":
        value = f"{value[:4]}-{value[5:7]}-{value[8:]}"
    timestamp = datetime.fromisoformat(value)
    offset = timestamp.strftime("%z")
    return timestamp.strftime(EXIF_TIME_FORMAT), f"{offset[:3]}:{offset[3:]}" if offset else None


def indexed_files(root: Path) -> dict[str, list[Path]]:
    files: dict[str, list[Path]] = defaultdict(list)
    for path in root.rglob("*"):
        if path.is_file():
            files[path.name].append(path)
    return files


def resolve_photo(root: Path, filename: str, files: dict[str, list[Path]] | None = None) -> tuple[Path | None, bool]:
    relative = Path(*PurePosixPath(filename).parts)
    for index in range(len(relative.parts)):
        candidate = (root / Path(*relative.parts[index:])).resolve()
        if candidate.is_file() and root in candidate.parents:
            return candidate, index > 0
    if files is None:
        return None, False
    matches = files.get(relative.name, [])
    suffix_matches = [path for path in matches if filename.endswith(path.relative_to(root).as_posix())]
    if len(suffix_matches) == 1:
        return suffix_matches[0], True
    if len(matches) == 1:
        return matches[0], True
    if not matches:
        raise click.ClickException(f"not found: {filename}")
    raise click.ClickException(f"ambiguous auto-detected filename: {filename}")


def exif_timestamp(path: Path) -> tuple[str, tuple[str, str, str]]:
    import piexif

    data = piexif.load(str(path))
    value = (data.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)
             or data.get("0th", {}).get(piexif.ImageIFD.DateTime)
             or b"")
    exif = data.get("Exif", {})
    offsets = tuple(
        exif.get(tag, b"").decode("ascii", "replace")
        for tag in (piexif.ExifIFD.OffsetTime, piexif.ExifIFD.OffsetTimeOriginal, piexif.ExifIFD.OffsetTimeDigitized)
    )
    return value.decode("ascii", "replace") if value else "", offsets


def update_exif_time(path: Path, timestamp: str, offset: str | None) -> None:
    import piexif

    data = piexif.load(str(path))
    encoded = timestamp.encode("ascii")
    data.setdefault("0th", {})[piexif.ImageIFD.DateTime] = encoded
    exif = data.setdefault("Exif", {})
    exif[piexif.ExifIFD.DateTimeOriginal] = encoded
    exif[piexif.ExifIFD.DateTimeDigitized] = encoded
    if offset:
        encoded_offset = offset.encode("ascii")
        exif[piexif.ExifIFD.OffsetTime] = encoded_offset
        exif[piexif.ExifIFD.OffsetTimeOriginal] = encoded_offset
        exif[piexif.ExifIFD.OffsetTimeDigitized] = encoded_offset
    with NamedTemporaryFile(dir=path.parent, suffix=path.suffix, delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        piexif.insert(piexif.dump(data), str(path), str(temp_path))
        temp_path.chmod(path.stat().st_mode)
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)


def csv_row_count(path: Path) -> int:
    # The editor exports one record per physical line; avoid parsing the CSV twice.
    with path.open("rb") as stream:
        lines = sum(chunk.count(b"\n") for chunk in iter(lambda: stream.read(1024 * 1024), b""))
    return max(0, lines - 1)  # Exclude the header.


@click.command()
@click.argument("csv_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("photos_root", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--dry-run", is_flag=True, help="Print changes without writing EXIF metadata.")
@click.option("--accept-auto-detected", is_flag=True, help="Use non-exact path matches without prompting.")
def main(csv_path: Path, photos_root: Path, dry_run: bool, accept_auto_detected: bool) -> None:
    """Apply CSV timestamps to photos below PHOTOS_ROOT."""
    try:
        import piexif  # noqa: F401
    except ImportError as error:
        raise click.ClickException("install dependencies with: python3 -m pip install -r requirements.txt") from error
    root = photos_root.resolve()
    files = None
    updated = skipped = same = 0
    total = csv_row_count(csv_path)
    with csv_path.open(newline="", encoding="utf-8") as stream:
        with Progress(console=console) as progress:
            task = progress.add_task("Checking" if dry_run else "Updating", total=total)
            for row in csv.DictReader(stream):
                filename, timestamp = row.get("filename", ""), row.get("timestamp", "")
                try:
                    if not filename or not timestamp:
                        skipped += 1
                        print_status("skipped", filename or "<missing filename>", "missing timestamp", "yellow")
                        continue
                    path, auto_detected = resolve_photo(root, filename, files)
                    if path is None:
                        progress.update(task, description="Indexing photos")
                        files = indexed_files(root)
                        progress.update(task, description="Checking" if dry_run else "Updating")
                        path, auto_detected = resolve_photo(root, filename, files)
                    if auto_detected and not accept_auto_detected:
                        progress.stop()
                        try:
                            print_status("auto", str(path), f"for [{filename}] type y then Enter to use it:", "yellow")
                            accepted = input().strip().lower() in ("y", "yes")
                        finally:
                            progress.start()
                        if not accepted:
                            raise click.ClickException("auto-detected photo declined")
                    updated_time, updated_offset = parse_timestamp(timestamp)
                    updated_label = f"{updated_time}{updated_offset or ''}"
                    original_time, original_offsets = exif_timestamp(path)
                    original_offset = next((offset for offset in (original_offsets[1], original_offsets[0], original_offsets[2]) if offset), "")
                    original_label = f"{original_time}{original_offset}"
                    if original_time == updated_time and all(offset == (updated_offset or "") for offset in original_offsets):
                        same += 1
                        print_status("same", str(path), f"[{original_label:25}] -> [{updated_label}]", "cyan", "green", True)
                    else:
                        if not dry_run:
                            update_exif_time(path, updated_time, updated_offset)
                        print_status("updated", str(path), f"[{original_label:25}] -> [{updated_label}]", "green", message_first=True)
                        updated += 1
                except (ValueError, OSError, click.ClickException) as error:
                    print_status("skipped", filename, str(error), "red")
                    skipped += 1
                finally:
                    progress.advance(task)
    if not dry_run:
        console.print(f"Updated {updated}; same {same}; skipped {skipped}.")


if __name__ == "__main__":
    main()
