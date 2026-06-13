# fetch-gtk

GTK4 system fetch utility. Just a graphical way to see your system specs and telemetry, similar to neofetch or fastfetch, but built with Libadwaita.

I wanted something that showed system info and live hardware usage side by side on a desktop.

Like `Ryzenadj-gtk` and `cpupower-gtk`, it has different color themes and runs fast because it reads directly from sysfs and proc instead of querying other commands.

## What it does

- **System overview**: A classic fetch style screen showing your distro logo, OS, kernel, shell, WM, package count, and memory.
- **Live telemetry**: Live charts for CPU speeds, temperatures, RAM, and disk space.
- **Desktop info**: Shows your GTK theme, active font, icon sets, and session type (Wayland or X11).
- **Color themes**: Switch between different color accents (Ryzen Red, DLSS Green, Arch Blue, etc.) to match your desktop.
- **Copy Fetch**: A button to format and copy the classic terminal ASCII fetch directly to your clipboard.

## Installation

### Arch (makepkg)

```bash
git clone https://github.com/marleylinux/fetch-gtk
cd fetch-gtk
makepkg -si
```

### Other Distros (Installer Script)

```bash
git clone https://github.com/marleylinux/fetch-gtk
cd fetch-gtk
sudo ./install.sh
```

Then launch "fetch-gtk" from your application menu or run `fetch-gtk`.

### Uninstall

```bash
sudo ./uninstall.sh
```

## License

GPL-3.0
