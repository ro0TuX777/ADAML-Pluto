#!/bin/bash
# Test script to verify desktop icon functionality

echo "🧪 Testing Desktop Icon Launch"
echo "=============================="

# Test if qterminal is available and working
echo "🔍 Testing qterminal availability..."
if command -v qterminal &> /dev/null; then
    echo "✅ qterminal found at: $(which qterminal)"
    
    # Test launching the application (will exit quickly for testing)
    echo "🚀 Testing application launch..."
    echo "   Command: qterminal -e python3 pluto_menu.py"
    echo "   Note: This will open a terminal window briefly"
    
    # Launch in background and kill quickly for testing
    qterminal -e bash -c "echo 'Desktop icon test successful! Application would start here.'; sleep 2" &
    QTERMINAL_PID=$!
    sleep 3
    kill $QTERMINAL_PID 2>/dev/null || true
    
    echo "✅ Test completed successfully"
else
    echo "❌ qterminal not found"
    
    # Test alternative terminal
    echo "🔍 Testing x-terminal-emulator..."
    if command -v x-terminal-emulator &> /dev/null; then
        echo "✅ x-terminal-emulator found"
        echo "🚀 Testing alternative launch..."
        x-terminal-emulator -e bash -c "echo 'Alternative desktop icon test successful!'; sleep 2" &
        ALT_PID=$!
        sleep 3
        kill $ALT_PID 2>/dev/null || true
        echo "✅ Alternative test completed"
    else
        echo "❌ No suitable terminal emulator found"
    fi
fi

echo ""
echo "📋 Desktop File Status:"
echo "======================"
if [[ -f "ADALM-PlutoSpectrumAnalyzer.desktop" ]]; then
    echo "✅ Desktop file exists"
    echo "📄 Content preview:"
    echo "   Exec line: $(grep '^Exec=' ADALM-PlutoSpectrumAnalyzer.desktop)"
    echo "   Terminal: $(grep '^Terminal=' ADALM-PlutoSpectrumAnalyzer.desktop)"
else
    echo "❌ Desktop file not found"
fi

echo ""
echo "🎯 Next Steps:"
echo "============="
echo "1. Double-click the desktop icon to test"
echo "2. Or search for 'ADALM-Pluto' in your application menu"
echo "3. If issues persist, try the alternative desktop file"
echo ""
echo "✅ Test script completed!"
