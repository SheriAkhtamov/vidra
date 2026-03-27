"""Generate vidra.ico from vidra_logo_48.png with proper multi-size icon."""
from PIL import Image

img = Image.open("vidra_logo_48.png").convert("RGBA")
img.save("vidra.ico", format="ICO", sizes=[(48, 48), (32, 32), (16, 16)])
print("  [OK] vidra.ico generated (48/32/16)")
