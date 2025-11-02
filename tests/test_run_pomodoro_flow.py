import pytest
from unittest.mock import patch, MagicMock
from src.pomodoro_timer import run_pomodoro

@pytest.fixture
def mock_sleep():
    with patch('time.sleep', return_value=None) as mock:
        yield mock

@pytest.fixture
def mock_clear_console():
    with patch('src.pomodoro_timer.clear_console', return_value=None) as mock:
        yield mock

@pytest.fixture
def mock_print():
    with patch('builtins.print') as mock:
        yield mock

def test_run_pomodoro_normal_flow(mock_sleep, mock_clear_console, mock_print):
    work_sec = 1  # 1 second for testing
    short_sec = 1  # 1 second for testing
    long_sec = 1  # 1 second for testing
    pomodoros_per_cycle = 2  # 2 pomodoros before a long break
    max_pomodoros = 0  # run until interrupted

    with patch('src.pomodoro_timer.countdown_timer') as mock_countdown:
        run_pomodoro(work_sec, short_sec, long_sec, pomodoros_per_cycle, max_pomodoros)

        assert mock_countdown.call_count == 4  # 2 work + 2 breaks
        assert mock_countdown.call_args_list[0][0][0] == work_sec  # first call is work
        assert mock_countdown.call_args_list[1][0][0] == short_sec  # first short break
        assert mock_countdown.call_args_list[2][0][0] == work_sec  # second work
        assert mock_countdown.call_args_list[3][0][0] == long_sec  # long break after 2 pomodoros

def test_run_pomodoro_with_max_pomodoros(mock_sleep, mock_clear_console, mock_print):
    work_sec = 1  # 1 second for testing
    short_sec = 1  # 1 second for testing
    long_sec = 1  # 1 second for testing
    pomodoros_per_cycle = 2  # 2 pomodoros before a long break
    max_pomodoros = 3  # stop after 3 completed pomodoros

    with patch('src.pomodoro_timer.countdown_timer') as mock_countdown:
        run_pomodoro(work_sec, short_sec, long_sec, pomodoros_per_cycle, max_pomodoros)

        assert mock_countdown.call_count == 6  # 3 work + 2 short breaks + 1 long break
        assert mock_countdown.call_args_list[0][0][0] == work_sec  # first call is work
        assert mock_countdown.call_args_list[1][0][0] == short_sec  # first short break
        assert mock_countdown.call_args_list[2][0][0] == work_sec  # second work
        assert mock_countdown.call_args_list[3][0][0] == short_sec  # second short break
        assert mock_countdown.call_args_list[4][0][0] == work_sec  # third work
        assert mock_countdown.call_args_list[5][0][0] == long_sec  # long break after 2 pomodoros

def test_run_pomodoro_interrupted(mock_sleep, mock_clear_console, mock_print):
    work_sec = 1  # 1 second for testing
    short_sec = 1  # 1 second for testing
    long_sec = 1  # 1 second for testing
    pomodoros_per_cycle = 2  # 2 pomodoros before a long break
    max_pomodoros = 0  # run until interrupted

    with patch('src.pomodoro_timer.countdown_timer', side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            run_pomodoro(work_sec, short_sec, long_sec, pomodoros_per_cycle, max_pomodoros)

    mock_print.assert_called_with("\nTimer interrupted by user. Exiting gracefully.")