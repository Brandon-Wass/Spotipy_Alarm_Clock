# Spotify Alarm Clock for Raspberry Pi

## Overview
This repository contains the source code for a Spotify Alarm Clock, designed specifically for use on a Raspberry Pi. This program not only acts as a regular alarm clock but also integrates with Spotify to play your favorite tracks. The Raspberry Pi setup requires the use of the dtoverlay=hifiberry-dac and the installation of Raspotify, configured to output to the Hifiberry device. The alarm sound is played through a different audio output, such as a 3.5mm audio jack or an HDMI audio device, ensuring a seamless experience.

## Requirements
- Raspberry Pi with dtoverlay=hifiberry-dac
- Raspotify installed and configured to output to the Hifiberry device
- A separate default audio output (other than the one used by Raspotify)
- Python 3.x

## Installation
1. Clone this repository.
2. Install the required Python libraries:
   ```
   pip install pygame psutil spotipy gpiozero
   ```
3. Configure your Spotify API credentials in `spotify_config.json`.
4. Make sure your Raspberry Pi is set up with the Hifiberry DAC and Raspotify as mentioned above.

## Configuration
- Enter your Spotify API details in `spotify_config.json` file.
- Adjust the audio output settings on your Raspberry Pi to match your setup.
- Enter your spotify login credentials in the /etc/raspotify/conf file.
- Ensure Raspotify device name is set to "Pi". This will allow the program to automatically enable the Pi for playback and control.
- Reboot your pi or restart the raspotify service.

## Usage
- Run `spotipy_alarm_clock.py` to start the application. The program displays a clock interface and allows you to set alarms. When an alarm goes off, it plays a sound through the default audio output and can also play music from Spotify on the Hifiberry device.
- You may need to start a playlist or song on spotify from another device before playback controls will work.

### Features
- Display time with a clean round-clock interface.
- Set alarms with an easy-to-use interface.
- Play alarm sound through your default audio output device.
- Control Spotify playback (Play/Pause, Next, Previous) directly from the interface.
- Display CPU usage and temperature for Raspberry Pi health monitoring.
- Dynamic updates of the currently playing Spotify track.

### Coming Soon...
- Spotify playlist scrolling, song selection, and song and playlist searching.

## Contributing
Contributions to this project are welcome! Please adhere to the GNU GPL v3.0 guidelines when contributing.

## License
This project is licensed under the GNU GPL v3.0 - see the LICENSE file for details.

---

*Note: This program is specifically designed for use with Raspberry Pi hardware and configurations as mentioned above. It may require modifications for use in other environments.*
