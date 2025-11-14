#!/usr/bin/env python3
"""
Command-line Log Browser for ADALM-Pluto SDR
Browse and analyze signal logs from the terminal
"""

import os
import json
import csv
from pathlib import Path
from datetime import datetime
import numpy as np

class LogBrowser:
    def __init__(self, logs_dir="logs"):
        """Initialize log browser"""
        self.logs_dir = Path(logs_dir)
        self.log_files = []
        self.scan_logs()
        
    def scan_logs(self):
        """Scan for available log files"""
        self.log_files = []
        
        if not self.logs_dir.exists():
            print(f"❌ Logs directory not found: {self.logs_dir}")
            return
            
        for subdir in self.logs_dir.iterdir():
            if subdir.is_dir():
                for log_file in subdir.glob('*'):
                    if log_file.is_file():
                        self.log_files.append({
                            'path': log_file,
                            'relative_path': log_file.relative_to(self.logs_dir),
                            'type': self.get_log_type(log_file),
                            'size': log_file.stat().st_size,
                            'modified': log_file.stat().st_mtime
                        })
        
        # Sort by modification time (newest first)
        self.log_files.sort(key=lambda x: x['modified'], reverse=True)
        
    def get_log_type(self, file_path):
        """Determine log type from file path"""
        path_str = str(file_path)
        if 'spectrum_data' in path_str:
            return 'SPECTRUM'
        elif 'signal_captures' in path_str:
            return 'SIGNAL'
        elif 'waterfall_data' in path_str:
            return 'WATERFALL'
        elif 'device_monitoring' in path_str:
            return 'DEVICE'
        elif 'session_logs' in path_str:
            return 'SESSION'
        else:
            return 'OTHER'
            
    def format_size(self, size_bytes):
        """Format file size for display"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
            
    def format_time(self, timestamp):
        """Format timestamp for display"""
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
    def show_log_list(self):
        """Display list of available logs"""
        print("\n📁 AVAILABLE SIGNAL LOGS")
        print("=" * 80)
        
        if not self.log_files:
            print("❌ No log files found. Run some signal captures first!")
            return
            
        print(f"{'#':<3} {'TYPE':<10} {'SIZE':<10} {'MODIFIED':<20} {'FILE'}")
        print("-" * 80)
        
        for i, log in enumerate(self.log_files, 1):
            print(f"{i:<3} {log['type']:<10} {self.format_size(log['size']):<10} "
                  f"{self.format_time(log['modified']):<20} {log['relative_path']}")
                  
    def view_log_summary(self, log_index):
        """Show summary of a specific log file"""
        if log_index < 1 or log_index > len(self.log_files):
            print("❌ Invalid log number")
            return
            
        log = self.log_files[log_index - 1]
        
        print(f"\n📄 LOG SUMMARY: {log['relative_path']}")
        print("=" * 60)
        print(f"Type: {log['type']}")
        print(f"Size: {self.format_size(log['size'])}")
        print(f"Modified: {self.format_time(log['modified'])}")
        print(f"Path: {log['path']}")
        
        # Show content summary based on type
        try:
            if log['type'] == 'SPECTRUM':
                self.summarize_spectrum_log(log['path'])
            elif log['type'] == 'SIGNAL':
                self.summarize_signal_log(log['path'])
            elif log['type'] == 'WATERFALL':
                self.summarize_waterfall_log(log['path'])
            elif log['type'] == 'DEVICE':
                self.summarize_device_log(log['path'])
            elif log['type'] == 'SESSION':
                self.summarize_session_log(log['path'])
        except Exception as e:
            print(f"❌ Error reading log: {e}")
            
    def summarize_spectrum_log(self, file_path):
        """Summarize spectrum data log"""
        frequencies = []
        amplitudes = []
        metadata = {}
        
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].startswith('#'):
                    if ':' in row[0]:
                        key = row[0][1:].strip()
                        value = row[1] if len(row) > 1 else ''
                        metadata[key] = value
                elif row and not row[0].startswith('#') and row[0] != 'Frequency_Hz':
                    try:
                        freq = float(row[0])
                        amp = float(row[1])
                        frequencies.append(freq)
                        amplitudes.append(amp)
                    except (ValueError, IndexError):
                        continue
                        
        print(f"\n📊 SPECTRUM DATA:")
        print(f"   Data points: {len(frequencies):,}")
        if frequencies:
            print(f"   Frequency range: {min(frequencies)/1e6:.1f} - {max(frequencies)/1e6:.1f} MHz")
            print(f"   Amplitude range: {min(amplitudes):.1f} - {max(amplitudes):.1f} dB")
            print(f"   Peak amplitude: {max(amplitudes):.1f} dB at {frequencies[amplitudes.index(max(amplitudes))]/1e6:.1f} MHz")
            
        if metadata:
            print(f"\n📋 METADATA:")
            for key, value in metadata.items():
                print(f"   {key}: {value}")
                
    def summarize_signal_log(self, file_path):
        """Summarize signal capture log"""
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        print(f"\n📡 SIGNAL CAPTURE:")
        
        if 'capture_info' in data:
            info = data['capture_info']
            print(f"   Sample rate: {info.get('sample_rate', 'Unknown')/1e6:.1f} MHz")
            print(f"   Center frequency: {info.get('center_frequency', 'Unknown')/1e9:.3f} GHz")
            print(f"   Sample count: {info.get('sample_count', 'Unknown'):,}")
            print(f"   Duration: {info.get('duration_seconds', 'Unknown'):.4f} seconds")
            
            if 'metadata' in info:
                print(f"\n📋 METADATA:")
                for key, value in info['metadata'].items():
                    print(f"   {key}: {value}")
                    
        if 'signal_data' in data:
            real_data = data['signal_data']['real']
            imag_data = data['signal_data']['imag']
            print(f"\n📊 SIGNAL STATISTICS:")
            print(f"   Real range: {min(real_data):.3f} - {max(real_data):.3f}")
            print(f"   Imag range: {min(imag_data):.3f} - {max(imag_data):.3f}")
            print(f"   Samples shown: {len(real_data)} (of {data['capture_info'].get('sample_count', 'unknown')})")
            
    def summarize_waterfall_log(self, file_path):
        """Summarize waterfall data log"""
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        print(f"\n🌊 WATERFALL DATA:")
        
        if 'capture_info' in data:
            info = data['capture_info']
            print(f"   Frequency points: {info.get('frequency_points', 'Unknown'):,}")
            print(f"   Time points: {info.get('time_points', 'Unknown'):,}")
            
            freq_range = info.get('frequency_range', [])
            if freq_range:
                print(f"   Frequency range: {freq_range[0]/1e6:.1f} - {freq_range[1]/1e6:.1f} MHz")
                
            print(f"   Time span: {info.get('time_span', 'Unknown')} seconds")
            
            if 'metadata' in info:
                print(f"\n📋 METADATA:")
                for key, value in info['metadata'].items():
                    print(f"   {key}: {value}")
                    
        if 'data' in data and 'power_matrix' in data['data']:
            power_matrix = np.array(data['data']['power_matrix'])
            print(f"\n📊 POWER STATISTICS:")
            print(f"   Matrix shape: {power_matrix.shape}")
            print(f"   Power range: {np.min(power_matrix):.1f} - {np.max(power_matrix):.1f} dB")
            print(f"   Average power: {np.mean(power_matrix):.1f} dB")
            
    def summarize_device_log(self, file_path):
        """Summarize device status log"""
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        print(f"\n🔧 DEVICE STATUS:")
        print(f"   Timestamp: {data.get('timestamp', 'Unknown')}")
        print(f"   Session ID: {data.get('session_id', 'Unknown')}")
        print(f"   System health: {data.get('system_health', 'Unknown')}")
        
        if 'device_info' in data:
            info = data['device_info']
            print(f"\n📡 DEVICE CONFIGURATION:")
            for key, value in info.items():
                print(f"   {key}: {value}")
                
        if 'temperatures' in data and data['temperatures']:
            print(f"\n🌡️ TEMPERATURES:")
            for sensor, temp in data['temperatures'].items():
                print(f"   {sensor}: {temp}°C")
        else:
            print(f"\n🌡️ TEMPERATURES: Not available")
            
    def summarize_session_log(self, file_path):
        """Summarize session log"""
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        print(f"\n📝 SESSION LOG:")
        print(f"   Total lines: {len(lines)}")
        
        # Extract session info
        session_info = {}
        events = []
        
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('['):
                key, value = line.split(':', 1)
                session_info[key.strip()] = value.strip()
            elif line.startswith('['):
                events.append(line)
                
        print(f"\n📋 SESSION INFO:")
        for key, value in session_info.items():
            print(f"   {key}: {value}")
            
        print(f"\n📊 EVENTS:")
        print(f"   Total events: {len(events)}")
        if events:
            print(f"   First event: {events[0]}")
            print(f"   Last event: {events[-1]}")
            
    def view_log_content(self, log_index, lines=20):
        """Show content of a specific log file"""
        if log_index < 1 or log_index > len(self.log_files):
            print("❌ Invalid log number")
            return
            
        log = self.log_files[log_index - 1]
        
        print(f"\n📄 LOG CONTENT: {log['relative_path']} (first {lines} lines)")
        print("=" * 80)
        
        try:
            with open(log['path'], 'r') as f:
                for i, line in enumerate(f, 1):
                    if i > lines:
                        print(f"... (showing first {lines} lines of {log['type']} log)")
                        break
                    print(f"{i:3}: {line.rstrip()}")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            
    def interactive_browser(self):
        """Interactive log browser"""
        while True:
            print("\n📊 ADALM-PLUTO SIGNAL LOG BROWSER")
            print("=" * 50)
            print("1. 📁 List all logs")
            print("2. 📄 View log summary")
            print("3. 👁️ View log content")
            print("4. 🔄 Refresh log list")
            print("5. 🚪 Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == '1':
                self.show_log_list()
            elif choice == '2':
                self.show_log_list()
                try:
                    log_num = int(input("\nEnter log number for summary: "))
                    self.view_log_summary(log_num)
                except ValueError:
                    print("❌ Invalid number")
            elif choice == '3':
                self.show_log_list()
                try:
                    log_num = int(input("\nEnter log number to view: "))
                    lines = input("Number of lines to show (default 20): ").strip()
                    lines = int(lines) if lines else 20
                    self.view_log_content(log_num, lines)
                except ValueError:
                    print("❌ Invalid number")
            elif choice == '4':
                print("🔄 Refreshing log list...")
                self.scan_logs()
                print(f"✅ Found {len(self.log_files)} log files")
            elif choice == '5':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")

def main():
    """Main function"""
    browser = LogBrowser()
    browser.interactive_browser()

if __name__ == "__main__":
    main()
