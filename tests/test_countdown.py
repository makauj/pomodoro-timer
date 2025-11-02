import time
import pytest
from src.pomodoro_timer import countdown_timer

def test_countdown_timer(capsys):
    duration = 5  # 5 seconds for testing
    stage_name = "TEST"
    pomodoro_count = 0

    countdown_timer(duration, stage_name, pomodoro_count, sleep_fn=time.sleep)

    captured = capsys.readouterr()
    assert "Time Remaining: 00:00" in captured.out
    assert "DING DING!" in captured.out

def test_countdown_timer_interrupt(capsys):
    duration = 5  # 5 seconds for testing
    stage_name = "TEST"
    pomodoro_count = 0

    with pytest.raises(KeyboardInterrupt):
        countdown_timer(duration, stage_name, pomodoro_count, sleep_fn=lambda x: time.sleep(x))

    captured = capsys.readouterr()
    assert "Timer stopped by user." in captured.out

def test_countdown_timer_negative_duration(capsys):
    duration = -5  # Negative duration should be treated as 0
    stage_name = "TEST"
    pomodoro_count = 0

    countdown_timer(duration, stage_name, pomodoro_count, sleep_fn=time.sleep)

    captured = capsys.readouterr()
    assert "Time Remaining: 00:00" in captured.out
    assert "DING DING!" in captured.out