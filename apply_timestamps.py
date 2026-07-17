#!/usr/bin/env python3
"""Apply an EXIF Date Taken timestamp from an EXIF Date Fixer CSV export."""

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path, PurePosixPath

import click
from rich.console import Console
from rich.progress import Progress


EXIF_TIME_FORMAT = "%Y:%m:%d %H:%M:%S"
console = Console()


def parse_timestamp(value: str) -> str:
    """Convert the CSV's local timestamp (with optional UTC offset) to EXIF time."""
    value = value.strip()
    if len(value) >= 10 and value[4] == value[7] == ":":
        value = f"{value[:4]}-{value[5:7]}-{value[8:]}"
    return datetime.fromisoformat(value).strftime(EXIF_TIME_FORMAT)


def indexed_files(root: Path) -> dict[str, list[Path]]:
    files: dict[str, list[Path]] = defaultdict(list)
    for path in root.rglob("*"):
        if path.is_file():
            files[path.name].append(path)
    return files


def resolve_photo(root: Path, filename: str, files: dict[str, list[Path]]) -> Path:
    relative = Path(*PurePosixPath(filename).parts)
    candidate = (root / relative).resolve()
    if candidate.is_file() and root in candidate.parents:
        return candidate
    matches = files.get(relative.name, [])
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise click.ClickException(f"not found: {filename}")
    raise click.ClickException(f"ambiguous filename: {filename}")


def exif_time(path: Path) -> str:
    import piexif

    data = piexif.load(str(path))
    value = (data.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)
             or data.get("0th", {}).get(piexif.ImageIFD.DateTime)
             or b"")
    return value.decode("ascii", "replace") if value else ""


def update_exif_time(path: Path, timestamp: str) -> None:
    import piexif

    data = piexif.load(str(path))
    encoded = timestamp.encode("ascii")
    data.setdefault("0th", {})[piexif.ImageIFD.DateTime] = encoded
    exif = data.setdefault("Exif", {})
    exif[piexif.ExifIFD.DateTimeOriginal] = encoded
    exif[piexif.ExifIFD.DateTimeDigitized] = encoded
    piexif.insert(piexif.dump(data), str(path))


def csv_row_count(path: Path) -> int:
    # The editor exports one record per physical line; avoid parsing the CSV twice.
    with path.open("rb") as stream:
        lines = sum(chunk.count(b"\n") for chunk in iter(lambda: stream.read(1024 * 1024), b""))
    return max(0, lines - 1)  # Exclude the header.


@click.command()
@click.argument("csv_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("photos_root", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--dry-run", is_flag=True, help="Print changes without writing EXIF metadata.")
def main(csv_path: Path, photos_root: Path, dry_run: bool) -> None:
    """Apply CSV timestamps to photos below PHOTOS_ROOT."""
    try:
        import piexif  # noqa: F401
    except ImportError as error:
        raise click.ClickException("install dependencies with: python3 -m pip install -r requirements.txt") from error
    files = indexed_files(photos_root.resolve())
    updated = skipped = 0
    total = csv_row_count(csv_path)
    with csv_path.open(newline="", encoding="utf-8") as stream:
        with Progress(console=console) as progress:
            task = progress.add_task("Checking" if dry_run else "Updating", total=total)
            for row in csv.DictReader(stream):
                filename, timestamp = row.get("filename", ""), row.get("timestamp", "")
                try:
                    if not filename or not timestamp:
                        skipped += 1
                        continue
                    path = resolve_photo(photos_root.resolve(), filename, files)
                    updated_time = parse_timestamp(timestamp)
                    original_time = exif_time(path)
                    line = f"[{path}] [{original_time:19}] -> [{updated_time}]"
                    if not dry_run:
                        update_exif_time(path, updated_time)
                    console.print(line, markup=False)
                    updated += 1
                except (ValueError, OSError, click.ClickException) as error:
                    console.print(f"{filename}: {error}", style="red", markup=False)
                    skipped += 1
                finally:
                    progress.advance(task)
    if not dry_run:
        console.print(f"Updated {updated}; skipped {skipped}.")


if __name__ == "__main__":
    main()
