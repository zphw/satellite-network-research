import os
from log import logger
from plot import PlotAverage, PlotAverageSummary
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

        # 10 rounds on/off
        for i in range(10):
            logger.info("Running with hystart on")
            self._set_hystart(1)
            self._run_a_trial()

            logger.info("Running with hystart off")
            self._set_hystart(0)
            self._run_a_trial()

        self._set_hystart(1)

    def run_test(self):
        self._global_init()
        self._set_hystart(0)
        self._run_a_trial()
        self._set_hystart(1)


def main():
    username = ""
    password = ""
    protocol = "cubic"

    hystart_trial = HystartTrial(protocol, username, password, iperf_data="1G")
    hystart_trial.run()

    # trials with hystart on
    p_on = PlotAverage("CUBIC - HyStart On",
                       [f"{os.getcwd()}/csv_files/{name}.csv" for name in hystart_trial.get_names()[::2]],
                       hystart_trial.get_names()[0] + "_on")
    p_on.plot()

    # trials with hystart off
    p_off = PlotAverage("CUBIC - HyStart Off",
                        [f"{os.getcwd()}/csv_files/{name}.csv" for name in hystart_trial.get_names()[1::2]],
                        hystart_trial.get_names()[0] + "_off")
    p_off.plot()

    # two average lines
    """p_averages = PlotAverageSummary("CUBIC - HyStart On/Off",
                                    [f"{os.getcwd()}/csv_files/{name}.csv" for name in hystart_trial.get_names()],
                                    hystart_trial.get_names()[0] + "_avg",
                                    ["HyStart On", "HyStart Off"])
    p_averages.set_breakpoint([5])
    p_averages.plot_tput_vs_time()"""


if __name__ == "__main__":
    main()
