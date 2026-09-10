"""Recording the browser, as a video of the display it draws on.

A headless run leaves nothing behind: a step that passed and a step that hung
look the same afterwards. This gives the browser a virtual X display, points
ffmpeg at it, and lets it run from the first click to the last. The test never
stops to take a picture, so nothing about its timing changes and nothing
between two steps is missed.

The caption is a banner injected into the page rather than drawn into the
video: no filter graph, and it lands in the failure screenshots too. It is
`pointer-events: none`, so hit testing passes straight through it and nothing
the test clicks can be intercepted by it.

A page load throws the banner away with the rest of the document, so it is
registered with the browser as well as with the page: Chrome re-runs it on
every document it opens from then on. `tick()` is the fallback for when that
registration is unavailable.

Nothing here may fail a test. A recorder that cannot record says so and stays
out of the way.
"""

import json
import os
import shutil
import subprocess
import time

# The display, and the browser window filling it.
SCREEN = (1920, 1440)

BANNER = """
function __medperfBanner(text) {
    if (!document.body) { return false; }
    var el = document.getElementById('__medperf_recorder__');
    if (!el) {
        el = document.createElement('div');
        el.id = '__medperf_recorder__';
        el.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:2147483647;'
            + 'pointer-events:none;background:rgba(15,17,21,0.92);color:#fff;'
            + 'font:600 22px/1.35 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;'
            + 'padding:12px 20px;letter-spacing:0.2px;';
        document.body.appendChild(el);
    }
    if (el.textContent !== text) { el.textContent = text; }
    return true;
}
"""

SHOW = BANNER + "\nreturn __medperfBanner(arguments[0]);"

ON_LOAD = BANNER + """
(function () {
    function draw() { __medperfBanner(CAPTION); }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', draw);
    } else {
        draw();
    }
})();
"""


class VirtualDisplay:
    """Somewhere for the browser to draw, on a machine with no screen."""

    def __init__(self, size=SCREEN, first=99, last=128):
        self.size = size
        self.first = first
        self.last = last
        self.number = None
        self.process = None

    @property
    def name(self) -> str:
        return f":{self.number}"

    @property
    def geometry(self) -> str:
        return f"{self.size[0]}x{self.size[1]}"

    def start(self) -> str:
        if not shutil.which("Xvfb"):
            raise RuntimeError("Xvfb is not installed, so there is no display to record")

        for number in range(self.first, self.last):
            if os.path.exists(self.__socket(number)):
                continue
            self.number = number
            self.process = subprocess.Popen(
                ["Xvfb", self.name, "-screen", "0", f"{self.geometry}x24",
                 "-nolisten", "tcp"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if self.__wait():
                os.environ["DISPLAY"] = self.name
                return self.name
            self.stop()

        raise RuntimeError(f"no free X display between :{self.first} and :{self.last}")

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None

    @staticmethod
    def __socket(number: int) -> str:
        return f"/tmp/.X11-unix/X{number}"

    def __wait(self, timeout=10) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if os.path.exists(self.__socket(self.number)):
                return True
            if self.process.poll() is not None:
                return False
            time.sleep(0.1)
        return False


class Recorder:
    """One continuous video of a display, and the caption showing on it."""

    def __init__(self, driver, display, path, fps=10, refresh=1.0):
        self.driver = driver
        self.display = display
        self.path = path
        self.fps = fps
        self.refresh = refresh
        self.text = ""
        self.last = 0.0
        self.process = None
        self.registered = None

    def start(self):
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            print(
                "    (no ffmpeg: nothing will be recorded."
                " `pip install imageio-ffmpeg` to get one)",
                flush=True,
            )
            return None

        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.process = subprocess.Popen(
            [
                ffmpeg, "-y", "-loglevel", "error",
                "-f", "x11grab",
                "-video_size", self.display.geometry,
                "-framerate", str(self.fps),
                "-i", self.display.name,
                # Half size keeps a long run to a few megabytes.
                "-vf", "scale=1280:-2,format=yuv420p",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
                "-movflags", "+faststart",
                self.path,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        return self.path

    def caption(self, text):
        self.text = text
        self.__register()
        self.__show(force=True)

    def tick(self):
        """Puts the caption back, for a browser that would not register it."""
        self.__show()

    def stop(self):
        """Ends the recording, while the browser is still up."""
        if not self.process:
            return None

        try:
            _, errors = self.process.communicate(input=b"q", timeout=60)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
            print("    (the recording had to be killed; it may be truncated)", flush=True)
            errors = b""

        if self.process.returncode not in (0, 255):
            print(
                f"    (video not written: {errors.decode()[:400].strip()})",
                flush=True,
            )
            return None
        if not os.path.exists(self.path) or os.path.getsize(self.path) == 0:
            return None
        return self.path

    def __show(self, force=False):
        now = time.time()
        if not force and now - self.last < self.refresh:
            return
        self.last = now
        try:
            self.driver.execute_script(SHOW, self.text)
        except Exception:
            # Between two pages, or the browser has gone.
            pass

    def __register(self):
        """Draws the caption on every page the browser opens next.

        The banner otherwise lives only as long as its document."""
        try:
            if self.registered:
                self.driver.execute_cdp_cmd(
                    "Page.removeScriptToEvaluateOnNewDocument",
                    {"identifier": self.registered},
                )
            self.registered = self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": ON_LOAD.replace("CAPTION", json.dumps(self.text))},
            ).get("identifier")
        except Exception:
            # Not a Chrome, or the browser has gone. tick() covers it.
            self.registered = None


class NullRecorder:
    """What the test talks to when there is nothing to record onto."""

    def start(self):
        return None

    def caption(self, text):
        pass

    def tick(self):
        pass

    def stop(self):
        return None


def find_ffmpeg():
    """A usable ffmpeg: the system one, or the one imageio-ffmpeg ships."""
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None
