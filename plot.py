import matplotlib.pyplot as plt
import pandas as pd
from log import logger


class PlotComparison:
    def __init__(self, title, csv_files, trial_name, legends=None):
        self.title = title
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
        for time_raw in self.times_raw:
            start_time = time_raw[0]
            time_since_start = []
            for t in time_raw:
                td = pd.Timedelta(str(t - start_time))
                time_since_start.append(td.seconds + (td.microseconds / 1000000) + (td.nanoseconds / 1000000000))
            self.times_since_start.append(time_since_start)

    def _compute_throughput(self):
        for i in range(len(self.df)):
            next_whole_sec = 1
            data_sent = 0
            throughput = []
            seconds = []
            for t in range(len(self.df[i]['frame.len'])):
                data_sent += self.df[i]['frame.len'][t]

                if self.times_since_start[i][t] > float(next_whole_sec):
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
        plt.title(self.title)
        plot_filename = f'graphs/{self.trial_name}-throughput-vs-time.png'
        plt.savefig(plot_filename)
        logger.info("Plot saved to " + plot_filename)

        plt.show()


class PlotAverage(PlotComparison):
    def plot_tput_vs_time(self):
        logger.info("Started plotting...")
        self._compute_time_since_start()
        self._compute_throughput()

        for i in range(len(self.throughput)):
            plt.plot(self.seconds[i], self.throughput[i], '.', color='tab:blue')

        max_times = max(self.seconds, key=len)
        avg_tput = []
        for t in range(len(max_times)):
            tput_sum = 0
            tput_num = 0
            for i in range(len(self.throughput)):
                if len(self.throughput[i]) > t:
                    tput_sum += self.throughput[i][t]
                    tput_num += 1
            tput_sum /= tput_num
            avg_tput.append(tput_sum)

        plt.plot(max_times, avg_tput, color='tab:orange')

        plt.xlabel("Time (seconds)")
        plt.ylabel("Throughput (Mbits)")
        plt.title(self.title)
        plot_filename = f'graphs/{self.trial_name}-throughput-vs-time.png'
        plt.savefig(plot_filename)
        logger.info("Plot saved to " + plot_filename)

        plt.show()


class PlotMultipleAverage(PlotComparison):
    def __init__(self, title, csv_files, trial_name, legends=None):
        super().__init__(title, csv_files, trial_name, legends)
        self.breakpoints = None

    def set_breakpoint(self, indexes):
        self.breakpoints = indexes

    def plot_tput_vs_time(self):
        logger.info("Started plotting...")
        self._compute_time_since_start()
        self._compute_throughput()

        start_index = 0
        end_index = len(self.throughput) + 1
        breakpoints_cursor = 0

        while start_index < end_index:
            if len(self.breakpoints) > breakpoints_cursor:
                end_index = self.breakpoints[breakpoints_cursor]
                breakpoints_cursor += 1

            max_times = max(self.seconds[start_index:end_index], key=len)
            avg_tput = []
            for t in range(len(max_times)):
                tput_sum = 0
                tput_num = 0
                for data in self.throughput[start_index:end_index]:
                    if len(data) > t:
                        tput_sum += data[t]
                        tput_num += 1
                tput_sum /= tput_num
                avg_tput.append(tput_sum)

            plt.plot(max_times, avg_tput)

            start_index = end_index
            end_index = len(self.throughput) + 1

        plt.xlabel("Time (seconds)")
        plt.ylabel("Throughput (Mbits)")
        plt.legend(self.legends)
        plt.title(self.title)
        plot_filename = f'graphs/{self.trial_name}-throughput-vs-time.png'
        plt.savefig(plot_filename)
        logger.info("Plot saved to " + plot_filename)

        plt.show()
