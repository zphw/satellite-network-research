import os
from log import logger
from plot import PlotAverage
from trial import Trial


# TCP RWIN comparison
class RwinTrial(Trial):
    def _global_init(self):
        self.sudo(self.mlcnet_ssh, 'sysctl -w net.ipv4.tcp_mem="60000000 60000000 60000000"')
        self.sudo(self.mlcnet_ssh, 'sysctl -w net.ipv4.tcp_wmem="60000000 60000000 60000000"')
        self.sudo(self.mlcnet_ssh, 'sysctl -w net.ipv4.tcp_rmem="60000000 60000000 60000000"')

    def _set_default_sysctl_settings(self):
        self.sudo(self.mlcnet_ssh, "sysctl -w net.core.rmem_max=212992")
        self.sudo(self.mlcnet_ssh, "sysctl -w net.core.wmem_max=212992")
        self.sudo(self.mlcnet_ssh, "sysctl -w net.core.rmem_default=212992")
        self.sudo(self.mlcnet_ssh, "sysctl -w net.core.wmem_default=212992")

    def _set_higher_rwin(self):
        self.sudo(self.mlcnet_ssh, "sysctl -w net.core.rmem_max=60000000")
        self.sudo(self.mlcnet_ssh, "sysctl -w net.core.wmem_max=60000000")
        self.sudo(self.mlcnet_ssh, "sysctl -w net.core.rmem_default=60000000")
        self.sudo(self.mlcnet_ssh, "sysctl -w net.core.wmem_default=60000000")

    def run(self):
        self._global_init()

        # Run with default rwin settings
        logger.info("Running with default rwin settings")
        self._set_default_sysctl_settings()
        self._run_a_trial()

        # Run with rwin bigger
        logger.info("Running with higher rwin settings")
        self._set_higher_rwin()
        self._run_a_trial()

        self._set_default_sysctl_settings()

    def run_five_default(self):
        self._global_init()
        self._set_default_sysctl_settings()

        for i in range(5):
            self._run_a_trial()


def main():
    username = ""
    password = ""
    protocol = "cubic"

    rwin_trial = RwinTrial(protocol, username, password, iperf_data="1G")
    rwin_trial.run_five_default()

    p = PlotAverage("CUBIC - Average",
                    [f"{os.getcwd()}/csv_files/{name}.csv" for name in rwin_trial.get_names()],
                    rwin_trial.get_names()[0])
    p.plot_tput_vs_time()


if __name__ == "__main__":
    main()
