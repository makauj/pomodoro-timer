import os
import platform
import shlex

class Notifier:
    """Simple notifier used by the timer. Uses notify-send on Linux if available."""
    def notify(self, message: str) -> None:
        try:
            if platform.system() == "Linux" and os.system("which notify-send >/dev/null 2>&1") == 0:
                os.system(f'notify-send "Pomodoro" {shlex.quote(message)}')
            else:
                # Fallback to printing to stdout (safe for tests)
                print(f"[NOTIFY] {message}")
        except Exception:
            # swallow errors so tests don't fail due to desktop integration
            pass

def notify_stage_end(stage_name: str) -> None:
    """Notify the user when a timer stage ends."""
    notifier = Notifier()
    notifier.notify(f"{stage_name} is over! Time to switch tasks.")