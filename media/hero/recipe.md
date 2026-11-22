# Hero: Fener, a seamless 7 s loop

Chosen by Özcan on 2026-11-22 from three loops (Fener, Ayna, Ada), with no text over it. Rendered headless in [pc_graphics](https://github.com/OzcanOrhanDemirci/pc_graphics), scene `fener`, view A: one half turn of the lamp at the scene's own speed (lamp.period 14 s, so the picture repeats every 7 s), the waves rounded to whole periods so the sea closes too; each frame averages 64 jittered samples. Then `python tools/hero.py` crops to 2:1, takes every second frame (15 fps) and writes the WebP.

```
cd C:/dev/pc_graphics
cmd /c C:\dev\pc_graphics\build.bat
./build/pc_graphics.exe --scene fener --headless --loop 210 --seconds 7 --frames 64 --width 1920 --height 1080  --out C:/Temp/vitrin/hero/fener-yavas/frames
# seam check: the frame at t = T must equal frame 0
./build/pc_graphics.exe --scene fener --headless --loop 1 --seconds 7 --time 7 --frames 64 --width 1920 --height 1080  --out C:/Temp/vitrin/hero/fener-yavas/seam
```

If the frames are rendered elsewhere, point `frames` in `recipe.json` at them. The seam check: the frame at t = 7 s must equal frame 0.
