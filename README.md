This program records KBS 1FM for 2 hours.

It needs Chromedriver, ffmpeg, and Selenium(Python package) to run.

You can set recording duration, radio webpage URL and auto-upload to Google Drive.
(You have to enable Google Drive API and have your credentials to use auto-upload.)
Unless mentioned, it will record KBS 1FM for 2 hours and save the recordings locally.
For further information, type `python record_kbs_1fm.py --help`.

If you are using macOS, use caffeinate to prevent stop recording from system sleeping.
(For example: `caffeinate -i python3 record_kbs_1fm.py`)
