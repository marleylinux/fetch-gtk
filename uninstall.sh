#!/bin/bash
# fetch-gtk uninstaller
# run with: sudo ./uninstall.sh

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./uninstall.sh)"
  exit 1
fi

echo "==> Removing fetch-gtk..."

rm -rf /usr/share/fetch-gtk
rm -f  /usr/bin/fetch-gtk
rm -f  /usr/share/applications/com.marley.fetch-gtk.desktop
for size in 256 512; do
    rm -f "/usr/share/icons/hicolor/${size}x${size}/apps/com.marley.fetch-gtk.png"
done

echo "==> Removing legacy gtkfetch..."
rm -rf /usr/share/gtkfetch
rm -f  /usr/bin/gtkfetch
rm -f  /usr/share/applications/com.marley.gtkfetch.desktop
for size in 256 512; do
    rm -f "/usr/share/icons/hicolor/${size}x${size}/apps/com.marley.gtkfetch.png"
done

update-desktop-database -q 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

echo "==> Uninstall complete."
