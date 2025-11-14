#!/usr/bin/env python3
"""
Dynamic Real-Time Signal Visualizer for ADALM-Pluto SDR
Continuously updating terminal-based visualization
"""

import numpy as np
import time
import os
import sys
from datetime import datetime
import adi

class DynamicVisualizer:
    def __init__(self):
        """Initialize dynamic visualizer"""
        self.sdr = None
        self.running = False
        self.width = 80
        self.height = 15
        self.update_rate = 0.5  # Updates per second
        self.data_history = []
        self.max_history = 50
        
    def clear_screen(self):
        """Clear terminal screen"""
        print('\033[2J\033[H', end='')  # ANSI escape codes
        
    def connect_pluto(self):
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
        except Exception as e:
            return False
            
    def capture_data(self):
        """Capture data from PlutoSDR or generate synthetic"""
        try:
            if self.sdr:
                samples = self.sdr.rx()
                return samples, self.sdr.sample_rate, self.sdr.rx_lo
            else:
                # Dynamic synthetic data with time-varying components
                N = 1024
                fs = 2.4e6
                t = np.arange(N) / fs
                
                # Time-varying frequency and amplitude
                time_factor = time.time() % 10  # 10-second cycle
                fc = 1e6 + 0.5e6 * np.sin(time_factor)  # Varying center frequency
                amplitude = 0.5 + 0.3 * np.cos(time_factor * 2)  # Varying amplitude
                
                # Create dynamic signal
                signal = np.exp(1j * 2 * np.pi * fc * t) * amplitude
                noise = (np.random.random(N) + 1j * np.random.random(N) - 0.5 - 0.5j) * 0.1
                samples = signal + noise
                
                return samples, fs, 2.4e9
        except Exception as e:
            # Fallback
            N = 1024
            samples = np.random.random(N) + 1j * np.random.random(N)
            return samples, 2.4e6, 2.4e9
            
    def create_dynamic_plot(self, data, title, min_val=None, max_val=None):
        """Create dynamic ASCII plot with auto-scaling"""
        if len(data) == 0:
            return [f"{title}: No data"]
            
        # Auto-scale if not provided
        if min_val is None:
            min_val = np.min(data)
        if max_val is None:
            max_val = np.max(data)
            
        if max_val == min_val:
            normalized = np.zeros_like(data)
        else:
            normalized = (data - min_val) / (max_val - min_val) * (self.height - 1)
            
        # Downsample to fit width
        if len(data) > self.width:
            indices = np.linspace(0, len(data) - 1, self.width, dtype=int)
            normalized = normalized[indices]
            
        # Create plot
        lines = []
        lines.append(f"{title} │ Range: {min_val:.1f} to {max_val:.1f}")
        lines.append("┌" + "─" * self.width + "┐")
        
        for row in range(self.height - 1, -1, -1):
            line = "│"
            for col in range(len(normalized)):
                val = int(normalized[col])
                if val == row:
                    line += "●"
                elif val > row:
                    line += "│"
                else:
                    line += " "
            line += "│"
            lines.append(line)
            
        lines.append("└" + "─" * self.width + "┘")
        return lines
        
    def create_waterfall_display(self):
        """Create dynamic waterfall display from history"""
        if len(self.data_history) < 2:
            return ["🌊 Waterfall: Collecting data..."]
            
        lines = []
        lines.append("🌊 WATERFALL (Time vs Frequency)")
        lines.append("┌" + "─" * self.width + "┐")
        
        # Show last 10 time slices
        display_history = self.data_history[-10:]
        
        for i, spectrum in enumerate(reversed(display_history)):
            line = "│"
            # Normalize spectrum for display
            if len(spectrum) > 0:
                norm_spectrum = (spectrum - np.min(spectrum)) / (np.max(spectrum) - np.min(spectrum) + 1e-12)
                # Downsample to fit width
                if len(norm_spectrum) > self.width:
                    indices = np.linspace(0, len(norm_spectrum) - 1, self.width, dtype=int)
                    norm_spectrum = norm_spectrum[indices]
                
                for val in norm_spectrum:
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
                line += " " * self.width
            line += "│"
            lines.append(line)
            
        lines.append("└" + "─" * self.width + "┘")
        return lines
        
    def analyze_signal(self, samples, sample_rate, center_freq):
        """Analyze signal and return metrics"""
        # Spectrum analysis
        fft_data = np.fft.fftshift(np.fft.fft(samples))
        freqs = np.fft.fftshift(np.fft.fftfreq(len(samples), 1/sample_rate))
        power_db = 20 * np.log10(np.abs(fft_data) + 1e-12)
        actual_freqs = (center_freq + freqs) / 1e6
        
        # Store for waterfall
        self.data_history.append(power_db)
        if len(self.data_history) > self.max_history:
            self.data_history.pop(0)
            
        # Signal metrics
        metrics = {
            'peak_freq': actual_freqs[np.argmax(power_db)],
            'peak_power': np.max(power_db),
            'avg_power': np.mean(power_db),
            'snr': np.max(power_db) - np.mean(power_db),
            'rms': np.sqrt(np.mean(np.abs(samples)**2)),
            'sample_count': len(samples),
            'bandwidth': sample_rate / 1e6,
            'center_freq': center_freq / 1e9
        }
        
        return actual_freqs, power_db, metrics
        
    def display_metrics(self, metrics, update_count):
        """Display real-time metrics"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"📡 ADALM-PLUTO DYNAMIC SIGNAL ANALYZER │ {timestamp} │ Update #{update_count}")
        print("═" * 80)
        print(f"📊 Peak: {metrics['peak_power']:.1f}dB @ {metrics['peak_freq']:.1f}MHz │ "
              f"SNR: {metrics['snr']:.1f}dB │ RMS: {metrics['rms']:.3f}")
        print(f"📻 Center: {metrics['center_freq']:.3f}GHz │ "
              f"BW: {metrics['bandwidth']:.1f}MHz │ Samples: {metrics['sample_count']:,}")
        print()
        
    def real_time_loop(self):
        """Main real-time visualization loop"""
        print("🚀 Starting Dynamic Real-Time Visualization...")
        print("📊 Connecting to PlutoSDR...")
        
        connected = self.connect_pluto()
        if not connected:
            print("⚠️ Using synthetic data for demonstration")
            
        print("🔄 Press Ctrl+C to stop")
        time.sleep(2)
        
        self.running = True
        update_count = 0
        
        try:
            while self.running:
                # Capture and analyze
                samples, sample_rate, center_freq = self.capture_data()
                freqs, power_db, metrics = self.analyze_signal(samples, sample_rate, center_freq)
                
                # Clear and display
                self.clear_screen()
                
                # Header with metrics
                self.display_metrics(metrics, update_count + 1)
                
                # Spectrum plot
                spectrum_lines = self.create_dynamic_plot(
                    power_db, "📈 SPECTRUM", 
                    min_val=metrics['avg_power'] - 20,
                    max_val=metrics['peak_power'] + 5
                )
                for line in spectrum_lines:
                    print(line)
                    
                print()
                
                # Waterfall display
                waterfall_lines = self.create_waterfall_display()
                for line in waterfall_lines[:12]:  # Limit height
                    print(line)
                    
                print()
                
                # Time domain (simplified)
                real_part = np.real(samples[:100])  # First 100 samples
                time_lines = self.create_dynamic_plot(real_part, "📊 TIME DOMAIN (Real)")
                for line in time_lines[:8]:  # Compact display
                    print(line)
                    
                print(f"\n🛑 Press Ctrl+C to stop │ Update rate: {1/self.update_rate:.1f}s")
                
                update_count += 1
                time.sleep(self.update_rate)
                
        except KeyboardInterrupt:
            print("\n\n👋 Dynamic visualization stopped")
            self.running = False
            
    def single_analysis(self):
        """Single capture analysis"""
        print("📊 Single Dynamic Analysis")
        print("=" * 50)
        
        connected = self.connect_pluto()
        if not connected:
            print("⚠️ Using synthetic data")
            
        samples, sample_rate, center_freq = self.capture_data()
        freqs, power_db, metrics = self.analyze_signal(samples, sample_rate, center_freq)
        
        # Display results
        self.display_metrics(metrics, 1)
        
        spectrum_lines = self.create_dynamic_plot(power_db, "📈 SPECTRUM ANALYSIS")
        for line in spectrum_lines:
            print(line)
            
        print(f"\n🎯 Analysis Complete")
        print(f"   Peak Signal: {metrics['peak_power']:.1f} dB at {metrics['peak_freq']:.1f} MHz")
        print(f"   Signal Quality: SNR = {metrics['snr']:.1f} dB")
        print(f"   RMS Level: {metrics['rms']:.3f}")

def main():
    """Main function"""
    visualizer = DynamicVisualizer()
    
    print("📡 ADALM-Pluto Dynamic Signal Visualizer")
    print("=" * 50)
    print("1. 🔄 Real-time dynamic visualization")
    print("2. 📊 Single analysis")
    print("3. 🚪 Exit")
    
    while True:
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            visualizer.real_time_loop()
            break
        elif choice == '2':
            visualizer.single_analysis()
            input("\nPress Enter to continue...")
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
