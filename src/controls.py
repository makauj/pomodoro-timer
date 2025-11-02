import threading
import sys
import time
import platform
from typing import Optional

# Unix-only imports guarded at runtime
try:
    import termios
    import tty
    import select
except Exception:
    termios = None  # type: ignore
    tty = None  # type: ignore
    select = None  # type: ignore

class KeyboardControls:
    """Cross-platform background keyboard listener for pause/skip.

    API expected by pomodoro_timer.py:
      - listen_for_input() -> starts background daemon (idempotent)
      - is_paused: bool attribute
      - check_skip() -> bool (consumes the skip flag)
      - stop() -> request listener stop (restores terminal on Unix)
    """

    def __init__(self) -> None:
        self.is_paused = False
        self._skip_requested = False
        self._stop_requested = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def listen_for_input(self) -> None:
        """Start the background listener thread (safe to call multiple times)."""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run_listener, daemon=True)
        self._thread.start()

    def _run_listener(self) -> None:
        """Platform-specific listener loop."""
        if platform.system() == "Windows":
            self._run_windows()
        else:
            self._run_unix()

    def _run_windows(self) -> None:
        try:
            import msvcrt  # type: ignore
        except Exception:
            return  # no windows console support available

        while not self._stop_requested:
            if msvcrt.kbhit():
                try:
                    ch = msvcrt.getwch().lower()
                except Exception:
                    try:
                        ch = msvcrt.getch().decode(errors="ignore").lower()
                    except Exception:
                        ch = ""
                self._handle_key(ch)
            time.sleep(0.05)

    def _run_unix(self) -> None:
        # If stdin is not a tty (e.g. running tests), do nothing.
        if not sys.stdin or not sys.stdin.isatty() or termios is None:
            return

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while not self._stop_requested:
                # use select to avoid blocking read and allow polite shutdown
                if select and select.select([sys.stdin], [], [], 0.1)[0]:
                    ch = sys.stdin.read(1)
                    if ch:
                        self._handle_key(ch.lower())
                else:
                    # sleep small to reduce CPU usage if select isn't available
                    time.sleep(0.05)
        finally:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except Exception:
                pass

    def _handle_key(self, ch: str) -> None:
        """Interpret keys: 'p' toggle pause, 's' request skip, 'q' stop listener."""
        with self._lock:
            if ch == "p":
                self.is_paused = not self.is_paused
            elif ch == "s":
                self._skip_requested = True
            elif ch == "q":
                self._stop_requested = True

    def check_skip(self) -> bool:
        """Return True once when a skip was requested (consumes flag)."""
        with self._lock:
            if self._skip_requested:
                self._skip_requested = False
                return True
        return False

    def stop(self, join_timeout: float = 0.5) -> None:
        """Request the listener to stop and join the thread (best-effort)."""
        self._stop_requested = True
        if self._thread:
            self._thread.join(timeout=join_timeout)

class TimerControls:
    def __init__(self):
        self.paused = False
        self.skip = False
        self.listener_thread = threading.Thread(target=self.listen_for_controls)
        self.listener_thread.daemon = True
        self.listener_thread.start()

    def listen_for_controls(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setraw(sys.stdin.fileno())
        try:
            while True:
                ch = sys.stdin.read(1)
                if ch == 'p':  # Pause
                    self.paused = not self.paused
                elif ch == 's':  # Skip
                    self.skip = True
                time.sleep(0.1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def is_paused(self):
        return self.paused

    def should_skip(self):
        if self.skip:
            self.skip = False
            return True
        return False

def main():
    controls = TimerControls()
    try:
        while True:
            if controls.is_paused():
                print("Timer is paused. Press 'p' to resume.")
            else:
                print("Timer is running.")
            if controls.should_skip():
                print("Timer stage skipped.")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting timer controls.")

if __name__ == "__main__":
    main()