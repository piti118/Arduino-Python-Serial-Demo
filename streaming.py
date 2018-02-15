import warnings
import serial
import serial.tools.list_ports
import time
import collections
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib import style
style.use("ggplot")

# from matplotlib import pyplot as plt
import threading

import tkinter as tk
from matplotlib.figure import Figure




def connect_arduino(baudrate=9600):
    def is_arduino(p):
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


class DataStream:
    def __init__(self, ser):
        self.ser = ser
        ndata = 2000
        self.time = collections.deque([], ndata)
        self.data = collections.deque([], ndata)
        self.lock = threading.Lock()
        self.shouldStop = True
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True  # Daemonize thread
        self.shouldStop = False
        self.thread.start()

    def run(self):
        while not self.shouldStop:
            self.get_data()

    def stop(self):
        self.shouldStop = True
        if self.thread is not None:
            self.thread.join()
            self.thred = None

    def get_data(self):
        try:
            data = self.ser.read_until(b"\n", 255).decode().strip()
        except UnicodeDecodeError as e:
            warnings.warn('invalid data got non unicode. This may happen at the start.')
            return

        # print(data)
        splitted = data.split(' ')

        if len(splitted) == 2:
            t, d = splitted
            ft, fd = 0., 0.
            try:
                ft, fd = float(t), float(d)
                self.time.append(ft)
                self.data.append(fd)
            except ValueError as e:
                pass

    def mean(self):
        return -1 if not self.data else (sum(self.data) / len(self.data))

    def max(self):
        return -1 if not self.data else max(self.data)

    def min(self):
        return -1 if not self.data else min(self.data)

    def status(self):
        return "ndata = %d" % (len(self.time))


class LivePlot(tk.Frame):
    def __init__(self, master, streamer, *arg, **kwargs):
        super().__init__(master, *arg, **kwargs)
        self.streamer = streamer
        self.fig = Figure(figsize=(10, 4.5))

        self.ax = self.fig.add_subplot(1, 1, 1)
        self.line, = self.ax.plot(self.streamer.time, self.streamer.data, 'r')
        self.ax.set_ylim(400, 600)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack()
        self.should_stop = True
        # self.ani = animation.FuncAnimation(self.fig, self.animate, interval=50, blit=False)

    def start(self):
        self.should_stop = False
        refresh_rate = 20

        def update():
            if not self.should_stop:
                self.animate()
                self.after(refresh_rate, update)

        self.after(refresh_rate, update)

    def animate(self):
        self.line.set_data(self.streamer.time, self.streamer.data)
        if len(self.streamer.time) > 2:
            self.ax.set_xlim(self.streamer.time[0], self.streamer.time[-1])
        else:
            self.ax.set_xlim(0, 30)
        self.canvas.draw()

    def stop(self):
        self.should_stop = True


class LabelValue(tk.Frame):
    def __init__(self, master, vname, vtext, *arg, **kwargs):
        super().__init__(master, *arg, **kwargs)
        self.label = tk.Label(text=vname)
        self.label.pack(side=tk.LEFT)
        self.value = tk.Label(textvariable=vtext)
        self.value.pack(side=tk.LEFT)


class SummaryInfo(tk.Frame):
    def __init__(self, master, streamer, *arg, **kwargs):
        super().__init__(master, *arg, **kwargs)
        self.streamer = streamer
        self.mean = tk.DoubleVar()
        self.max = tk.DoubleVar()
        self.min = tk.DoubleVar()
        self.mean_label = LabelValue(self, 'Mean', self.mean)
        self.mean_label.pack(side=tk.TOP)
        self.max_label = LabelValue(self, 'Max', self.max)
        self.max_label.pack(side=tk.TOP)
        self.min_label = LabelValue(self, 'Min', self.min)
        self.min_label.pack(side=tk.TOP)

    def update(self):
        self.mean.set(self.streamer.mean())
        self.max.set(self.streamer.max())
        self.min.set(self.streamer.min())

    def start(self):
        self.update()
        self.after(500, self.start)


def main():
    with connect_arduino(250000) as ser:
        streamer = DataStream(ser)

        root = tk.Tk()
        # root.geometry('1200x700+200+100')
        lplot = LivePlot(root, streamer)
        lplot.start()
        lplot.pack(side=tk.TOP)
        sinfo = SummaryInfo(root, streamer)
        sinfo.pack(side=tk.TOP)
        streamer.start()
        sinfo.start()
        root.mainloop()


if __name__ == '__main__':
    main()
