import warnings
import serial
import serial.tools.list_ports
import time
import tkinter as tk

# matching sketch at
# https://create.arduino.cc/editor/piti118/d62e2b1e-f304-48b8-99cd-0d57f0375e1c/preview

def connect_arduino(baudrate=9600): # a more civilized way to connect to arduino
    def is_arduino(p):
        # need more comprehensive test
        return p.manufacturer is not None and 'arduino' in p.manufacturer.lower()

    ports = serial.tools.list_ports.comports()
    arduino_ports = [p for p in ports if is_arduino(p)]

    def port2str(p):
        return "%s - %s (%s)" % (p.device, p.description, p.manufacturer)

    if not arduino_ports:
        portlist = "\n".join([port2str(p) for p in ports])
        raise IOError("No Arduino found\n" + portlist)

    if len(arduino_ports) > 1:
        portlist = "\n".join([port2str(p) for p in ports])
        warnings.warn('Multiple Arduinos found - using the first\n' + portlist)

    selected_port = arduino_ports[0]
    print("Using %s" % port2str(selected_port))
    ser = serial.Serial(selected_port.device, baudrate)
    time.sleep(2)  # this is important it takes time to handshake
    return ser


class LightSwitch:
    def __init__(self, ser):
        self.ser = ser

    def send_rec(self, msg):
        self.ser.write((msg + "\n").encode())
        return self.ser.read_until(b"\n", 255)

    def get_status(self):
        self.send_rec('status')

    def turn_on(self):
        self.send_rec('on')

    def turn_off(self):
        self.send_rec('off')


class SwitchUI:
    def __init__(self, parent, switch):
        self.switch = switch
        self.frame = tk.Frame(parent)
        self.on_button = tk.Button(self.frame,
                                   text="on",
                                   command=lambda: switch.turn_on()).pack()
        self.off_button = tk.Button(self.frame,
                                    text="off",
                                    command=lambda: switch.turn_off()).pack()
        self.frame.pack()


def main():
    with connect_arduino() as ser:
        ls = LightSwitch(ser)
        root = tk.Tk()
        ui = SwitchUI(root, ls)
        root.mainloop()


if __name__ == '__main__':
    main()
