# import screeninfo
#
# for m in screeninfo.get_monitors():
#     print(f"Monitor {m.name}: {m.width}x{m.height} at ({m.x}, {m.y})")

import mss
import numpy as np
from PIL import Image

with mss.mss() as sct:
    monitor = sct.monitors[1]  # або [2] — другий екран
    sct_img = sct.grab(monitor)
    img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
    img.save("screenshot.jpg")