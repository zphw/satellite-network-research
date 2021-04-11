import matplotlib.pyplot as plt
import pandas as pd
from log import logger


class PlotOne:
    def __init__(self, protocol, csv_file, output_name):
        self.protocol = protocol
        self.csv_file = csv_file
        self.output_name = output_name
        self.df = pd.read_csv(csv_file)
        self.times_raw = pd.to_datetime(self.df['frame.time'], infer_datetime_format=True)
        self.times_since_start = []
        self.throughput = []
        self.seconds = []

    def _compute_time_since_start(self):
        for i in range(len(self.times_raw)):
            td = pd.Timedelta(str(self.times_raw[i] - self.times_raw[0]))
            self.times_since_start.append(td.seconds + (td.microseconds / 1000000) + (td.nanoseconds / 1000000000))

    def _compute_throughput(self):
        next_whole_sec = 1
        data_sent = 0
        for i in range(len(self.df['frame.len'])):
            data_sent += self.df['frame.len'][i]

            if self.times_since_start[i] > float(next_whole_sec):
                self.throughput.append((data_sent * 8) / 1000000)
                self.seconds.append(next_whole_sec)
                data_sent = 0
                next_whole_sec += 1

    def plot_tput_vs_time(self):
        logger.info("Started plotting...")
        self._compute_time_since_start()
        self._compute_throughput()

        plt.plot(self.seconds, self.throughput)
        plt.xlabel("Time (seconds)")
        plt.ylabel("Throughput (Mbits)")
        plt.legend([self.protocol])
        plt.title('Throughput vs Time')
        filename = f'graphs/{self.output_name}-throughput-vs-time.png'
        plt.savefig(filename)
        logger.info("Plot saved to " + filename)

        plt.show()


class PlotComparison:
    def __init__(self, protocol, legends, csv_files, trial_name):
        self.protocol = protocol
        self.legends = legends
        self.csv_files = csv_files
        self.trial_name = trial_name
        self.df = []
        for csv in csv_files:
            self.df.append(pd.read_csv(csv))

        self.times_raw = []
        for data in self.df:
            self.times_raw.append(pd.to_datetime(data['frame.time'], infer_datetime_format=True))

        self.times_since_start = []
        self.throughput = []
        self.seconds = []

    def _compute_time_since_start(self):
        for i in range(len(self.times_raw[0])):
            td = pd.Timedelta(str(self.times_raw[0][i] - self.times_raw[0][0]))
            self.times_since_start.append(td.seconds + (td.microseconds / 1000000) + (td.nanoseconds / 1000000000))

    def _compute_throughput(self):
        for data in self.df:
            next_whole_sec = 1
            data_sent = 0
            throughput = []
            seconds = []
            for i in range(len(data['frame.len'])):
                data_sent += data['frame.len'][i]

                if self.times_since_start[i] > float(next_whole_sec):
                    throughput.append((data_sent * 8) / 1000000)
                    seconds.append(next_whole_sec)
                    data_sent = 0
                    next_whole_sec += 1

            self.throughput.append(throughput)
            self.seconds.append(seconds)

    def plot_tput_vs_time(self):
        logger.info("Started plotting...")
        self._compute_time_since_start()
        self._compute_throughput()

        for i in range(len(self.throughput)):
            plt.plot(self.seconds[i], self.throughput[i])
        plt.xlabel("Time (seconds)")
        plt.ylabel("Throughput (Mbits)")
        plt.legend(self.legends)
        plt.title(self.protocol)
        plot_filename = f'graphs/{self.trial_name}-throughput-vs-time.png'
        plt.savefig(plot_filename)
        logger.info("Plot saved to " + plot_filename)

        plt.show()
