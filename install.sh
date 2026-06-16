#!/bin/bash
# fetch-gtk installer
# run with: sudo ./install.sh

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./install.sh)"
  exit 1
fi

# Check for python3
if ! command -v python3 &> /dev/null; then
  echo "Error: python3 is not installed. Please install Python 3." >&2
  exit 1
fi

# Check for PyGObject
if ! python3 -c "import gi" &> /dev/null; then
  echo "Warning: Python GObject (PyGObject) is not installed." >&2
  echo "Please install it using your package manager (e.g., python-gobject, python3-gi, or python3-gobject)." >&2
fi

echo "==> Installing fetch-gtk..."

# Remove legacy gtkfetch
echo "  -> Removing legacy gtkfetch if present..."
rm -rf /usr/share/gtkfetch
rm -f  /usr/bin/gtkfetch
rm -f  /usr/share/applications/com.marley.gtkfetch.desktop
for size in 256 512; do
    rm -f "/usr/share/icons/hicolor/${size}x${size}/apps/com.marley.gtkfetch.png"
done

INSTALL_DIR="/usr/share/fetch-gtk"
BIN_DIR="/usr/bin"
APP_DIR="/usr/share/applications"

# make the folders we need
mkdir -p "$INSTALL_DIR"
mkdir -p "$APP_DIR"

# copy python files and assets and set up permissions
echo "  -> Copying Python files and assets..."
cp src/*.py "$INSTALL_DIR/"
cp -r src/assets "$INSTALL_DIR/"
chmod 644 "$INSTALL_DIR"/*.py
chmod 755 "$INSTALL_DIR/app.py"
chmod 755 "$INSTALL_DIR/backend.py"
find "$INSTALL_DIR/assets" -type d -exec chmod 755 {} +
find "$INSTALL_DIR/assets" -type f -exec chmod 644 {} +

# copy the app icons to the system icon folder
for size in 16 24 32 48 64 128 256 512; do
    ICON_DIR="/usr/share/icons/hicolor/${size}x${size}/apps"
    mkdir -p "$ICON_DIR"
    if [ -f "src/assets/icons/${size}x${size}/com.marley.fetch-gtk.png" ]; then
        cp "src/assets/icons/${size}x${size}/com.marley.fetch-gtk.png" "$ICON_DIR/com.marley.fetch-gtk.png"
        chmod 644 "$ICON_DIR/com.marley.fetch-gtk.png"
    fi
done

# Install desktop entry
echo "  -> Installing .desktop file..."
cp com.marley.fetch-gtk.desktop "$APP_DIR/com.marley.fetch-gtk.desktop"
chmod 644 "$APP_DIR/com.marley.fetch-gtk.desktop"

# create launcher
echo "  -> Creating launcher..."
cat > "$BIN_DIR/fetch-gtk" << EOF
#!/bin/sh
export PYTHONPATH="$INSTALL_DIR:\$PYTHONPATH"
exec python3 "$INSTALL_DIR/app.py" "\$@"
EOF
chmod 755 "$BIN_DIR/fetch-gtk"

# update databases
update-desktop-database -q 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

echo ""
echo "==> Installation complete!"
echo "    Launch 'fetch-gtk' from your application menu, or run: fetch-gtk"
echo ""

if [ -t 0 ]; then
    read -p "Press Enter to exit..."
fi
