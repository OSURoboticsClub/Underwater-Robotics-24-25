import serial
import threading
import re
import sys

rx_buffer = bytearray()
finished = False
ser = None

def serial_reader():
    global ser
    global rx_buffer

    PACKET_PATTERN = re.compile(r"^EX31,\d+,\d+,\d+\.\d{2}$")
    with open("float_data.csv", "w") as f:
        f.write("name,time,pascals,depth\n")
        while not finished:
            try:
                while ser and ser.in_waiting:
                    c = ser.read(1)
                    if c == b'\n':
                        line = rx_buffer.decode('utf-8', errors='ignore').strip()
                        rx_buffer.clear()
                        print(f'Received from Esp32: {line}')
                        if line and PACKET_PATTERN.fullmatch(line):
                            f.write(line + '\n')
                        else:
                            print(f'Failed to match with: "{line}".')
                    else:
                        rx_buffer += c
            except Exception as e:
                print(f'Serial read error: {e}')

def serial_writer():
    global ser
    while not finished:
        msg = input() + "\n"
        try:
            ser.write(msg.encode('utf-8'))
        except Exception as e:
            print(f'Serial write errors: {e}')

def main():
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = '/dev/usb_back'
    baud = '115200'

    global ser
    try:
        ser = serial.Serial(port, baud, timeout=0)
        ser.flushInput()
        ser.flushOutput()
        print(f'Opened serial port {port} at {baud} baud.')
    except serial.SerialException as e:
        print(f'Failed to open serial port {port}: {e}')
        ser = None
        return

    writer_thread = threading.Thread(target=serial_reader, daemon=True)
    writer_thread.start()


    try:
        serial_writer()
    except KeyboardInterrupt:
        print('Shutting down (SIGINT)')
        pass
    finally:
        global finished
        finished = True
        writer_thread.join(timeout=0.0);
        if ser and ser.is_open:
            print('Closing serial port')
            ser.close()

if __name__ == '__main__':
    main()
