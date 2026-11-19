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
    group: General

  - title: Transmission Web UI
    url: http://xp:9091
    icon: broadcast
    color: "#10b981"
    group: Links

  - title: Power Off Server
    shell: poweroff
    icon: power
    onclick: confirm
    color: "#dc2626"
    group: Power
```

### Action Properties

| Field | Description | Example |
| :--- | :--- | :--- |
| `title` | The button label shown in the UI | `Say Hello` |
| `shell` | The shell command to execute on the server (omit if using `url`) | `echo "Hello World!"` |
| `url` | Optional URL to open in a new tab (`link` is also accepted as an alias) | `http://xp:9091` |
| `group` | Optional group name to organize buttons under labeled sections | `System`, `Media`, `Power` |
| `icon` | Icon shown on the button (see supported icons below) | `smile`, `power`, `terminal` |
| `onclick` | Interaction mode when clicked (for `shell` actions) | `execution-dialog` or `confirm` |
| `color` | Optional custom theme color (hex code only, e.g. `"#dc2626"` or `"#10b981"`) | `"#dc2626"`, `"#2563eb"` |

### Button Groups (`group`)

- Add a `group` field to actions to organize them into separate labeled sections in the UI.
- Groups appear in the order they are first defined in `config.yaml`.
- If no actions define a `group`, all buttons render in a single flat grid.

### Link Buttons (`url`)

- Use `url` (or `link`) instead of `shell` to create a shortcut button that opens in a new browser tab (`target="_blank"`).
- Link buttons display a subtle external-link indicator in the top-right corner.

### Interaction Modes (`onclick`)

- `execution-dialog`: Opens a modal dialog, runs the shell command, and displays stdout/stderr output with execution time and exit status.
- `confirm`: Prompts the user with a confirmation dialog before executing (ideal for sensitive actions like reboot or power off), then displays the execution dialog with the result.

### Supported Icons (Bootstrap Icons)

The UI now uses **Bootstrap Icons**. You can specify standard aliases or any icon name directly from the [Bootstrap Icons library](https://icons.getbootstrap.com/):

- `smile`: `bi-emoji-smile`
- `power`: `bi-power`
- `terminal`: `bi-terminal`
- `restart` / `reboot`: `bi-arrow-clockwise`
- `server`: `bi-hdd-network`
- `disk`: `bi-hdd`
- `cpu`: `bi-cpu`
- `memory`: `bi-memory`
- `play` / `stop`: `bi-play-fill` / `bi-stop-fill`
- Or any Bootstrap icon directly, e.g. `icon: bi-shield-lock`, `icon: wifi`, `icon: folder`

---

## Project Structure

- [`config.yaml`](file:///home/goncalo/Documentos/Code/server/config.yaml): Single configuration file for server settings and actions.
- [`server.py`](file:///home/goncalo/Documentos/Code/server/server.py): Threaded HTTP server handling the API, shell execution, and hot reloading.
- [`index.html`](file:///home/goncalo/Documentos/Code/server/index.html): Responsive dark-theme OliveTin web client (offline-ready, zero CDN dependencies).
- [`server.sh`](file:///home/goncalo/Documentos/Code/server/server.sh): Executable startup script.
