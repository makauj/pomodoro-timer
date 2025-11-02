# Pomodoro Timer

A simple terminal-based Pomodoro timer implemented in Python. This project helps users manage their time effectively using the Pomodoro technique, which involves working in focused intervals followed by short breaks.

## Features

- **Customizable Timer**: Set your own work and break durations.
- **Keyboard Controls**: Pause and skip timer stages using keyboard inputs.
- **Notifications**: Get notified when a work session or break ends.
- **Sound Alerts**: Play sounds at the start and end of each timer stage.
- **Unit Tests**: Comprehensive tests to ensure functionality and reliability.

## Project Structure

```bash
pomodoro-timer
├── src
│   ├── pomodoro_timer.py   # Main logic for the Pomodoro timer
│   ├── controls.py         # Keyboard controls for pausing and skipping
│   ├── notifier.py         # Notification management
│   ├── audio.py            # Sound integration
│   └── __init__.py         # Package initialization
├── tests
│   ├── test_countdown.py   # Unit tests for countdown functionality
│   ├── test_run_pomodoro_flow.py # Unit tests for Pomodoro flow
│   └── conftest.py         # Test configuration and fixtures
├── requirements.txt         # Project dependencies
├── pyproject.toml          # Project metadata and build configuration
├── .gitignore               # Files to ignore in version control
└── README.md                # Project documentation
```

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/makauj/pomodoro-timer.git
   cd pomodoro-timer
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the Pomodoro timer from the command line:

```bash
python src/pomodoro_timer.py --work <work_minutes> --short <short_break_minutes> --long <long_break_minutes> --pomodoro-cycle <number_of_pomodoros> --max <max_pomodoros>
```

### Example

To start a Pomodoro session with 25 minutes of work, 5 minutes of short break, and 15 minutes of long break after every 4 Pomodoros:

```bash
python src/pomodoro_timer.py --work 25 --short 5 --long 15 --pomodoro-cycle 4
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the [MIT License](https://mit-license.org/). See the [LICENSE](LICENSE) file for details.
