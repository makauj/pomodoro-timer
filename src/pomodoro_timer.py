import argparse
import time
import os
import threading
from typing import Callable, Optional
from controls import KeyboardControls
from notifier import Notifier
from audio import Audio

# --- Defaults (minutes) ---
DEFAULT_WORK_MIN = 25
DEFAULT_SHORT_BREAK_MIN = 5
DEFAULT_LONG_BREAK_MIN = 15
DEFAULT_POMODOROS_PER_CYCLE = 4


def clear_console() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')


def countdown_timer(
    duration: int,
    stage_name: str,
    pomodoro_count: int,
    notifier: Notifier,
    audio: Audio,
    controls: KeyboardControls,
    *,
    sleep_fn: Callable[[float], None] = time.sleep,
    clear_fn: Callable[[], None] = clear_console,
    print_fn: Callable[..., None] = print,
    end_pause: int = 3,
) -> None:
    if duration < 0:
        duration = 0

    print_fn(f"--- Pomodoro Timer --- | Completed Pomodoros: {pomodoro_count}")
    print_fn("(Press 'p' to pause, 's' to skip, 'q' to quit)\n")

    # Start the controls listener via the controls API (idempotent)
    controls.listen_for_input()

    try:
        while duration >= 0:
            # Check for skip request
            if controls.check_skip():
                clear_fn()
                print_fn(f"\n[SKIPPED] {stage_name} skipped!\n")
                break

            mins, secs = divmod(duration, 60)
            time_format = f"{mins:02d}:{secs:02d}"

            msg = f"[{stage_name}] Time Remaining: {time_format}"
            print_fn(f"\r{msg}\033[K", end='', flush=True)

            if controls.is_paused:
                print_fn(f"\r{msg} [PAUSED]\033[K", end='', flush=True)
                sleep_fn(0.5)
                continue

            try:
                sleep_fn(1)
            except KeyboardInterrupt:
                clear_fn()
                print_fn("\nTimer stopped by user. Goodbye!")
                raise

            duration -= 1
    finally:
        # Ensure the background listener is requested to stop in all cases
        try:
            controls.stop()
        except Exception:
            pass

    clear_fn()
    notifier.notify(f"{stage_name} is over!")
    audio.play_end_sound()
    print_fn(f"\n[DING DING!] {stage_name} is over! Starting next stage...\n")
    print_fn("*************************************************")
    print_fn("***** Take a deep breath and switch tasks *****")
    print_fn("*************************************************\n")
    sleep_fn(end_pause)


def run_pomodoro(
    work_sec: int,
    short_sec: int,
    long_sec: int,
    pomodoros_per_cycle: int = DEFAULT_POMODOROS_PER_CYCLE,
    max_pomodoros: Optional[int] = None,
    *,
    sleep_fn: Callable[[float], None] = time.sleep,
    clear_fn: Callable[[], None] = clear_console,
    print_fn: Callable[..., None] = print,
) -> None:
    """Run the timer using the new Timer class (start/pause/skip/stop).

    This function wraps src.timer.Timer and exposes the same CLI-style
    behavior (periodic console updates + keyboard controls).
    """
    # local import to avoid circular/top-level dependency issues in tests
    from timer import Timer

    controls = KeyboardControls()
    timer = Timer(audio=Audio(), notifier=Notifier(), sleep_fn=sleep_fn)

    # convert seconds -> minutes for Timer.start()
    work_min = max(0, work_sec // 60)
    short_min = max(0, short_sec // 60)
    long_min = max(0, long_sec // 60)
    pomodoros_per_cycle = max(1, int(pomodoros_per_cycle))
    max_pomos = int(max_pomodoros) if max_pomodoros else None

    clear_fn()
    print_fn("Welcome to the Python Pomodoro Timer (wrapped Timer)!")
    print_fn(f"Work: {work_min}m | Short Break: {short_min}m | Long Break: {long_min}m | Cycle: {pomodoros_per_cycle}\n")
    print_fn("Controls: 'p' pause/resume | 's' skip | Ctrl+C to quit\n")

    # start listening for keyboard controls (idempotent)
    controls.listen_for_input()

    try:
        timer.start(work_min, short_min, long_min, pomodoros_per_cycle)

        while True:
            state = timer.get_state()
            mins, secs = divmod(state["remaining"], 60)
            line = f"[{state['stage']}] {mins:02d}:{secs:02d} | Completed: {state['pomodoros_completed']}"
            # update console line
            print_fn(f"\r{line}\033[K", end="", flush=True)

            # react to keyboard controls
            if controls.check_skip():
                timer.skip()

            # sync pause state from controls -> timer
            if controls.is_paused and not state["paused"]:
                timer.pause()
            elif not controls.is_paused and state["paused"]:
                timer.resume()

            # stop when requested by max pomodoros
            if max_pomos is not None and state["pomodoros_completed"] >= max_pomos:
                print_fn("\nReached configured maximum pomodoros. Stopping timer.")
                timer.stop()
                break

            # exit loop if timer stopped for any other reason
            if not state["running"]:
                print_fn("\nTimer stopped.")
                break

            sleep_fn(1.0)
    except KeyboardInterrupt:
        print_fn("\nInterrupted by user; stopping timer...")
        timer.stop()
    finally:
        try:
            controls.stop()
        except Exception:
            pass

    clear_fn()
    print_fn("Goodbye!")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple terminal Pomodoro timer.")
    parser.add_argument("--work", type=int, default=DEFAULT_WORK_MIN, help="Work duration in minutes (default: 25)")
    parser.add_argument("--short", type=int, default=DEFAULT_SHORT_BREAK_MIN, help="Short break duration in minutes (default: 5)")
    parser.add_argument("--long", type=int, default=DEFAULT_LONG_BREAK_MIN, help="Long break duration in minutes (default: 15)")
    parser.add_argument("--pomodoro-cycle", type=int, default=DEFAULT_POMODOROS_PER_CYCLE, help="Pomodoros per cycle before a long break (default: 4)")
    parser.add_argument("--max", type=int, default=0, help="Optional: stop after this many completed pomodoros (0 means run until interrupted)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    work_sec = max(0, args.work) * 60
    short_sec = max(0, args.short) * 60
    long_sec = max(0, args.long) * 60
    pomodoros_per_cycle = max(1, args.pomodoro_cycle)
    max_pomodoros = args.max or None

    run_pomodoro(
        work_sec,
        short_sec,
        long_sec,
        pomodoros_per_cycle=pomodoros_per_cycle,
        max_pomodoros=max_pomodoros,
    )


if __name__ == "__main__":
    main()
