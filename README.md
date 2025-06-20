This program records KBS 1FM for 2 hours.
It works with Chromedriver and ffmpeg.

You can set how long it will record, set custom radio webpage URL, and enable auto-upload to Google Drive.
(You have to enable Google Drive API and have your credentials to use auto-upload.)
Unless mentioned, it will record KBS 1FM for 2 hours and save the recordings locally in /recordings.
For further information, type `python record_kbs_1fm.py --help`.

If you are using macOS, use caffeinate to prevent it from stop recording as system sleeping.
(For example: `caffeinate -i python3 record_kbs_1fm.py`)

##### Installation

- Linux (deb)

  1. Install Python 3 and FFMPEG

  ```bash
  sudo apt install python3-dev ffmpeg
  ```

  2. Create venv

  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

  3. Install pip packages

  ```bash
  pip3 install --upgrade -r requirements.txt
  ```

