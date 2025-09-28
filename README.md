# Yealink T46S Remote Control & Call Logger

This repository contains a set of scripts and tools for remotely controlling a Yealink T46S IP phone and logging call activity. It includes:

- A web interface for call control and log viewing
- A syslog server to parse and store call data
- An Electron overlay for quick access to call controls

## 🚀 Features

- 📞 Remote call control (answer, decline, hold, mute, transfer)
- 📋 Real-time call logging via syslog
- 🌐 Web interface served on `localhost:8080`
- 🖥️ Electron overlay with persistent controls
- 📁 JSON and text-based call logs

## 📁 Repository Contents

- `phoneControls.sh`  
  Shell script to launch the Python services (`webServer.py` and `syslogServer.py`).

- `webServer.py`  
  Python script that runs a web server on `localhost:8080`, serving the control interface and displaying the call log.

- `syslogServer.py`  
  Python script that acts as a syslog server, receiving messages from the Yealink phone, parsing call data, saving it to `cid_status.json`, and logging all messages to `call_log.txt`.

- `index.html`  
  Web page served by `webServer.py`. Displays call control buttons, transfer options, macros, and the call log.

- `overlay.html`: UI for the overlay bar (bottom-right of screen)

- `yealink-overlay/`  
  Contains files for the Electron overlay:
  - `main.js`: Electron logic for rendering and controlling the overlay
  - `overlay.log`: Log file for overlay activity
  - `package.json`: Electron app configuration

- `resources/`  
  Folder containing all icons used in the web and overlay interfaces.

- `syslog/`  
  Contains files for the syslog server:
  - `cid_status.json`: JSON file storing parsed call data from the syslog server
  - `call_log.txt`: Text log of all syslog messages received from the phone

- `webServer.log`  
  Log file for the web server's background activity.

- `syslogServer.log`  
  Log file for the syslog server's background activity.

## 🛠️ Requirements

- Python 3.8+
- Electron (for overlay)
- Basic shell environment

## Setup

- Configure the Yealink phone from their dashboard, enable remote control, setup syslog messages, and add servers IP as a trusted address
- Enter the IP address of the phone into 'webServer.py', along with the username and password
- Copy the file locations of the server and overlay directories into the 'phoneControls.sh' script
- Launch the script, should start the overlay, and navigating to 'localhost:8080' should bring up the web dashboard.
