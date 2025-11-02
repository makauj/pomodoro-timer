import os
import winsound  # For Windows sound playback
import platform

def play_sound(sound_file: str) -> None:
    """Plays a sound file if the operating system supports it."""
    if platform.system() == "Windows":
        winsound.PlaySound(sound_file, winsound.SND_FILENAME)
    elif platform.system() == "Linux":
        os.system(f"aplay {sound_file} &")  # Requires aplay to be installed
    elif platform.system() == "Darwin":
        os.system(f"afplay {sound_file} &")  # For macOS
    else:
        print("Sound playback is not supported on this OS.")

def play_start_sound() -> None:
    """Plays the sound for the start of a timer stage."""
    play_sound("start_sound.wav")  # Replace with actual sound file path

def play_end_sound() -> None:
    """Plays the sound for the end of a timer stage."""
    play_sound("end_sound.wav")  # Replace with actual sound file path

def play_break_sound() -> None:
    """Plays the sound for the break stage."""
    play_sound("break_sound.wav")  # Replace with actual sound file path