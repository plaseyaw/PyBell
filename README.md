PyBell

[![License: GPL v3](https://img.shields.io/badge/License that allows users to schedule sounds to play at specific times on selected days. The app features a user-friendly GUI built with Tkinter and supports multiple schedules with activation, modification, and deletion capabilities.
Features

    Schedule sound playback at specified times with second precision.

    Choose one or more days for each schedule.

    Add, modify, duplicate, delete, and activate/deactivate schedules.

    Save and load schedules from a JSON file.

    Minimized to system tray with Pystray integration.

    Supports .mp3, .wav, and .ogg sound files.

    Error handling and logging for playback issues.

    About window with version and author info, plus user manual.

Getting Started
Prerequisites

Make sure you have Python 3.7 or above installed along with the following packages:

    pygame

    pystray

    Pillow

Install dependencies via pip:

text
pip install -r requirements.txt

Running the App

Clone this repository, navigate to the project directory, and run:

text
python your_script_name.py

Replace your_script_name.py with the main script filename.
Usage

    Set the desired time using hour, minute, and second selectors.

    Browse and select the sound file you want to play.

    Select days on which the schedule will be active.

    Use buttons to add, modify, duplicate, delete, or activate schedules.

    Save schedules to persist them.

    Access the About window or User Manual from the main GUI.

Contributing

Contributions are welcome! Please open issues or pull requests to improve PyBell.
License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.