import matplotlib.pyplot as plt
import pandas as pd
from log import logger


class Plot:
    def __init__(self, title, csv_files, trial_name, legends=None):
        self.title = title
        self.legends = legends
        self.csv_files = csv_files
        self.trial_name = trial_name
        self.df = []
        for csv in csv_files:
            self.df.append(pd.read_csv(csv))

        self.throughput = []
        self.rtt = []
        self.cwnd = []
        self.retransmissions = []
        self.seconds = []
        self.server_port = 12222

    # compute throughput, RTT, CWND, and retransmission for dataframes
    def _compute_throughput(self):
        for i in range(len(self.df)):
            next_whole_sec = 1
            data_sent = 0
            throughput = []
            seconds = []

            rtt = []
            rtt_avg = 0

            cwnd = []
            cwnd_avg = 0

            retransmissions = []
            retransmissions_count = 0
            start_frame = 1

            for t in range(len(self.df[i]['frame.len'])):
                # only count sent packets
                if self.df[i]['tcp.srcport'][t] == self.server_port:
                    data_sent += self.df[i]['frame.len'][t]

                # rolling average for RTT
                if not pd.isnull(self.df[i]['tcp.analysis.ack_rtt'][t]):
                    if rtt_avg != 0:
                        rtt_avg = (rtt_avg + self.df[i]['tcp.analysis.ack_rtt'][t]) / 2
                    else:
                        rtt_avg = self.df[i]['tcp.analysis.ack_rtt'][t]

                # rolling average for CWND est.
                if not pd.isnull(self.df[i]['tcp.analysis.bytes_in_flight'][t]):
                    if cwnd_avg != 0:
                        cwnd_avg = (cwnd_avg + self.df[i]['tcp.analysis.bytes_in_flight'][t]) / 2
                    else:
                        cwnd_avg = self.df[i]['tcp.analysis.bytes_in_flight'][t]

                # count retransmissions
                if not pd.isnull(self.df[i]['tcp.analysis.retransmission'][t]) or not pd.isnull(
                        self.df[i]['tcp.analysis.fast_retransmission'][t]):
                    retransmissions_count += 1

                if self.df[i]['tcp.time_relative'][t] > float(next_whole_sec):
                    throughput.append((data_sent * 8) / 1000000)
                    seconds.append(next_whole_sec)
                    rtt.append(rtt_avg)
                    cwnd.append(cwnd_avg)
                    retransmissions.append(retransmissions_count / (t - start_frame + 1))

                    data_sent = 0
                    rtt_avg = 0
                    retransmissions_count = 0
                    start_frame = t
                    next_whole_sec += 1

            self.throughput.append(throughput)
            self.rtt.append(rtt)
            self.cwnd.append(cwnd)
            self.retransmissions.append(retransmissions)
            self.seconds.append(seconds)

    def plot_tput_vs_time(self):
        logger.info("Started plotting...")
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


class PlotAverage(Plot):
    def plot(self):
        logger.info("Started plotting...")
        self._compute_throughput()

        fig, axs = plt.subplots(4, gridspec_kw={'height_ratios': [3, 1, 1, 1]})
        fig.set_figheight(8)

        for i in range(len(self.throughput)):
            axs[0].plot(self.seconds[i], self.throughput[i], '.', color='tab:blue')

        max_times = max(self.seconds, key=len)
        avg_tput = []
        avg_rtt = []
        avg_cwnd = []
        avg_retransmission = []
        for t in range(len(max_times)):
            tput_sum = 0
            rtt_sum = 0
            cwnd_sum = 0
            retrans_sum = 0
            num = 0
            for i in range(len(self.df)):
                if len(self.throughput[i]) > t:
                    tput_sum += self.throughput[i][t]
                    rtt_sum += self.rtt[i][t]
                    cwnd_sum += self.cwnd[i][t]
                    retrans_sum += self.retransmissions[i][t]
                    num += 1

            avg_tput.append(tput_sum / num)
            avg_rtt.append(rtt_sum / num)
            avg_cwnd.append(cwnd_sum / num / 1024 / 1024)  # Bytes to MBytes
            avg_retransmission.append(retrans_sum / num)

        axs[0].plot(max_times, avg_tput, color='tab:orange')
        axs[1].plot(max_times, avg_rtt, color='tab:blue')
        axs[2].plot(max_times, avg_cwnd, color='tab:blue')
        axs[3].plot(max_times, avg_retransmission, color='tab:blue')

        fig.suptitle(self.title)
        axs[0].set_ylabel("Throughput (Mbits)")
        axs[1].set_ylabel("RTT (sec.)")
        axs[2].set_ylabel("CWND (MB)")
        axs[3].set_ylabel("Retrans. (%)")
        axs[3].set_xlabel("Time (seconds)")

        plot_filename = f'graphs/{self.trial_name}-throughput-vs-time.png'
        plt.savefig(plot_filename)
        logger.info("Plot saved to " + plot_filename)

        plt.show()


class PlotAverageSummary(Plot):
    def __init__(self, title, csv_files, trial_name, legends=None):
        super().__init__(title, csv_files, trial_name, legends)
        self.breakpoints = None

    def set_breakpoint(self, indexes):
        self.breakpoints = indexes

    def plot_tput_vs_time(self):
        logger.info("Started plotting...")
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


class PlotDownloadTime(Plot):
    def __init__(self, title, csv_files, trial_name, max_size, legends=None):
        super().__init__(title, csv_files, trial_name, legends)
        self.max_size = max_size
        self.download_size = []
        self.breakpoints = None

    def set_breakpoint(self, indexes):
        self.breakpoints = indexes

    def _compute_download_size(self):
        for i in range(len(self.df)):
            next_whole_mbyte = 1
            data_sent = 0
            download_size = []
            seconds = []

            for t in range(len(self.df[i]['frame.len'])):
                # only count sent packets
                if self.df[i]['tcp.srcport'][t] == self.server_port:
                    data_sent += self.df[i]['frame.len'][t]

                if data_sent / 1000000 >= float(next_whole_mbyte):
                    download_size.append(next_whole_mbyte)
                    seconds.append(self.df[i]['tcp.time_relative'][t])

                    if next_whole_mbyte >= self.max_size:
                        break

                    next_whole_mbyte += 1

            self.download_size.append(download_size)
            self.seconds.append(seconds)

    def plot(self):
        logger.info("Started plotting...")
        self._compute_download_size()

        start_index = 0
        end_index = len(self.download_size) + 1
        breakpoints_cursor = 0

        while start_index < end_index:
            if len(self.breakpoints) > breakpoints_cursor:
                end_index = self.breakpoints[breakpoints_cursor]
                breakpoints_cursor += 1

            max_times = max(self.seconds[start_index:end_index], key=len)
            avg_size = []
            for t in range(len(max_times)):
                size_sum = 0
                size_num = 0
                for data in self.download_size[start_index:end_index]:
                    if len(data) > t:
                        size_sum += data[t]
                        size_num += 1
                size_sum /= size_num
                avg_size.append(size_sum)

            plt.plot(avg_size, max_times, marker='x')

            start_index = end_index
            end_index = len(self.download_size) + 1

        plt.xlabel("Download Size (MBytes)")
        plt.ylabel("Time (seconds)")
        plt.legend(self.legends)
        plt.title(self.title)
        plot_filename = f'graphs/{self.trial_name}-download-time.png'
        plt.savefig(plot_filename)
        logger.info("Plot saved to " + plot_filename)

        plt.show()
