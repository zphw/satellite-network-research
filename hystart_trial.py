import os
from log import logger
from plot import PlotAverage, PlotMultipleAverage
from trial import Trial


# TCP HyStart on/off
class HystartTrial(Trial):
    def _global_init(self):
        self.sudo(self.mlcnet_ssh, 'sysctl -w net.ipv4.tcp_mem="60000000 60000000 60000000"')
        self.sudo(self.mlcnet_ssh, 'sysctl -w net.ipv4.tcp_wmem="60000000 60000000 60000000"')
        self.sudo(self.mlcnet_ssh, 'sysctl -w net.ipv4.tcp_rmem="60000000 60000000 60000000"')

    def _set_hystart(self, value):
        self.sudo(self.mlcnet_ssh, f'bash -c "echo {value} > /sys/module/tcp_cubic/parameters/hystart"')

    def run(self):
        self._global_init()

        # Run with hystart on
        logger.info("Running with hystart on")
        self._set_hystart(1)
        for i in range(5):
            self._run_a_trial()

        # Run with hystart off
        logger.info("Running with hystart off")
        self._set_hystart(0)
        for i in range(5):
            self._run_a_trial()

        self._set_hystart(1)


def main():
    username = ""
    password = ""
    protocol = "cubic"

    hystart_trial = HystartTrial(protocol, username, password, iperf_data="1G")
    hystart_trial.run()

    # first 5 will be trials with hystart on - :5
    p_on = PlotAverage("CUBIC - HyStart On",
                       [f"{os.getcwd()}/csv_files/{name}.csv" for name in hystart_trial.get_names()[:5]],
                       hystart_trial.get_names()[0])
    p_on.plot_tput_vs_time()

    # last 5 will be trials with hystart off - 5:
    p_off = PlotAverage("CUBIC - HyStart Off",
                        [f"{os.getcwd()}/csv_files/{name}.csv" for name in hystart_trial.get_names()[5:]],
                        hystart_trial.get_names()[5])
    p_off.plot_tput_vs_time()

    # two average lines
    p_averages = PlotMultipleAverage("CUBIC - HyStart On/Off",
                                     [f"{os.getcwd()}/csv_files/{name}.csv" for name in hystart_trial.get_names()],
                                     hystart_trial.get_names()[0] + "_avg",
                                     ["HyStar On", "HyStart Off"])
    p_averages.set_breakpoint([5])
    p_averages.plot_tput_vs_time()


if __name__ == "__main__":
    main()
