#!/usr/bin/env python3
"""
Clean Persistent SDR Monitor - True in-place updating
Uses proper terminal control for clean updates
"""

import numpy as np
import time
import os
import sys
from datetime import datetime
import adi

class CleanMonitor:
    def __init__(self):
        """Initialize clean monitor"""
        self.sdr = None
        self.running = False
        self.spectrum_history = []
        self.power_history = []
        self.snr_history = []
        self.max_history = 20
        self.update_interval = 1.0  # 1 second updates
        self.session_start = time.time()
        self.frame_count = 0
        
    def setup_terminal(self):
        """Setup terminal for clean display"""
        # Hide cursor and clear screen
        os.system('clear')
        print('\033[?25l', end='', flush=True)  # Hide cursor
        print('\033[2J\033[H', end='', flush=True)  # Clear screen and home
        
    def cleanup_terminal(self):
        """Restore terminal"""
        print('\033[?25h', end='', flush=True)  # Show cursor
        print('\033[2J\033[H', end='', flush=True)  # Clear screen
        
    def connect_sdr(self):
        """Connect to PlutoSDR"""
        try:
            self.sdr = adi.ad9361(uri='ip:192.168.2.1')
            self.sdr.sample_rate = int(2.4e6)
            self.sdr.rx_lo = int(2.4e9)
            self.sdr.rx_rf_bandwidth = int(2e6)
            self.sdr.rx_buffer_size = 1024
            self.sdr.gain_control_mode_chan0 = 'manual'
            self.sdr.rx_hardwaregain_chan0 = 60
            return True
        except Exception:
            return False
            
    def get_sdr_data(self):
        """Get SDR data or generate synthetic"""
        try:
            if self.sdr:
                samples = self.sdr.rx()
                return samples, self.sdr.sample_rate, self.sdr.rx_lo
            else:
                # Dynamic synthetic data
                N = 1024
                fs = 2.4e6
                t = np.arange(N) / fs
                
                # Time-varying signal
                time_factor = time.time() % 20
                sig1 = 0.6 * np.exp(1j * 2 * np.pi * (1e6 + 0.3e6 * np.sin(time_factor)) * t)
                sig2 = 0.4 * np.exp(1j * 2 * np.pi * (0.5e6 + 0.2e6 * np.cos(time_factor * 1.5)) * t)
                noise_level = 0.05 + 0.03 * np.sin(time_factor * 0.5)
                noise = (np.random.random(N) + 1j * np.random.random(N) - 0.5 - 0.5j) * noise_level
                
                samples = sig1 + sig2 + noise
                return samples, fs, 2.4e9
        except Exception:
            N = 1024
            samples = np.random.random(N) + 1j * np.random.random(N)
            return samples, 2.4e6, 2.4e9
            
    def analyze_spectrum(self, samples, sample_rate, center_freq):
        """Analyze spectrum and extract metrics"""
        # FFT analysis
        fft_data = np.fft.fftshift(np.fft.fft(samples))
        freqs = np.fft.fftshift(np.fft.fftfreq(len(samples), 1/sample_rate))
        power_db = 20 * np.log10(np.abs(fft_data) + 1e-12)
        actual_freqs = (center_freq + freqs) / 1e6
        
        # Calculate metrics
        peak_power = np.max(power_db)
        avg_power = np.mean(power_db)
        noise_floor = np.percentile(power_db, 10)
        snr = peak_power - noise_floor
        peak_freq = actual_freqs[np.argmax(power_db)]
        rms = np.sqrt(np.mean(np.abs(samples)**2))
        
        # Store history
        self.spectrum_history.append(power_db)
        self.power_history.append(peak_power)
        self.snr_history.append(snr)
        
        # Limit history
        for hist in [self.spectrum_history, self.power_history, self.snr_history]:
            if len(hist) > self.max_history:
                hist.pop(0)
                
        return {
            'freqs': actual_freqs,
            'power_db': power_db,
            'peak_power': peak_power,
            'avg_power': avg_power,
            'noise_floor': noise_floor,
            'snr': snr,
            'peak_freq': peak_freq,
            'rms': rms,
            'sample_rate': sample_rate / 1e6,
            'center_freq': center_freq / 1e9,
            'samples': len(samples)
        }
        
    def create_spectrum_bar(self, power_db, width=60):
        """Create simple spectrum bar"""
        if len(power_db) == 0:
            return " " * width
            
        # Downsample for display
        if len(power_db) > width:
            indices = np.linspace(0, len(power_db) - 1, width, dtype=int)
            display_power = power_db[indices]
        else:
            display_power = power_db
            
        # Normalize for display
        min_power = np.min(display_power)
        max_power = np.max(display_power)
        
        if max_power > min_power:
            norm_power = (display_power - min_power) / (max_power - min_power)
        else:
            norm_power = np.zeros_like(display_power)
            
        # Create bar
        bar = ""
        for val in norm_power:
            if val > 0.8:
                bar += "█"
            elif val > 0.6:
                bar += "▓"
            elif val > 0.4:
                bar += "▒"
            elif val > 0.2:
                bar += "░"
            else:
                bar += " "
                
        return bar[:width]
        
    def create_history_bar(self, data, width=30):
        """Create history bar chart"""
        if not data:
            return " " * width
            
        recent_data = data[-width:]
        if len(recent_data) == 0:
            return " " * width
            
        max_val = max(recent_data)
        min_val = min(recent_data)
        
        if max_val == min_val:
            return "█" * len(recent_data) + " " * (width - len(recent_data))
            
        bar = ""
        for val in recent_data:
            normalized = (val - min_val) / (max_val - min_val)
            if normalized > 0.8:
                bar += "█"
            elif normalized > 0.6:
                bar += "▓"
            elif normalized > 0.4:
                bar += "▒"
            elif normalized > 0.2:
                bar += "░"
            else:
                bar += " "
                
        # Pad to width
        bar += " " * (width - len(bar))
        return bar[:width]
        
    def display_frame(self, metrics):
        """Display complete frame cleanly"""
        # Move to home position
        print('\033[H', end='', flush=True)
        
        # Calculate uptime
        uptime = time.time() - self.session_start
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Build display
        lines = []
        lines.append("┌─ SDR Monitor ─────────────────────────────────────────────────────────┐")
        lines.append(f"│ Time: {timestamp} │ Uptime: {hours:02d}:{minutes:02d}:{seconds:02d} │ Frame: {self.frame_count:4d} │ {'Connected' if self.sdr else 'Synthetic':>10} │")
        lines.append("├───────────────────────────────────────────────────────────────────────┤")
        lines.append(f"│ Peak: {metrics['peak_power']:5.1f}dB │ SNR: {metrics['snr']:5.1f}dB │ Freq: {metrics['peak_freq']:7.1f}MHz │ RMS: {metrics['rms']:6.3f} │")
        lines.append("├───────────────────────────────────────────────────────────────────────┤")
        
        # Spectrum display
        spectrum_bar = self.create_spectrum_bar(metrics['power_db'], 65)
        lines.append(f"│ Spectrum: {spectrum_bar} │")
        lines.append("├───────────────────────────────────────────────────────────────────────┤")
        
        # History displays
        power_bar = self.create_history_bar(self.power_history, 30)
        snr_bar = self.create_history_bar(self.snr_history, 30)
        
        lines.append(f"│ Power History:  {power_bar}                     │")
        lines.append(f"│ SNR History:    {snr_bar}                     │")
        lines.append("├───────────────────────────────────────────────────────────────────────┤")
        lines.append("│ Press Ctrl+C to exit │ Updates every 1.0s │ Clean persistent display │")
        lines.append("└───────────────────────────────────────────────────────────────────────┘")
        
        # Print all lines
        for line in lines:
            print(line)
            
        # Add padding to clear any leftover content
        for _ in range(5):
            print(" " * 75)
            
        sys.stdout.flush()
        
    def run(self):
        """Main monitoring loop"""
        try:
            # Setup
            self.setup_terminal()
            
            print("🚀 Starting Clean SDR Monitor...")
            print("📡 Connecting to PlutoSDR...")
            time.sleep(1)
            
            connected = self.connect_sdr()
            if not connected:
                print("⚠️ Using synthetic data for demonstration")
                time.sleep(1)
                
            self.running = True
            
            while self.running:
                # Get data and analyze
                samples, sample_rate, center_freq = self.get_sdr_data()
                metrics = self.analyze_spectrum(samples, sample_rate, center_freq)
                
                # Display frame
                self.display_frame(metrics)
                
                self.frame_count += 1
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup_terminal()
            print("📡 Clean SDR Monitor stopped")
            print("👋 Thanks for using SDR Monitor!")

def main():
    """Main function"""
    monitor = CleanMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
