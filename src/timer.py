import threading
import time
from typing import Optional, Dict

from audio import Audio
from notifier import Notifier

Stage = str  # "WORK", "SHORT_BREAK", "LONG_BREAK", "IDLE"

class Timer:
    """Threaded, test-friendly Pomodoro timer with start/pause/skip/stop APIs."""

    def __init__(self, audio: Optional[Audio] = None, notifier: Optional[Notifier] = None, sleep_fn=time.sleep):
        self.audio = audio or Audio()
        self.notifier = notifier or Notifier()
        self.sleep_fn = sleep_fn

        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_requested = False

        # public state
        self.stage: Stage = "IDLE"
        self.remaining: int = 0
        self.running: bool = False
        self.paused: bool = False
        self.pomodoros_completed: int = 0

        # configuration (seconds)
        self._work_sec = 25 * 60
        self._short_sec = 5 * 60
        self._long_sec = 15 * 60
        self._pomos_per_cycle = 4

        # skip flag + throttle to avoid rapid repeated skips
        self._skip_requested = False
        self._last_skip_at = 0.0
        self._skip_cooldown = 0.25  # seconds

    def start(self, work_min: int = 25, short_min: int = 5, long_min: int = 15, pomos_per_cycle: int = 4) -> None:
        with self._lock:
            if self.running:
                return
            self._work_sec = max(0, int(work_min)) * 60
            self._short_sec = max(0, int(short_min)) * 60
            self._long_sec = max(0, int(long_min)) * 60
            self._pomos_per_cycle = max(1, int(pomos_per_cycle))

            self.pomodoros_completed = 0
            self._stop_requested = False
            self._skip_requested = False
            self._last_skip_at = 0.0
            self.stage = "WORK"
            self.remaining = self._work_sec
            self.running = True
            self.paused = False

            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            try:
                self.audio.play_start_sound()
            except Exception:
                pass

    def pause(self) -> None:
        with self._lock:
            if not self.running:
                return
            self.paused = True

    def resume(self) -> None:
        with self._lock:
            if not self.running:
                return
            self.paused = False

    def toggle_pause(self) -> None:
        with self._lock:
            if not self.running:
                return
            self.paused = not self.paused

    def skip(self) -> None:
        with self._lock:
            if not self.running:
                return
            now = time.time()
            if now - self._last_skip_at < self._skip_cooldown:
                # ignore spurious/rapid skips
                return
            self._last_skip_at = now
            self._skip_requested = True

    def stop(self) -> None:
        with self._lock:
            if not self.running:
                # ensure state is idle
                self.running = False
                self.paused = False
                self.stage = "IDLE"
                self.remaining = 0
                return
            self._stop_requested = True
            self.running = False
            self.paused = False
        # thread is daemon; join best-effort but don't block forever
        if self._thread:
            try:
                self._thread.join(timeout=1.0)
            except Exception:
                pass
        with self._lock:
            self.stage = "IDLE"
            self.remaining = 0

    def _run(self) -> None:
        try:
            while True:
                with self._lock:
                    if self._stop_requested:
                        break
                    if self.paused:
                        pass
                    elif self._skip_requested:
                        # consume skip and mark stage end by setting remaining to 0
                        self._skip_requested = False
                        self.remaining = 0
                    elif self.remaining <= 0:
                        # end of stage
                        self._on_stage_end()
                    else:
                        # normal countdown
                        pass

                    running = self.running
                    paused = self.paused
                    remaining = self.remaining

                if not running:
                    break

                if paused:
                    self.sleep_fn(0.5)
                    continue

                if remaining > 0:
                    self.sleep_fn(1.0)
                    with self._lock:
                        # decrement safely
                        # guard double-check in case skip/end changed remaining
                        if self.remaining > 0:
                            self.remaining = max(0, self.remaining - 1)
                else:
                    # small sleep so loop doesn't spin tight after stage end
                    self.sleep_fn(0.1)
        finally:
            # ensure running flag cleared on exit
            with self._lock:
                self.running = False
                # do not reset stage/remaining here so clients can inspect final state
            # best-effort cleanup: no blocking I/O here

    def _on_stage_end(self) -> None:
        # Called while holding lock context in caller; adjust carefully
        # Do minimal work under lock then perform I/O outside the lock
        with self._lock:
            finished_stage = self.stage
            # update completed count for work
            if finished_stage == "WORK":
                self.pomodoros_completed += 1

            # choose next stage
            if finished_stage == "WORK":
                if (self.pomodoros_completed % self._pomos_per_cycle) == 0:
                    next_stage = "LONG_BREAK"
                    next_duration = self._long_sec
                else:
                    next_stage = "SHORT_BREAK"
                    next_duration = self._short_sec
            else:
                next_stage = "WORK"
                next_duration = self._work_sec

            # set next stage state
            self.stage = next_stage
            self.remaining = next_duration

        # perform I/O without holding lock (must be non-blocking / robust)
        try:
            self.notifier.notify(f"{finished_stage} finished; next: {self.stage}")
        except Exception:
            pass
        try:
            self.audio.play_end_sound()
        except Exception:
            pass

    def get_state(self) -> Dict:
        with self._lock:
            return {
                "stage": self.stage,
                "remaining": int(self.remaining),
                "running": bool(self.running),
                "paused": bool(self.paused),
                "pomodoros_completed": int(self.pomodoros_completed),
                "work_min": int(self._work_sec // 60),
                "short_min": int(self._short_sec // 60),
                "long_min": int(self._long_sec // 60),
                "pomos_per_cycle": int(self._pomos_per_cycle),
            }
