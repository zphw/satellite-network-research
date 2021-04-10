import matplotlib.pyplot as plt
import pandas as pd
from log import logger


class PlotOneProtocol:
    def __init__(self, protocol, csv_file, output_name):
        self.protocol = protocol
        self.csv_file = csv_file
        self.output_name = output_name
        self.df = pd.read_csv(csv_file)
        self.times_raw = pd.to_datetime(self.df['frame.time'], infer_datetime_format=True)
        self.times_since_start = []
        self.throughput = []
        self.seconds = []

    def __compute_time_since_start(self):
        for i in range(len(self.times_raw)):
            td = pd.Timedelta(str(self.times_raw[i] - self.times_raw[0]))
            self.times_since_start.append(td.seconds + (td.microseconds / 1000000) + (td.nanoseconds / 1000000000))

    def __compute_throughput(self):
        next_whole_sec = 1
        data_sent = 0
        for i in range(len(self.df['frame.len'])):
            data_sent += self.df['frame.len'][i]

            if self.times_since_start[i] >= float(next_whole_sec):
                self.throughput.append((data_sent * 8) / 1000000)
                self.seconds.append(next_whole_sec)
                data_sent = 0
                next_whole_sec += 1

    def plot_tput_vs_time(self):
        logger.info("Started plotting...")
        self.__compute_time_since_start()
        self.__compute_throughput()

        plt.plot(self.seconds, self.throughput)
        plt.xlabel("Time (seconds)")
        plt.ylabel("Throughput (Mbits)")
        plt.legend([self.protocol])
        plt.title('Throughput vs Time')
        filename = f'graphs/{self.output_name}-throughput-vs-time.png'
        plt.savefig(filename)
        logger.info("Plot saved to " + filename)

        plt.show()
