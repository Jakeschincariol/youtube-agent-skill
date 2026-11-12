#!/usr/bin/env python3
"""Search and download Pexels media without storing the API key in source."""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

API_ROOT = "https://api.pexels.com"
LICENSE_URL = "https://www.pexels.com/license/"
MAX_DOWNLOAD_BYTES = 500 * 1024 * 1024


def api_key() -> str:
    key = os.environ.get("PEXELS_API_KEY")
    if key:
        return key
    env_file = Path(".env")
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() == "PEXELS_API_KEY":
                return value.strip().strip("\"'")
    raise RuntimeError("PEXELS_API_KEY is missing; set it in the environment or local .env file.")


def request_json(url: str) -> dict:
    req = Request(url, headers={"Authorization": api_key(), "User-Agent": "yt-documentary/1.0"})
    try:
        with urlopen(req, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Pexels API returned HTTP {exc.code}. Check the key and request limits.") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Pexels: {exc.reason}") from exc


def preferred_video_file(media: dict) -> dict | None:
    files = [
        item
        for item in media.get("video_files", [])
        if item.get("file_type") == "video/mp4"
        and item.get("link")
        and item.get("width")
        and item.get("height")
    ]
    if not files:
        return None
    landscape = [item for item in files if item["width"] >= item["height"]]
    candidates = landscape or files
    return min(candidates, key=lambda item: abs(item["width"] - 1280))


def result_record(media: dict, kind: str) -> dict | None:
    user = media.get("photographer") or media.get("user", {}).get("name") or "Unknown"
    record = {
        "id": media["id"],
        "kind": kind,
        "photographer": user,
        "source": "Pexels",
        "license": "Pexels License",
        "license_url": LICENSE_URL,
        "source_url": media.get("url", ""),
    }
    if kind == "video":
        item = preferred_video_file(media)
        if not item:
            return None
        record.update(
            file_url=item["link"],
            width=item["width"],
            height=item["height"],
            duration=media.get("duration"),
        )
    else:
        sources = media.get("src", {})
        record.update(
            file_url=sources.get("large2x") or sources.get("large") or sources.get("original"),
            width=media.get("width"),
            height=media.get("height"),
        )
        if not record["file_url"]:
            return None
    return record


def search(query: str, kind: str, limit: int) -> list[dict]:
    if kind == "video":
        endpoint = "/videos/search"
    else:
        endpoint = "/v1/search"
    params = urlencode({"query": query, "per_page": limit, "orientation": "landscape"})
    data = request_json(f"{API_ROOT}{endpoint}?{params}")
    items = data.get("videos" if kind == "video" else "photos", [])
    return [record for item in items if (record := result_record(item, kind))]


def download(record: dict, destination: Path) -> dict:
    parsed = urlparse(record["file_url"])
    if parsed.scheme != "https" or not (
        parsed.hostname == "pexels.com" or (parsed.hostname or "").endswith(".pexels.com")
    ):
        raise RuntimeError("Refusing a download URL that is not an HTTPS Pexels host.")

    req = Request(record["file_url"], headers={"User-Agent": "yt-documentary/1.0"})
    destination.mkdir(parents=True, exist_ok=True)
    extension = ".mp4" if record["kind"] == "video" else ".jpg"
    stem = f"pexels-{record['id']}"
    target = destination / f"{stem}{extension}"
    suffix = 2
    while target.exists():
        target = destination / f"{stem}-{suffix}{extension}"
        suffix += 1

    temp_path = None
    try:
        with urlopen(req, timeout=60) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > MAX_DOWNLOAD_BYTES:
                raise RuntimeError("File exceeds the 500 MiB download limit.")
            with tempfile.NamedTemporaryFile(dir=destination, suffix=".part", delete=False) as temp:
                temp_path = Path(temp.name)
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise RuntimeError("File exceeds the 500 MiB download limit.")
                    temp.write(chunk)
        temp_path.replace(target)
    except Exception:
        if temp_path:
            temp_path.unlink(missing_ok=True)
        raise

    record = {**record, "path": str(target.resolve()), "bytes": target.stat().st_size}
    manifest_path = destination / "pexels-credits.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    manifest.append(record)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    find = commands.add_parser("search", help="find landscape photos or videos")
    find.add_argument("query")
    find.add_argument("--kind", choices=("video", "photo"), default="video")
    find.add_argument("--limit", type=int, choices=range(1, 16), default=8)
    get = commands.add_parser("download", help="download one result and record its credit")
    get.add_argument("id", type=int)
    get.add_argument("--kind", choices=("video", "photo"), default="video")
    get.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    try:
        if args.command == "search":
            records = search(args.query, args.kind, args.limit)
            print(json.dumps(records, ensure_ascii=False, indent=2))
            return 0
        endpoint = f"/videos/videos/{args.id}" if args.kind == "video" else f"/v1/photos/{args.id}"
        media = request_json(f"{API_ROOT}{endpoint}")
        record = result_record(media, args.kind)
        if not record:
            raise RuntimeError(f"Pexels result {args.id} has no downloadable {args.kind} file.")
        print(json.dumps(download(record, args.out), ensure_ascii=False, indent=2))
        return 0
    except (RuntimeError, HTTPError, URLError, OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
