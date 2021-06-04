import warnings
import serial
import serial.tools.list_ports
import time
import tkinter as tk
# matching arduino code
# #define BUFFERSIZE 255
# #define LEDPIN 9
# void setup() {
#   // put your setup code here, to run once:
#   Serial.begin(9600);
#   pinMode(LEDPIN, OUTPUT);
# }

# void loop() {
#   char buffer[BUFFERSIZE];
#   if(Serial.available()){//there is a byte here.
#     int nbytes = Serial.readBytesUntil('\n', buffer, BUFFERSIZE-1);
#     buffer[nbytes] = 0; //null terminated string
#     String message = String(buffer);
#     analogWrite(LEDPIN, message.toInt());
#     Serial.println("ok");
#   }
# }

def connect_arduino(baudrate=9600): # a more civilized way to connect to arduino
    def is_arduino(p):
        # need more comprehensive test
        return p.device == '/dev/cu.usbserial-1130'
        # return p.manufacturer is not None and 'arduino' in p.manufacturer.lower()

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


class Dimmer:
    def __init__(self, ser):
        self.ser = ser

    def send_rec(self, msg):
        self.ser.write((msg + "\n").encode())
        return self.ser.read_until(b"\n", 255)

    def send_dim_cmd(self, i):
        self.send_rec('%d'%i)

class DimmerUI:
    def __init__(self, parent, dimmer):
        self.frame = tk.Frame(parent)
        self.dimmer = dimmer
        self.slider = tk.Scale(self.frame, from_=0, to=255, 
                               orient="horizontal",
                               command=self.updateValue)
        #self.slider.bind("<ButtonRelease-1>", self.updateValue)

        self.slider.pack()
        self.frame.pack()

    def updateValue(self, event):
        value = self.slider.get()
        self.dimmer.send_dim_cmd(value)
        print(value)



def main():
    with connect_arduino() as ser:
        dimmer = Dimmer(ser)
        root = tk.Tk()
        ui = DimmerUI(root, dimmer)
        root.mainloop()


if __name__ == '__main__':
    main()
