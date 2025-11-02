import os
import platform
import shlex
import subprocess

class Notifier:
    """Simple notifier used by the timer. Uses notify-send on Linux if available."""
    def notify(self, message: str) -> None:
        try:
            if platform.system() == "Linux" and shutil_available():
                # use subprocess to avoid blocking the main thread
                subprocess.Popen(["notify-send", "Pomodoro", message], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
            else:
                # Fallback to printing to stdout (safe for tests)
                print(f"[NOTIFY] {message}")
        except Exception:
            # swallow errors so tests don't fail due to desktop integration
            pass

def shutil_available():
    try:
        from shutil import which
        return which("notify-send") is not None
    except Exception:
        return False

def notify_stage_end(stage_name: str) -> None:
    """Notify the user when a timer stage ends."""
    notifier = Notifier()
    notifier.notify(f"{stage_name} is over! Time to switch tasks.")