import os
import platform
import subprocess

def notify(title: str, message: str) -> None:
    """Send a notification to the user."""
    if platform.system() == "Linux":
        subprocess.run(["notify-send", title, message])
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["osascript", "-e", f'display notification "{message}" with title "{title}"'])
    elif platform.system() == "Windows":
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=10)
    else:
        print(f"Notification: {title} - {message}")

def notify_stage_end(stage_name: str) -> None:
    """Notify the user when a timer stage ends."""
    notify("Pomodoro Timer", f"{stage_name} is over! Time to switch tasks.")