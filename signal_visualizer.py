#!/usr/bin/env python3
"""
Signal Visualizer for ADALM-Pluto SDR
Real-time and log-based signal visualization
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
import json
import csv
import adi
from datetime import datetime
import threading
import time

class SignalVisualizer:
    def __init__(self):
        """Initialize the signal visualizer"""
        self.fig = None
        self.axes = None
        self.lines = []
        self.data_buffer = []
        self.running = False
        self.sdr = None
        
    def setup_plots(self):
        """Setup the plot layout"""
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.suptitle('ADALM-Pluto SDR Signal Visualization', fontsize=16)
        
        # Spectrum plot (top left)
        self.axes[0,0].set_title('Real-Time Spectrum')
        self.axes[0,0].set_xlabel('Frequency (MHz)')
        self.axes[0,0].set_ylabel('Amplitude (dB)')
        self.axes[0,0].grid(True)
        
        # Time domain plot (top right)
        self.axes[0,1].set_title('Time Domain Signal')
        self.axes[0,1].set_xlabel('Sample')
        self.axes[0,1].set_ylabel('Amplitude')
        self.axes[0,1].grid(True)
        
        # Waterfall plot (bottom left)
        self.axes[1,0].set_title('Waterfall Display')
        self.axes[1,0].set_xlabel('Frequency (MHz)')
        self.axes[1,0].set_ylabel('Time')
        
        # Constellation plot (bottom right)
        self.axes[1,1].set_title('IQ Constellation')
        self.axes[1,1].set_xlabel('I (Real)')
        self.axes[1,1].set_ylabel('Q (Imaginary)')
        self.axes[1,1].grid(True)
        
        plt.tight_layout()
        
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
            print("✅ Connected to PlutoSDR")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
            
    def capture_data(self):
        """Capture data from PlutoSDR or generate synthetic data"""
        try:
            if self.sdr:
                # Try to capture real data
                samples = self.sdr.rx()
                return samples, self.sdr.sample_rate, self.sdr.rx_lo
            else:
                # Generate synthetic data for demonstration
                N = 1024
                fs = 2.4e6
                fc = 1e6  # 1 MHz tone
                t = np.arange(N) / fs
                
                # Create a complex signal with noise
                signal = np.exp(1j * 2 * np.pi * fc * t) * 0.5
                noise = (np.random.random(N) + 1j * np.random.random(N) - 0.5 - 0.5j) * 0.1
                samples = signal + noise
                
                return samples, fs, 2.4e9
        except Exception as e:
            print(f"⚠️ Data capture failed: {e}, using synthetic data")
            # Fallback to synthetic data
            N = 1024
            samples = np.random.random(N) + 1j * np.random.random(N)
            return samples, 2.4e6, 2.4e9
            
    def update_plots(self, samples, sample_rate, center_freq):
        """Update all plots with new data"""
        # Clear previous plots
        for ax in self.axes.flat:
            ax.clear()
            
        # 1. Spectrum Plot
        fft_data = np.fft.fftshift(np.fft.fft(samples))
        freqs = np.fft.fftshift(np.fft.fftfreq(len(samples), 1/sample_rate))
        power_db = 20 * np.log10(np.abs(fft_data) + 1e-12)
        actual_freqs = (center_freq + freqs) / 1e6  # Convert to MHz
        
        self.axes[0,0].plot(actual_freqs, power_db, 'b-', linewidth=1)
        self.axes[0,0].set_title('Real-Time Spectrum')
        self.axes[0,0].set_xlabel('Frequency (MHz)')
        self.axes[0,0].set_ylabel('Amplitude (dB)')
        self.axes[0,0].grid(True)
        
        # 2. Time Domain Plot
        time_samples = np.arange(len(samples))
        self.axes[0,1].plot(time_samples, np.real(samples), 'r-', label='Real', alpha=0.7)
        self.axes[0,1].plot(time_samples, np.imag(samples), 'b-', label='Imag', alpha=0.7)
        self.axes[0,1].set_title('Time Domain Signal')
        self.axes[0,1].set_xlabel('Sample')
        self.axes[0,1].set_ylabel('Amplitude')
        self.axes[0,1].legend()
        self.axes[0,1].grid(True)
        
        # 3. Waterfall Plot (simplified)
        # Store recent spectrum data for waterfall
        if not hasattr(self, 'waterfall_data'):
            self.waterfall_data = []
        
        self.waterfall_data.append(power_db)
        if len(self.waterfall_data) > 50:  # Keep last 50 spectra
            self.waterfall_data.pop(0)
            
        if len(self.waterfall_data) > 1:
            waterfall_matrix = np.array(self.waterfall_data)
            im = self.axes[1,0].imshow(waterfall_matrix, aspect='auto', 
                                     extent=[actual_freqs[0], actual_freqs[-1], 
                                           len(self.waterfall_data), 0],
                                     cmap='viridis')
            self.axes[1,0].set_title('Waterfall Display')
            self.axes[1,0].set_xlabel('Frequency (MHz)')
            self.axes[1,0].set_ylabel('Time (updates)')
            
        # 4. Constellation Plot
        self.axes[1,1].scatter(np.real(samples), np.imag(samples), 
                              alpha=0.6, s=1, c='blue')
        self.axes[1,1].set_title('IQ Constellation')
        self.axes[1,1].set_xlabel('I (Real)')
        self.axes[1,1].set_ylabel('Q (Imaginary)')
        self.axes[1,1].grid(True)
        self.axes[1,1].axis('equal')
        
        plt.tight_layout()
        
    def start_real_time(self):
        """Start real-time visualization"""
        print("🚀 Starting real-time visualization...")
        print("📊 Close the plot window to stop")
        
        # Setup plots
        self.setup_plots()
        
        # Try to connect to PlutoSDR
        connected = self.connect_pluto()
        if not connected:
            print("⚠️ Using synthetic data for demonstration")
            
        # Animation function
        def animate(frame):
            if not plt.get_fignums():  # Check if window is closed
                return
                
            samples, sample_rate, center_freq = self.capture_data()
            self.update_plots(samples, sample_rate, center_freq)
            
        # Start animation
        ani = animation.FuncAnimation(self.fig, animate, interval=500, blit=False)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.fig.suptitle(f'ADALM-Pluto SDR Signal Visualization - {timestamp}', fontsize=14)
        
        plt.show()
        
    def visualize_log_file(self, log_file):
        """Visualize data from a log file"""
        print(f"📊 Visualizing log file: {log_file}")
        
        try:
            if log_file.endswith('.csv'):
                self.visualize_csv_log(log_file)
            elif log_file.endswith('.json'):
                self.visualize_json_log(log_file)
            else:
                print("❌ Unsupported file format")
        except Exception as e:
            print(f"❌ Error visualizing log: {e}")
            
    def visualize_csv_log(self, csv_file):
        """Visualize spectrum data from CSV log"""
        frequencies = []
        amplitudes = []
        
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and not row[0].startswith('#') and row[0] != 'Frequency_Hz':
                    try:
                        freq = float(row[0]) / 1e6  # Convert to MHz
                        amp = float(row[1])
                        frequencies.append(freq)
                        amplitudes.append(amp)
                    except (ValueError, IndexError):
                        continue
                        
        if frequencies and amplitudes:
            plt.figure(figsize=(12, 6))
            plt.plot(frequencies, amplitudes, 'b-', linewidth=1)
            plt.title(f'Spectrum Data from {csv_file}')
            plt.xlabel('Frequency (MHz)')
            plt.ylabel('Amplitude (dB)')
            plt.grid(True)
            plt.show()
        else:
            print("❌ No valid data found in CSV file")
            
    def visualize_json_log(self, json_file):
        """Visualize signal data from JSON log"""
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        if 'signal_data' in data:
            # Signal capture visualization
            real_data = data['signal_data']['real']
            imag_data = data['signal_data']['imag']
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Time domain
            samples = np.arange(len(real_data))
            ax1.plot(samples, real_data, 'r-', label='Real', alpha=0.7)
            ax1.plot(samples, imag_data, 'b-', label='Imag', alpha=0.7)
            ax1.set_title('Time Domain Signal')
            ax1.set_xlabel('Sample')
            ax1.set_ylabel('Amplitude')
            ax1.legend()
            ax1.grid(True)
            
            # Constellation
            ax2.scatter(real_data, imag_data, alpha=0.6, s=2)
            ax2.set_title('IQ Constellation')
            ax2.set_xlabel('I (Real)')
            ax2.set_ylabel('Q (Imaginary)')
            ax2.grid(True)
            ax2.axis('equal')
            
            plt.tight_layout()
            plt.show()
            
        elif 'data' in data and 'power_matrix' in data['data']:
            # Waterfall visualization
            power_matrix = np.array(data['data']['power_matrix'])
            frequencies = np.array(data['data']['frequencies']) / 1e6  # Convert to MHz
            timestamps = data['data']['timestamps']
            
            plt.figure(figsize=(10, 6))
            plt.imshow(power_matrix, aspect='auto', 
                      extent=[frequencies[0], frequencies[-1], 
                             timestamps[-1], timestamps[0]],
                      cmap='viridis')
            plt.colorbar(label='Power (dB)')
            plt.title(f'Waterfall Data from {json_file}')
            plt.xlabel('Frequency (MHz)')
            plt.ylabel('Time (s)')
            plt.show()
        else:
            print("❌ Unknown JSON format")

def main():
    """Main function with user menu"""
    visualizer = SignalVisualizer()
    
    print("📊 ADALM-Pluto Signal Visualizer")
    print("=" * 40)
    print("1. Real-time visualization")
    print("2. Visualize log file")
    print("3. Demo with synthetic data")
    print("4. Exit")
    
    while True:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            visualizer.start_real_time()
            break
        elif choice == '2':
            log_file = input("Enter log file path: ").strip()
            visualizer.visualize_log_file(log_file)
        elif choice == '3':
            print("🧪 Starting demo with synthetic data...")
            visualizer.sdr = None  # Force synthetic data
            visualizer.start_real_time()
            break
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice, please try again")

if __name__ == "__main__":
    main()
