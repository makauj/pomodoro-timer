import os
import platform
import shlex
import subprocess
from typing import Optional

# Try to import winsound only on Windows
try:
    if platform.system() == "Windows":
        import winsound  # type: ignore
    else:
        winsound = None  # type: ignore
except Exception:
    winsound = None  # type: ignore

def _has_cmd(cmd: str) -> bool:
    from shutil import which
    return which(cmd) is not None

def _spawn_cmd(cmd_list):
    try:
        subprocess.Popen(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
    except Exception:
        # best-effort fallback to printing bell
        try:
            print("\a", end="", flush=True)
        except Exception:
            pass

def play_sound(sound_file: str) -> None:
    """Plays a sound file if possible; falls back to system bell."""
    system = platform.system()
    if system == "Windows" and winsound:
        try:
            # winsound.PlaySound is async when SND_ASYNC specified
            winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass
    elif system == "Linux" and _has_cmd("aplay"):
        try:
            _spawn_cmd(["aplay", sound_file])
        except Exception:
            pass
    elif system == "Darwin" and _has_cmd("afplay"):
        try:
            _spawn_cmd(["afplay", sound_file])
        except Exception:
            pass
    else:
        # graceful fallback: ASCII bell
        try:
            print("\a", end="", flush=True)
        except Exception:
            pass

def play_start_sound() -> None:
    """Plays the sound for the start of a timer stage."""
    play_sound("start_sound.wav")  # Replace with actual sound file path

def play_end_sound() -> None:
    """Plays the sound for the end of a timer stage."""
    play_sound("end_sound.wav")  # Replace with actual sound file path

def play_break_sound() -> None:
    """Plays the sound for the break stage."""
    play_sound("break_sound.wav")  # Replace with actual sound file path

class Audio:
    """Simple wrapper class expected by other modules."""
    def play_start_sound(self) -> None:
        play_start_sound()

    def play_end_sound(self) -> None:
        play_end_sound()

    def play_break_sound(self) -> None:
        play_break_sound()