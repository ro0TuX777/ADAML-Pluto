#!/usr/bin/env python3
"""
SDR Monitor - nvtop-style dynamic visualization for ADALM-Pluto SDR
Real-time monitoring with continuous updates and multiple panels
"""

import numpy as np
import time
import os
import sys
import threading
from datetime import datetime
import adi
import json

class SDRMonitor:
    def __init__(self):
        """Initialize SDR monitor"""
        self.sdr = None
        self.running = False
        self.width = 120  # Wider display like nvtop
        self.spectrum_history = []
        self.power_history = []
        self.snr_history = []
        self.temp_history = []
        self.max_history = 100
        self.update_interval = 0.1  # 10 FPS like nvtop
        self.session_start = time.time()
        
    def clear_screen(self):
        """Clear screen and move cursor to top"""
        print('\033[2J\033[H', end='', flush=True)
        
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
                
                # Time-varying signal with multiple components
                time_factor = time.time() % 20
                
                # Multiple signal components
                sig1 = 0.6 * np.exp(1j * 2 * np.pi * (1e6 + 0.3e6 * np.sin(time_factor)) * t)
                sig2 = 0.4 * np.exp(1j * 2 * np.pi * (0.5e6 + 0.2e6 * np.cos(time_factor * 1.5)) * t)
                sig3 = 0.3 * np.exp(1j * 2 * np.pi * (-0.8e6 + 0.1e6 * np.sin(time_factor * 2)) * t)
                
                # Dynamic noise level
                noise_level = 0.05 + 0.03 * np.sin(time_factor * 0.5)
                noise = (np.random.random(N) + 1j * np.random.random(N) - 0.5 - 0.5j) * noise_level
                
                samples = sig1 + sig2 + sig3 + noise
                return samples, fs, 2.4e9
        except Exception:
            # Fallback
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
        
        # Signal quality metrics
        rms = np.sqrt(np.mean(np.abs(samples)**2))
        peak_to_avg = peak_power - avg_power
        
        # Store history
        self.spectrum_history.append(power_db)
        self.power_history.append(peak_power)
        self.snr_history.append(snr)
        
        # Simulate temperature (would be real from device)
        temp = 45 + 10 * np.sin(time.time() * 0.1) + np.random.normal(0, 1)
        self.temp_history.append(temp)
        
        # Limit history
        for hist in [self.spectrum_history, self.power_history, self.snr_history, self.temp_history]:
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
            'peak_to_avg': peak_to_avg,
            'temperature': temp,
            'sample_rate': sample_rate / 1e6,
            'center_freq': center_freq / 1e9,
            'samples': len(samples)
        }
        
    def create_bar_chart(self, values, width=40, height=8, title="", unit=""):
        """Create horizontal bar chart like nvtop"""
        if not values:
            return [f"{title}: No data"]
            
        lines = []
        lines.append(f"┌─ {title} " + "─" * (width - len(title) - 4) + "┐")
        
        # Get recent values
        recent_vals = values[-height:] if len(values) >= height else values
        max_val = max(recent_vals) if recent_vals else 1
        min_val = min(recent_vals) if recent_vals else 0
        
        for i, val in enumerate(reversed(recent_vals)):
            # Normalize to bar width
            if max_val > min_val:
                bar_len = int((val - min_val) / (max_val - min_val) * (width - 15))
            else:
                bar_len = 0
                
            bar = "█" * bar_len + "░" * (width - 15 - bar_len)
            lines.append(f"│{val:6.1f}{unit} │{bar}│")
            
        lines.append(f"└{'─' * (width - 2)}┘")
        return lines
        
    def create_spectrum_display(self, freqs, power_db, width=80, height=12):
        """Create spectrum display like nvtop GPU usage"""
        lines = []
        lines.append(f"┌─ Real-Time Spectrum " + "─" * (width - 20) + "┐")
        
        # Downsample for display
        if len(power_db) > width - 2:
            indices = np.linspace(0, len(power_db) - 1, width - 2, dtype=int)
            display_power = power_db[indices]
            display_freqs = freqs[indices]
        else:
            display_power = power_db
            display_freqs = freqs
            
        # Normalize for display
        min_power = np.min(display_power)
        max_power = np.max(display_power)
        
        if max_power > min_power:
            norm_power = (display_power - min_power) / (max_power - min_power) * (height - 1)
        else:
            norm_power = np.zeros_like(display_power)
            
        # Create spectrum plot
        for row in range(height - 1, -1, -1):
            line = "│"
            for col, val in enumerate(norm_power):
                if int(val) == row:
                    line += "█"
                elif int(val) > row:
                    line += "│"
                else:
                    line += " "
            line += "│"
            lines.append(line)
            
        # Add frequency labels
        freq_line = f"│{display_freqs[0]:6.1f}MHz" + " " * (width - 20) + f"{display_freqs[-1]:6.1f}MHz│"
        lines.append(freq_line)
        lines.append(f"└{'─' * (width - 2)}┘")
        
        return lines
        
    def create_waterfall_display(self, width=60, height=10):
        """Create waterfall display"""
        lines = []
        lines.append(f"┌─ Waterfall " + "─" * (width - 12) + "┐")
        
        if len(self.spectrum_history) < 2:
            for _ in range(height):
                lines.append("│" + " " * (width - 2) + "│")
        else:
            # Show recent spectrum history
            recent_spectra = self.spectrum_history[-height:]
            
            for spectrum in reversed(recent_spectra):
                line = "│"
                # Downsample spectrum
                if len(spectrum) > width - 2:
                    indices = np.linspace(0, len(spectrum) - 1, width - 2, dtype=int)
                    display_spectrum = spectrum[indices]
                else:
                    display_spectrum = spectrum
                    
                # Normalize and convert to characters
                if len(display_spectrum) > 0:
                    norm_spec = (display_spectrum - np.min(display_spectrum)) / (np.max(display_spectrum) - np.min(display_spectrum) + 1e-12)
                    for val in norm_spec:
                        if val > 0.8:
                            line += "█"
                        elif val > 0.6:
                            line += "▓"
                        elif val > 0.4:
                            line += "▒"
                        elif val > 0.2:
                            line += "░"
                        else:
                            line += " "
                else:
                    line += " " * (width - 2)
                    
                line += "│"
                lines.append(line)
                
        lines.append(f"└{'─' * (width - 2)}┘")
        return lines
        
    def create_info_panel(self, metrics):
        """Create info panel like nvtop"""
        uptime = time.time() - self.session_start
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        
        lines = []
        lines.append("┌─ SDR Information ─────────────────────────┐")
        lines.append(f"│ Device: ADALM-Pluto SDR                   │")
        lines.append(f"│ Status: {'Connected' if self.sdr else 'Synthetic'}                    │")
        lines.append(f"│ Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}                        │")
        lines.append(f"│ Center: {metrics['center_freq']:.3f} GHz                │")
        lines.append(f"│ Sample Rate: {metrics['sample_rate']:.1f} MHz            │")
        lines.append(f"│ Samples: {metrics['samples']:,}                     │")
        lines.append(f"│ Temperature: {metrics['temperature']:.1f}°C               │")
        lines.append("└───────────────────────────────────────────┘")
        
        return lines
        
    def create_metrics_panel(self, metrics):
        """Create metrics panel"""
        lines = []
        lines.append("┌─ Signal Metrics ──────────────────────────┐")
        lines.append(f"│ Peak Power: {metrics['peak_power']:6.1f} dB              │")
        lines.append(f"│ Avg Power:  {metrics['avg_power']:6.1f} dB              │")
        lines.append(f"│ Noise Floor:{metrics['noise_floor']:6.1f} dB              │")
        lines.append(f"│ SNR:        {metrics['snr']:6.1f} dB              │")
        lines.append(f"│ Peak Freq:  {metrics['peak_freq']:6.1f} MHz            │")
        lines.append(f"│ RMS Level:  {metrics['rms']:6.3f}                │")
        lines.append(f"│ Peak/Avg:   {metrics['peak_to_avg']:6.1f} dB              │")
        lines.append("└───────────────────────────────────────────┘")
        
        return lines
        
    def display_frame(self, metrics):
        """Display complete frame like nvtop"""
        self.clear_screen()
        
        # Header
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"📡 SDR Monitor v1.0 - ADALM-Pluto Real-Time Analysis │ {timestamp}")
        print("═" * 120)
        
        # Top row: Spectrum and Info
        spectrum_lines = self.create_spectrum_display(metrics['freqs'], metrics['power_db'], 80, 12)
        info_lines = self.create_info_panel(metrics)
        
        max_lines = max(len(spectrum_lines), len(info_lines))
        for i in range(max_lines):
            left = spectrum_lines[i] if i < len(spectrum_lines) else " " * 80
            right = info_lines[i] if i < len(info_lines) else " " * 43
            print(f"{left} {right}")
            
        print()
        
        # Middle row: Waterfall and Metrics
        waterfall_lines = self.create_waterfall_display(60, 10)
        metrics_lines = self.create_metrics_panel(metrics)
        
        max_lines = max(len(waterfall_lines), len(metrics_lines))
        for i in range(max_lines):
            left = waterfall_lines[i] if i < len(waterfall_lines) else " " * 60
            right = metrics_lines[i] if i < len(metrics_lines) else " " * 43
            print(f"{left} {right}")
            
        print()
        
        # Bottom row: History charts
        power_chart = self.create_bar_chart(self.power_history[-20:], 40, 6, "Power History", "dB")
        snr_chart = self.create_bar_chart(self.snr_history[-20:], 40, 6, "SNR History", "dB")
        temp_chart = self.create_bar_chart(self.temp_history[-20:], 40, 6, "Temperature", "°C")
        
        # Display charts side by side
        max_chart_lines = max(len(power_chart), len(snr_chart), len(temp_chart))
        for i in range(max_chart_lines):
            left = power_chart[i] if i < len(power_chart) else " " * 42
            middle = snr_chart[i] if i < len(snr_chart) else " " * 42
            right = temp_chart[i] if i < len(temp_chart) else " " * 42
            print(f"{left} {middle} {right}")
            
        # Footer
        print("\n" + "─" * 120)
        print("Press Ctrl+C to exit │ Update rate: 10 FPS │ Like nvtop but for SDR!")
        
    def run(self):
        """Main monitoring loop"""
        print("🚀 Starting SDR Monitor (nvtop-style)...")
        print("📡 Connecting to PlutoSDR...")
        
        connected = self.connect_sdr()
        if not connected:
            print("⚠️ Using synthetic data for demonstration")
            
        print("🔄 Starting real-time monitoring...")
        time.sleep(2)
        
        self.running = True
        
        try:
            while self.running:
                # Get data and analyze
                samples, sample_rate, center_freq = self.get_sdr_data()
                metrics = self.analyze_spectrum(samples, sample_rate, center_freq)
                
                # Display frame
                self.display_frame(metrics)
                
                # Wait for next update
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            self.clear_screen()
            print("\n📡 SDR Monitor stopped")
            print("👋 Thanks for using SDR Monitor!")
            self.running = False

def main():
    """Main function"""
    monitor = SDRMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
