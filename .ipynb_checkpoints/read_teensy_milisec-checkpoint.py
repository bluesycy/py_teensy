import serial
import time
import csv
import datetime
# --- Configuration ---
# IMPORTANT: Replace '/dev/ttyACM0' with the actual serial port for your Teensy in WSL
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200
OUTPUT_CSV_FILE = 'teensy_millis_data.csv'
READ_TIMEOUT = 1 # seconds, how long to wait for data on the serial port
def read_and_save_millis():
    ser = None # Initialize serial port object to None
    csv_file = None # Initialize CSV file object to None
    csv_writer = None # Initialize CSV writer object to None
    try:
        print(f"Opening serial port: {SERIAL_PORT} at {BAUD_RATE} baud...")
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=READ_TIMEOUT # Timeout for reading a line
        )

        # Toggle DTR to reset the Arduino
        ser.setDTR(False)
        time.sleep(1)
        ser.flushInput()
        ser.setDTR(True)
        print("Serial port opened successfully.")
        # Open CSV file for writing
        csv_file = open(OUTPUT_CSV_FILE, 'w', newline='')
        csv_writer = csv.writer(csv_file)
        # Write CSV header
        csv_writer.writerow(['Python_Timestamp_UTC', 'Teensy_Millis'])
        print(f"Saving data to '{OUTPUT_CSV_FILE}'...")
        print("Press Ctrl+C to stop.")
        while True:
            
            # Read a line from the serial port
            # readline() blocks until a newline or timeout occurs
            line = ser.readline()
            if line:
                try:
                    # Decode bytes to string and remove leading/trailing whitespace (like newlines)
                    teensy_millis_str = line.decode('utf-8').strip()
                    # Convert the string to an integer
                    teensy_millis = int(teensy_millis_str)
                    # Get current UTC timestamp from Python
                    python_timestamp_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    # Write to CSV
                    csv_writer.writerow([python_timestamp_utc, teensy_millis])
                    csv_file.flush() # Ensure data is written to disk immediately
                    print(f"Read: Python_Timestamp={python_timestamp_utc}, Teensy_Millis={teensy_millis}")
                except ValueError:
                    print(f"Warning: Could not convert data to integer: '{teensy_millis_str}'. Skipping line.")
                except UnicodeDecodeError:
                    print(f"Warning: Could not decode bytes: {line}. Skipping line.")
            # No 'else' for empty line because readline() blocks for timeout.
            # If line is empty, it means timeout occurred, and we'll just wait for the next iteration.

            
    except serial.SerialException as e:
        print(f"ERROR: Could not open serial port {SERIAL_PORT}: {e}")
        print("Please ensure the Teensy is connected, the correct port is specified,")
        print("and you have read/write permissions (e.g., add user to 'dialout' group).")
    except KeyboardInterrupt:
        print("\nStopping data collection.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Close the serial port if it was opened
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")
        # Close the CSV file if it was opened
        if csv_file:
            csv_file.close()
            print(f"Data saved to {OUTPUT_CSV_FILE}.")
if __name__ == "__main__":
    read_and_save_millis()












