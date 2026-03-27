import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from contextlib import suppress

FFMPEG_ZIP_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-gpl.zip"
)
OUTPUT_FFMPEG = "ffmpeg.exe"
OUTPUT_FFPROBE = "ffprobe.exe"
REQUEST_TIMEOUT_SEC = 60
CHUNK_SIZE = 1024 * 1024  # 1 MB


def log(msg: str) -> None:
    print(msg, flush=True)


def download_file(url: str, dest_path: str) -> None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Vidra-FFmpeg-Downloader/1.0"},
    )
    with (
        urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as response,
        open(dest_path, "wb") as out_file,
    ):
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            out_file.write(chunk)


def find_bin_in_archive(zip_path: str, binary: str) -> str | None:
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            normalized = name.replace("\\", "/").lower()
            target = f"/bin/{binary.lower()}"
            if normalized.endswith(target):
                return name
    return None


def extract_ffmpeg(zip_path: str, member_name: str, output_path: str) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(member_name) as src, open(output_path, "wb") as dst:
            shutil.copyfileobj(src, dst)


def validate_output(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0


def main() -> int:
    log("  Downloading ffmpeg (50-80 MB)...")

    temp_zip = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="ffmpeg_", suffix=".zip", delete=False
        ) as tmp:
            temp_zip = tmp.name

        download_file(FFMPEG_ZIP_URL, temp_zip)

        log("  Extracting...")
        ffmpeg_member = find_bin_in_archive(temp_zip, "ffmpeg.exe")
        if not ffmpeg_member:
            log("[WARN] ffmpeg.exe not found in archive")
            return 1

        extract_ffmpeg(temp_zip, ffmpeg_member, OUTPUT_FFMPEG)

        if not validate_output(OUTPUT_FFMPEG):
            log("[WARN] Extracted ffmpeg.exe is empty or missing")
            return 1

        log(f"[OK] {OUTPUT_FFMPEG} ready")

        ffprobe_member = find_bin_in_archive(temp_zip, "ffprobe.exe")
        if ffprobe_member:
            extract_ffmpeg(temp_zip, ffprobe_member, OUTPUT_FFPROBE)
            if validate_output(OUTPUT_FFPROBE):
                log(f"[OK] {OUTPUT_FFPROBE} ready")
            else:
                log("[WARN] Extracted ffprobe.exe is empty or missing")
        else:
            log("[WARN] ffprobe.exe not found in archive (metadata may be limited)")

        return 0

    except urllib.error.URLError as e:
        log(f"[WARN] Network error: {e}")
        return 1
    except zipfile.BadZipFile:
        log("[WARN] Downloaded file is not a valid ZIP archive")
        return 1
    except PermissionError as e:
        log(f"[WARN] Permission error: {e}")
        return 1
    except OSError as e:
        log(f"[WARN] Filesystem error: {e}")
        return 1
    except Exception as e:
        log(f"[WARN] Failed: {e}")
        return 1
    finally:
        if temp_zip:
            with suppress(OSError):
                os.remove(temp_zip)


if __name__ == "__main__":
    if sys.platform != "win32":
        log("[WARN] This helper is intended for Windows (downloads ffmpeg.exe).")
        sys.exit(1)

    sys.exit(main())
