<p align="center">
  <img src="src/assets/com.marley.fetch-gtk.png" width="128" height="128" alt="fetch-gtk logo" />
</p>

# fetch-gtk

GTK4 system fetch utility. Just a graphical way to see your system specs and telemetry, similar to neofetch or fastfetch, but built with Libadwaita.

Like `Ryzenadj-gtk` and `cpupower-gtk`, it has different color themes and runs fast because it reads directly from sysfs and proc instead of querying other commands.

## What it does

- **System overview**: A classic fetch style screen showing your distro logo, OS, kernel, shell, WM, package count, and memory.
- **Live telemetry**: Live charts for CPU speeds, temperatures, RAM, and disk space.
- **Desktop info**: Shows your GTK theme, active font, icon sets, and session type (Wayland or X11).
- **Color themes**: Switch between different color accents (Ryzen Red, DLSS Green, Arch Blue, etc.) to match your desktop.
- **Copy Fetch**: A button to format and copy the classic terminal ASCII fetch directly to your clipboard.
## Requirements

- Python 3.11+
- gtk4 + libadwaita + python-gobject

## Install

**Arch (easiest):**

```bash
yay -S fetch-gtk
```

Or build from this repo:

```bash
git clone https://github.com/marleylinux/fetch-gtk
```
```bash
cd fetch-gtk
makepkg -si
```

**Other distros:**

```bash
git clone https://github.com/marleylinux/fetch-gtk
```
```bash
cd fetch-gtk
sudo ./install.sh
```

Then launch "fetch-gtk" from your menu or just run `fetch-gtk`.

## Uninstall

```bash
sudo ./uninstall.sh
```

## License

GPL-3.0

---

### Check out my other apps:

| [<img src="https://raw.githubusercontent.com/marleylinux/cpupower-gtk/main/src/assets/com.marley.cpupower-gtk.png" width="48" height="48" /><br/>cpupower-gtk](https://github.com/marleylinux/cpupower-gtk) | [<img src="https://raw.githubusercontent.com/marleylinux/Ryzenadj-gtk/main/src/assets/com.marley.ryzenadj-gtk.png" width="48" height="48" /><br/>Ryzenadj-gtk](https://github.com/marleylinux/Ryzenadj-gtk) | [<img src="https://raw.githubusercontent.com/marleylinux/FastFlowLM-gtk/main/src/assets/com.marley.FastFlowLM-gtk.png" width="48" height="48" /><br/>FastFlowLM-gtk](https://github.com/marleylinux/FastFlowLM-gtk) | [<img src="https://raw.githubusercontent.com/marleylinux/fetch-gtk/main/src/assets/com.marley.fetch-gtk.png" width="48" height="48" /><br/>fetch-gtk](https://github.com/marleylinux/fetch-gtk) |
|---|---|---|---|
