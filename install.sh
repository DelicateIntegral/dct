#!/bin/bash

# Change to the directory where the script is located
cd "$(dirname "$0")"

# Check if Python 3.12 or newer is installed
PYTHON_PATH=$(which python3)
IS_PYTHON_312=$($PYTHON_PATH -c "import sys; print(sys.version_info >= (3, 12))")

if [ "$IS_PYTHON_312" = "True" ]; then
    echo "Python 3.12 or newer is installed."
else
    echo "Python 3.12 or newer is not installed."
    read -n 1 -s -p "Press any key to exit..."
    exit 1
fi

# Ask user for installation path
read -p "Enter the installation path: " INSTALL_PATH

# Validate the provided path
if [ ! -d "$INSTALL_PATH" ]; then
    echo "The path \"$INSTALL_PATH\" does not exist."
    read -n 1 -s -p "Press any key to exit..."
    exit 1
fi

# Install as Python CLI package
TOOL_PATH="$INSTALL_PATH/dct"
mkdir -p "$TOOL_PATH"

# Create the virtual environment
VENV_PATH="$HOME/python/env/cyoaenv"
python3 -m venv "$VENV_PATH"

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Upgrade pip and install poetry
pip install --upgrade pip
pip install poetry

# Run poetry install
poetry install

# Deactivate the virtual environment
deactivate

# Create launch-dct.sh
    cat <<EOL > "$TOOL_PATH/launch-dct.sh"
#!/bin/bash
source "$VENV_PATH/bin/activate"
dct
deactivate
EOL
chmod +x "$TOOL_PATH/launch-dct.sh"

# Create desktop shortcut
DESKTOP_ENTRY="$HOME/Desktop/dct.desktop"
    cat <<EOL > "$DESKTOP_ENTRY"
[Desktop Entry]
Version=1.0
Type=Application
Name=dct
Exec="$INSTALL_PATH/dct/launch-dct.sh"
Icon=utilities-terminal
Terminal=true
EOL
chmod +x "$DESKTOP_ENTRY"

# Create menu entry
MENU_ENTRY="$HOME/.local/share/applications/dct.desktop"
cp "$DESKTOP_ENTRY" "$MENU_ENTRY"

echo "Done! The program has been installed at \"$TOOL_PATH/launch-dct.sh\" and shortcuts created."
read -n 1 -s -p "Press any key to exit..."
exit