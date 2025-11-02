import threading
import termios
import tty
import sys
import time

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