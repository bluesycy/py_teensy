import serial
import time
import csv
import datetime
import re # Import the regular expression module

# --- Configuration ---
# IMPORTANT: Replace '/dev/ttyACM0' with the actual serial port for your Teensy in WSL
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200
OUTPUT_CSV_FILE = 'sensor_data.csv' # Changed filename for clarity
# READ_TIMEOUT should be relatively low (e.g., 0.1 or 0.05) to allow quick checking for new data
# or even None if you want readline() to block until data is available.
# For continuous reading, a non-blocking approach (timeout=0) or a very short timeout is best.
READ_TIMEOUT = 0.05 

# --- New Configuration for 5-second saving ---
SAVE_INTERVAL_SECONDS = 5

def parse_serial_data(line):
    """
    Parses a single line of serial output and extracts the values.
    Expected format: "Reading: [int]\tWeight: [float]\tAvgWeight: [float]"
    """
    data = {}
    # Use regular expressions to extract the values
    match = re.search(r"Reading:\s*(\d+)\tWeight:\s*([\d.]+)\tAvgWeight:\s*([\d.]+)", line)
    if match:
        try:
            data['currentReading'] = int(match.group(1))
            data['currentWeight'] = float(match.group(2))
            data['avgWeight'] = float(match.group(3))
        except (ValueError, IndexError) as e:
            # print(f"Error converting parsed values: '{line.strip()}' - {e}") # Uncomment for more verbose error
            return None
    else:
        # print(f"Warning: Line did not match expected format: '{line.strip()}'") # Uncomment for more verbose error
        return None
    return data

def read_and_save_latest_sensor_data_5s():
    ser = None # Initialize serial port object to None
    csv_file = None # Initialize CSV file object to None
    csv_writer = None # Initialize CSV writer object to None
    
    latest_data = None # Store the most recently received and parsed data
    last_save_time = time.time() # Timestamp to track when the last save occurred

    try:
        print(f"Opening serial port: {SERIAL_PORT} at {BAUD_RATE} baud...")
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=READ_TIMEOUT # Timeout for reading a line. Crucial for non-blocking loop.
        )

        # Toggle DTR to reset the Teensy
        ser.setDTR(False)
        time.sleep(1)
        ser.flushInput() # Clear any old data in the input buffer
        ser.setDTR(True)
        print("Serial port opened successfully.")

        # Open CSV file for writing (append mode, 'a', so we don't overwrite on restart)
        # Check if file exists to decide whether to write header
        file_exists = False
        try:
            with open(OUTPUT_CSV_FILE, 'r') as f:
                file_exists = True
        except FileNotFoundError:
            pass

        csv_file = open(OUTPUT_CSV_FILE, 'a', newline='')
        csv_writer = csv.writer(csv_file)

        # Write CSV header only if the file is new
        if not file_exists:
            csv_writer.writerow(['Python_Timestamp_UTC', 'currentReading', 'currentWeight', 'avgWeight'])
            print("CSV header written.")
        else:
            print("Appending to existing CSV file.")

        print(f"Saving latest data every {SAVE_INTERVAL_SECONDS} seconds to '{OUTPUT_CSV_FILE}'...")
        print("Press Ctrl+C to stop.")

        while True:
            # Continuously read and update the 'latest_data' variable
            # We use ser.in_waiting to check if there's data without blocking.
            if ser.in_waiting > 0:
                line_bytes = ser.readline()
                try:
                    line_str = line_bytes.decode('utf-8').strip()
                    parsed_data = parse_serial_data(line_str)
                    
                    if parsed_data:
                        # Update latest_data with the newest reading
                        latest_data = parsed_data
                        # print(f"Received: {latest_data}") # Uncomment to see every incoming reading

                except UnicodeDecodeError:
                    print(f"Warning: Could not decode bytes: {line_bytes}. Skipping line.")
            
            # Check if SAVE_INTERVAL_SECONDS has passed since the last save
            current_time = time.time()
            if (current_time - last_save_time) >= SAVE_INTERVAL_SECONDS:
                if latest_data:
                    # Get current UTC timestamp for the saved entry
                    python_timestamp_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    
                    # Write the latest data point to the CSV
                    csv_writer.writerow([
                        python_timestamp_utc,
                        latest_data['currentReading'],
                        f"{latest_data['currentWeight']:.2f}", # Format to 2 decimal places
                        f"{latest_data['avgWeight']:.2f}"
                    ])
                    csv_file.flush() # Ensure data is written to disk immediately
                    print(f"Saved latest reading: {latest_data} at {python_timestamp_utc}")
                    
                    # You might choose to set latest_data = None here if you only want to save if new data arrives between intervals
                    # but keeping it means it saves the last known value even if no new data arrived in the last 5s.
                else:
                    print(f"No data received yet, waiting for first reading.")
                
                last_save_time = current_time # Reset timer for the next interval

            # A small sleep to prevent the loop from consuming 100% CPU,
            # especially if READ_TIMEOUT is very short or 0.
            time.sleep(0.01) 

    except serial.SerialException as e:
        print(f"ERROR: Could not open serial port {SERIAL_PORT}: {e}")
        print("Please ensure the Teensy is connected, the correct port is specified,")
        print("and you have read/write permissions (e.g., add user to 'dialout' group on Linux).")
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
            print(f"Final data saved to {OUTPUT_CSV_FILE}.")

if __name__ == "__main__":
    read_and_save_latest_sensor_data_5s()