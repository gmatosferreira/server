# OliveTin Server Control

A lightweight, OliveTin-compatible web interface for executing shell commands and controlling your server from any browser.

Instead of writing custom HTML forms and parsing network requests manually in shell scripts, all actions are now configured in a single, simple [`config.yaml`](file:///home/goncalo/Documentos/Code/server/config.yaml).

---

## Quick Start

### 1. Start the Server
Run the launcher script:
```bash
./server.sh
```
Or directly with Python 3:
```bash
python3 server.py
```
Open your browser at `http://<server-ip>:8888`.

---

## Configuration (`config.yaml`)

To add, edit, or remove buttons, simply edit [`config.yaml`](file:///home/goncalo/Documentos/Code/server/config.yaml). Changes take effect immediately upon page refresh—**no need to restart the server**!

### Example Configuration

```yaml
title: "Pentium 4 Server Power Control"
port: 8888
listenAddress: "0.0.0.0"

actions:
  - title: Say Hello
    shell: echo "Hello World!"
    icon: smile
    onclick: execution-dialog

  - title: Power Off Server
    shell: poweroff
    icon: power
    onclick: confirm
```

### Action Properties

| Field | Description | Example |
| :--- | :--- | :--- |
| `title` | The button label shown in the UI | `Say Hello` |
| `shell` | The shell command to execute on the server | `echo "Hello World!"` |
| `icon` | Icon shown on the button (see supported icons below) | `smile`, `power`, `terminal` |
| `onclick` | Interaction mode when clicked | `execution-dialog` or `confirm` |

### Interaction Modes (`onclick`)

- `execution-dialog`: Opens a modal dialog, runs the shell command, and displays stdout/stderr output with execution time and exit status.
- `confirm`: Prompts the user with a confirmation dialog before executing (ideal for sensitive actions like reboot or power off), then displays the execution dialog with the result.

### Supported Icons

The web interface comes with built-in, offline SVG icons:
- `smile`: Smiley face
- `power`: Power switch icon
- `terminal`: Command line / prompt
- `restart`: Reload / sync arrows
- `play`: Play triangle
- `server`: Server chassis
- `trash`: Trash can

---

## Project Structure

- [`config.yaml`](file:///home/goncalo/Documentos/Code/server/config.yaml): Single configuration file for server settings and actions.
- [`server.py`](file:///home/goncalo/Documentos/Code/server/server.py): Threaded HTTP server handling the API, shell execution, and hot reloading.
- [`index.html`](file:///home/goncalo/Documentos/Code/server/index.html): Responsive dark-theme OliveTin web client (offline-ready, zero CDN dependencies).
- [`server.sh`](file:///home/goncalo/Documentos/Code/server/server.sh): Executable startup script.
