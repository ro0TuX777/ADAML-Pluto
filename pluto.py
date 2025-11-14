#!/usr/bin/env python3
"""
Enhanced ADALM-Pluto SDR Toolkit Launcher

Simple launcher script that provides easy access to all tools and features
in the enhanced ADALM-Pluto spectrum analyzer toolkit.

Usage:
    python pluto.py                    # Launch terminal menu
    python pluto.py menu               # Launch terminal menu
    python pluto.py gui                # Launch GUI spectrum analyzer
    python pluto.py waterfall          # Launch standalone waterfall
    python pluto.py demo               # Run feature demonstration
    python pluto.py test               # Run integration tests
    python pluto.py --help             # Show this help

Author: Enhanced SDR Tools
License: GPL-2 (compatible with all integrated projects)
"""

import sys
import os
import subprocess
import argparse


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Enhanced ADALM-Pluto SDR Toolkit                         ║
║                                                                              ║
║  🚀 Comprehensive SDR toolkit integrating features from:                    ║
║     📡 ADALM-Pluto-Spectrum-Analyzer (original)                            ║
║     🔧 plutosdr_scripts (Analog Devices)                                   ║
║     💾 plutosdr-fw (Analog Devices)                                        ║
║     🌊 waterfall display (inspired by Stvff/waterfall)                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def launch_menu():
    """Launch the terminal menu system"""
    print("🖥️  Launching terminal menu system...")
    try:
        subprocess.run([sys.executable, "pluto_menu.py"])
    except KeyboardInterrupt:
        print("\nMenu system interrupted by user.")
    except Exception as e:
        print(f"Error launching menu: {e}")


def launch_gui():
    """Launch the GUI spectrum analyzer"""
    print("🖥️  Launching GUI spectrum analyzer...")
    try:
        subprocess.Popen([sys.executable, "enhanced_spectrum_analyzer.py"])
        print("✅ GUI application launched")
    except Exception as e:
        print(f"Error launching GUI: {e}")


def launch_waterfall():
    """Launch the standalone waterfall display"""
    print("🌊 Launching standalone waterfall display...")
    try:
        subprocess.Popen([sys.executable, "waterfall_app.py"])
        print("✅ Waterfall application launched")
    except Exception as e:
        print(f"Error launching waterfall: {e}")


def run_demo():
    """Run the feature demonstration"""
    print("🎭 Running feature demonstration...")
    try:
        subprocess.run([sys.executable, "demo_all_features.py"])
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Error running demo: {e}")


def run_tests():
    """Run integration tests"""
    print("🧪 Running integration tests...")
    try:
        subprocess.run([sys.executable, "test_integration.py", "--verbose"])
    except KeyboardInterrupt:
        print("\nTests interrupted by user.")
    except Exception as e:
        print(f"Error running tests: {e}")


def show_status():
    """Show system status and available tools"""
    print("📊 System Status:")
    print("=" * 40)
    
    # Check Python modules
    modules = {
        "numpy": "NumPy (numerical computing)",
        "scipy": "SciPy (scientific computing)",
        "pyqtgraph": "PyQtGraph (plotting)",
        "PyQt6": "PyQt6 (GUI framework)"
    }
    
    for module, description in modules.items():
        try:
            __import__(module)
            print(f"  ✅ {description}")
        except ImportError:
            print(f"  ❌ {description} - Not available")
    
    # Check our utilities
    try:
        from pluto_utils import PlutoSDRManager
        print(f"  ✅ Enhanced PlutoSDR utilities")
    except ImportError:
        print(f"  ❌ Enhanced PlutoSDR utilities - Not available")
    
    # Check system tools
    system_tools = {
        "iio_info": "libiio tools",
        "avahi-resolve": "Avahi/Zeroconf tools"
    }
    
    for tool, description in system_tools.items():
        try:
            result = subprocess.run([tool, "--help"], 
                                  capture_output=True, timeout=2)
            print(f"  ✅ {description}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"  ⚠️  {description} - Optional")
    
    print("\n📁 Available Applications:")
    print("=" * 40)
    
    apps = [
        ("pluto_menu.py", "Terminal menu system"),
        ("enhanced_spectrum_analyzer.py", "GUI spectrum analyzer"),
        ("waterfall_app.py", "Standalone waterfall display"),
        ("demo_all_features.py", "Feature demonstration"),
        ("test_integration.py", "Integration tests")
    ]
    
    for app, description in apps:
        if os.path.exists(app):
            print(f"  ✅ {app} - {description}")
        else:
            print(f"  ❌ {app} - Not found")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced ADALM-Pluto SDR Toolkit Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Commands:
  menu          Launch terminal menu system (default)
  gui           Launch GUI spectrum analyzer
  waterfall     Launch standalone waterfall display
  demo          Run feature demonstration
  test          Run integration tests
  status        Show system status and available tools

Examples:
  python pluto.py              # Launch terminal menu
  python pluto.py gui          # Launch GUI
  python pluto.py waterfall    # Launch waterfall
  python pluto.py demo         # Run demo
  python pluto.py test         # Run tests
  python pluto.py status       # Show status

The terminal menu provides access to all features and is recommended
for first-time users or when working on headless systems.
        """
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        default="menu",
        choices=["menu", "gui", "waterfall", "demo", "test", "status"],
        help="Command to execute (default: menu)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Enhanced ADALM-Pluto SDR Toolkit v2.0"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Execute command
    if args.command == "menu":
        launch_menu()
    elif args.command == "gui":
        launch_gui()
    elif args.command == "waterfall":
        launch_waterfall()
    elif args.command == "demo":
        run_demo()
    elif args.command == "test":
        run_tests()
    elif args.command == "status":
        show_status()
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main()
