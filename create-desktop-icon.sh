#!/bin/bash
# Desktop Icon Creator for ADALM-Pluto Spectrum Analyzer
# Based on the Desktop Icon Creation Guide

# Configuration
APP_NAME="ADALM-Pluto Spectrum Analyzer"
APP_DESCRIPTION="Professional spectrum analysis and RF monitoring toolkit for ADALM-Pluto SDR"
APP_DIR="/home/dragos/rf-kit/pluto-sdr/ADALM-Pluto-Spectrum-Analyzer"
APP_EXECUTABLE="$APP_DIR/pluto_menu.py"
APP_ICON="$APP_DIR/Pluto.png"
CATEGORIES="Network;System;X-HamRadio;X-SDR;"
KEYWORDS="pluto;sdr;spectrum;analyzer;rf;signal;monitoring;adalm;radio;frequency;"
DESKTOP_FILE_NAME="ADALM-PlutoSpectrumAnalyzer"

echo "🖥️ Creating Desktop Icon for ADALM-Pluto Spectrum Analyzer"
echo "=================================================="

# Verify files exist
echo "📋 Verifying application files..."

if [[ ! -f "$APP_EXECUTABLE" ]]; then
    echo "❌ Error: Executable not found at $APP_EXECUTABLE"
    exit 1
fi

if [[ ! -f "$APP_ICON" ]]; then
    echo "❌ Error: Icon not found at $APP_ICON"
    exit 1
fi

echo "✅ Executable found: $APP_EXECUTABLE"
echo "✅ Icon found: $APP_ICON"

# Make executable if needed
if [[ ! -x "$APP_EXECUTABLE" ]]; then
    echo "🔧 Making executable..."
    chmod +x "$APP_EXECUTABLE"
fi

# Detect available terminal emulator
echo "🔍 Detecting available terminal emulator..."
TERMINAL_CMD=""
if command -v qterminal &> /dev/null; then
    TERMINAL_CMD="qterminal -e"
    echo "✅ Found qterminal"
elif command -v x-terminal-emulator &> /dev/null; then
    TERMINAL_CMD="x-terminal-emulator -e"
    echo "✅ Found x-terminal-emulator"
elif command -v gnome-terminal &> /dev/null; then
    TERMINAL_CMD="gnome-terminal --"
    echo "✅ Found gnome-terminal"
elif command -v konsole &> /dev/null; then
    TERMINAL_CMD="konsole -e"
    echo "✅ Found konsole"
elif command -v xterm &> /dev/null; then
    TERMINAL_CMD="xterm -e"
    echo "✅ Found xterm"
else
    echo "⚠️  No suitable terminal emulator found, using fallback"
    TERMINAL_CMD="x-terminal-emulator -e"
fi

# Create desktop file
echo "📝 Creating desktop entry file..."

cat > "${DESKTOP_FILE_NAME}.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=${APP_NAME}
Comment=${APP_DESCRIPTION}
Exec=${TERMINAL_CMD} python3 ${APP_EXECUTABLE}
Icon=${APP_ICON}
Terminal=false
Categories=${CATEGORIES}
Keywords=${KEYWORDS}
StartupNotify=true
StartupWMClass=adalm-pluto-spectrum-analyzer
MimeType=application/x-pluto-sdr;
EOF

# Make desktop file executable
chmod +x "${DESKTOP_FILE_NAME}.desktop"

echo "✅ Created: ${DESKTOP_FILE_NAME}.desktop"

# Validate desktop file
echo "🔍 Validating desktop file..."
if command -v desktop-file-validate &> /dev/null; then
    if desktop-file-validate "${DESKTOP_FILE_NAME}.desktop"; then
        echo "✅ Desktop file validation passed"
    else
        echo "⚠️  Desktop file validation warnings (may still work)"
    fi
else
    echo "ℹ️  desktop-file-validate not available, skipping validation"
fi

# Deploy to desktop
echo "🖥️ Deploying to desktop..."
if [[ -d ~/Desktop ]]; then
    cp "${DESKTOP_FILE_NAME}.desktop" ~/Desktop/
    chmod +x ~/Desktop/"${DESKTOP_FILE_NAME}.desktop"
    echo "✅ Deployed to ~/Desktop/"
else
    echo "⚠️  ~/Desktop directory not found, skipping desktop deployment"
fi

# Deploy to applications menu
echo "📱 Deploying to applications menu..."
mkdir -p ~/.local/share/applications
cp "${DESKTOP_FILE_NAME}.desktop" ~/.local/share/applications/
chmod +x ~/.local/share/applications/"${DESKTOP_FILE_NAME}.desktop"
echo "✅ Deployed to ~/.local/share/applications/"

# Update desktop database
echo "🔄 Updating desktop database..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications/
    echo "✅ Desktop database updated"
else
    echo "⚠️  update-desktop-database not available, may need manual refresh"
fi

# System-wide deployment (optional)
echo ""
echo "🌐 System-wide deployment (optional):"
echo "To make this available to all users, run:"
echo "sudo cp '${DESKTOP_FILE_NAME}.desktop' /usr/share/applications/"
echo "sudo update-desktop-database"

echo ""
echo "🎯 Deployment Summary:"
echo "======================"
echo "✅ Desktop file created: ${DESKTOP_FILE_NAME}.desktop"
echo "✅ Desktop deployment: ~/Desktop/${DESKTOP_FILE_NAME}.desktop"
echo "✅ Applications menu: ~/.local/share/applications/${DESKTOP_FILE_NAME}.desktop"
echo ""
echo "🚀 How to use:"
echo "- Double-click desktop icon to launch"
echo "- Search for 'ADALM-Pluto' or 'Spectrum' in applications menu"
echo "- Find in Network/System categories"
echo ""
echo "📋 Application Details:"
echo "- Name: ${APP_NAME}"
echo "- Executable: ${APP_EXECUTABLE}"
echo "- Icon: ${APP_ICON}"
echo "- Terminal: Auto-detected (${TERMINAL_CMD})"
echo ""
echo "✅ Desktop icon creation complete!"
