import urllib.request, zipfile, os, shutil, sys
def main():
    url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    tmp = "ffmpeg_tmp.zip"
    try:
        print("  Downloading ffmpeg (50-80 MB)...")
        urllib.request.urlretrieve(url, tmp)
        print("  Extracting...")
        with zipfile.ZipFile(tmp) as z:
            for name in z.namelist():
                if name.endswith("bin/ffmpeg.exe"):
                    with z.open(name) as src, open("ffmpeg_bundled.exe","wb") as dst:
                        shutil.copyfileobj(src, dst)
                    print("[OK] ffmpeg_bundled.exe ready")
                    return 0
        print("[WARN] ffmpeg.exe not found in archive")
        return 1
    except Exception as e:
        print("[WARN] Failed:", e)
        return 1
    finally:
        if os.path.isfile(tmp): os.remove(tmp)
sys.exit(main())
