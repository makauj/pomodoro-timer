import tkinter as tk
from tkinter import ttk
from typing import Optional

from audio import Audio
from notifier import Notifier

class PomodoroUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Pomodoro Timer")
        self.resizable(False, False)

        # audio / notifier
        self.audio = Audio()
        self.notifier = Notifier()

        # settings (minutes)
        self.work_min = tk.IntVar(value=25)
        self.short_min = tk.IntVar(value=5)
        self.long_min = tk.IntVar(value=15)
        self.pomos_per_cycle = tk.IntVar(value=4)

        # runtime state
        self._stage = "IDLE"  # "WORK", "SHORT", "LONG", "IDLE"
        self._remaining = 0
        self._pomodoros_completed = 0
        self._running = False
        self._paused = False
        self._after_id: Optional[str] = None

        self._build_ui()

    def _build_ui(self) -> None:
        frm = ttk.Frame(self, padding=12)
        frm.grid()

        # Settings row
        settings = ttk.Frame(frm)
        settings.grid(row=0, column=0, sticky="w")
        ttk.Label(settings, text="Work (min):").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(settings, from_=1, to=180, width=5, textvariable=self.work_min).grid(row=0, column=1, padx=4)
        ttk.Label(settings, text="Short (min):").grid(row=0, column=2, sticky="w")
        ttk.Spinbox(settings, from_=1, to=60, width=5, textvariable=self.short_min).grid(row=0, column=3, padx=4)
        ttk.Label(settings, text="Long (min):").grid(row=0, column=4, sticky="w")
        ttk.Spinbox(settings, from_=1, to=60, width=5, textvariable=self.long_min).grid(row=0, column=5, padx=4)
        ttk.Label(settings, text="Cycle:").grid(row=0, column=6, sticky="w", padx=(8,0))
        ttk.Spinbox(settings, from_=1, to=10, width=3, textvariable=self.pomos_per_cycle).grid(row=0, column=7, padx=4)

        # Status
        self.stage_label = ttk.Label(frm, text="Idle", font=("TkDefaultFont", 14, "bold"))
        self.stage_label.grid(row=1, column=0, pady=(10,0))
        self.time_label = ttk.Label(frm, text="00:00", font=("TkDefaultFont", 24))
        self.time_label.grid(row=2, column=0, pady=(6,10))

        # Controls
        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0)
        self.start_btn = ttk.Button(btns, text="Start", command=self.start)
        self.start_btn.grid(row=0, column=0, padx=4)
        self.pause_btn = ttk.Button(btns, text="Pause", command=self.pause_resume, state="disabled")
        self.pause_btn.grid(row=0, column=1, padx=4)
        self.skip_btn = ttk.Button(btns, text="Skip", command=self.skip, state="disabled")
        self.skip_btn.grid(row=0, column=2, padx=4)
        self.stop_btn = ttk.Button(btns, text="Stop", command=self.stop, state="disabled")
        self.stop_btn.grid(row=0, column=3, padx=4)

        # footer
        self.info_label = ttk.Label(frm, text="Completed: 0")
        self.info_label.grid(row=4, column=0, pady=(8,0))

    def _format_time(self, seconds: int) -> str:
        m, s = divmod(max(0, seconds), 60)
        return f"{m:02d}:{s:02d}"

    def _set_stage(self, stage: str, duration_sec: int) -> None:
        self._stage = stage
        self._remaining = duration_sec
        self.stage_label.config(text=f"{stage}")
        self.time_label.config(text=self._format_time(self._remaining))

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._paused = False
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal", text="Pause")
        self.skip_btn.config(state="normal")
        self.stop_btn.config(state="normal")
        # begin with a work stage
        self._set_stage("WORK", self.work_min.get() * 60)
        self.audio.play_start_sound()
        self._tick()

    def pause_resume(self) -> None:
        if not self._running:
            return
        self._paused = not self._paused
        self.pause_btn.config(text="Resume" if self._paused else "Pause")

    def skip(self) -> None:
        if not self._running:
            return
        # end current stage immediately
        self._on_stage_end(skipped=True)

    def stop(self) -> None:
        self._running = False
        self._paused = False
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="Pause")
        self.skip_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self._set_stage("IDLE", 0)

    def _on_stage_end(self, skipped: bool = False) -> None:
        # notify and sound
        if not skipped:
            self._pomodoros_completed += 1 if self._stage == "WORK" else 0

        self.info_label.config(text=f"Completed: {self._pomodoros_completed}")
        self.notifier.notify(f"{self._stage} ended (skipped: {skipped})")
        self.audio.play_end_sound()

        # decide next stage
        if self._stage == "WORK":
            # choose short or long break
            if self._pomodoros_completed > 0 and (self._pomodoros_completed % self.pomos_per_cycle.get() == 0):
                self._set_stage("LONG BREAK", self.long_min.get() * 60)
            else:
                self._set_stage("SHORT BREAK", self.short_min.get() * 60)
        else:
            # after break go to work
            self._set_stage("WORK", self.work_min.get() * 60)

    def _tick(self) -> None:
        if not self._running:
            return
        if self._paused:
            # update UI but do not decrement
            self._after_id = self.after(1000, self._tick)
            return

        if self._remaining <= 0:
            # stage finished
            self._on_stage_end(skipped=False)
            # small pause then continue next stage
            self._after_id = self.after(800, self._tick)
            return

        # decrement and schedule next tick
        self._remaining -= 1
        self.time_label.config(text=self._format_time(self._remaining))
        self._after_id = self.after(1000, self._tick)

if __name__ == "__main__":
    # Run with: PYTHONPATH=src python3 src/gui_tk.py
    app = PomodoroUI()
    app.mainloop()