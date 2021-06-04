import serial
import time


# matching sketch at
# https://create.arduino.cc/editor/piti118/d62e2b1e-f304-48b8-99cd-0d57f0375e1c/preview
def main():
    address = "/dev/cu.usbserial-1130"  # change this to yours!!!
    baudrate = 9600  # make sure the baud rate matches
    with serial.Serial(address, baudrate) as ser:
        time.sleep(2)  # it takes a while for arduino to get ready so wait!
        for i in range(100):
            ser.write(b"on\n")  # you could do .c
            print(ser.read_until(b"\n", 255), '....')
            time.sleep(0.5)
            ser.write("off\n".encode())  # string.encode gives you byte array
            print(ser.read_until(b"\n", 255), '...')
            time.sleep(0.5)


if __name__ == "__main__":
    main()
