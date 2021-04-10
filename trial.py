import os
import time
from log import logger
from plot import PlotOneProtocol
from ssh_client import SSHClientOverProxy


class Trial:
    def __init__(self, protocol, username, password, iperf_data=None, iperf_time=10):
        self.protocol = protocol
        self.username = username
        self.password = password
        self.proxy_host = "cs.wpi.edu"
        self.client_host = "glomma.cs.wpi.edu"
        self.protocol_host = {
            "cubic": "mlcneta.cs.wpi.edu",
            "hybla": "mlcnetb.cs.wpi.edu",
            "bbr": "mlcnetc.cs.wpi.edu",
            "pcc": "mlcnetd.cs.wpi.edu"
        }
        self.iperf_server_port = 12222
        self.iperf3_data = iperf_data
        self.iperf3_time = iperf_time
        self.output_name = f"{protocol}-{int(time.time())}"

        # init glomma client
        logger.info("Connecting to glomma...")
        glomma_client = SSHClientOverProxy(username=self.username,
                                           password=self.password,
                                           proxy_host=self.proxy_host,
                                           host=self.client_host)
        self.glomma_ssh = glomma_client.get_client()

    # Trial Procedure Functions Start #

    def __init_mlcnet_client(self, host):
        self.mlcnet_client = SSHClientOverProxy(username=self.username,
                                                password=self.password,
                                                proxy_host=self.proxy_host,
                                                host=host)
        self.mlcnet_ssh = self.mlcnet_client.get_client()

    def __start_iperf3_server(self):
        self.mlcnet_ssh.exec_command("nohup iperf3 -s -p {} > /dev/null 2>&1 &".format(self.iperf_server_port))

    def __start_tcpdump(self, pcap_filename):
        stdin, stdout, stderr = self.mlcnet_ssh.exec_command(
            "sudo -S tcpdump -i ens2 -s 96 src port {} -w {}".format(self.iperf_server_port, pcap_filename),
            get_pty=True)
        stdin.write(f'{self.password}\n')
        stdin.flush()

    def __start_iperf3_client(self, server):
        if self.iperf3_data is not None:
            command = "iperf3 -R -c {} -p {} -n{}".format(server, self.iperf_server_port, self.iperf3_data)
        else:
            command = "iperf3 -R -c {} -p {} -t {}".format(server, self.iperf_server_port, self.iperf3_time)

        stdin, stdout, stderr = self.glomma_ssh.exec_command(command, get_pty=True)
        for line in iter(lambda: stdout.readline(1024), ""):
            logger.debug(line.replace("\n", ""))

    def __shutdown_tasks(self):
        self.mlcnet_ssh.exec_command('killall tcpdump')
        self.mlcnet_ssh.exec_command('killall iperf3')

    def __pcap_to_csv(self, pcap_filename, csv_filename):
        command = f'tshark -r ~/{pcap_filename} -T fields \
                                    -e frame.number \
                                    -e frame.len \
                                    -e tcp.window_size \
                                    -e ip.src \
                                    -e ip.dst \
                                    -e tcp.srcport \
                                    -e tcp.dstport \
                                    -e frame.time \
                                    -E header=y \
                                    -E separator=, \
                                    -E quote=d \
                                    -E occurrence=f \
                                    > ~/{csv_filename}'
        self.mlcnet_ssh.exec_command(command)

    def __download_mlcnet_file(self, remote_file, download_to):
        sftp = self.mlcnet_ssh.open_sftp()
        sftp.get(remote_file, download_to)
        sftp.close()

    # Trial Procedure Functions End #

    def __run_a_trial(self, protocol):
        logger.info("Started trial for " + protocol)

        logger.info("Connecting to MLCnet server...")
        self.__init_mlcnet_client(self.protocol_host[protocol])

        # start iperf3 server on MLCnet
        logger.info(f"Starting iperf3 server on port {self.iperf_server_port}")
        self.__start_iperf3_server()

        # start tcpdump on server
        logger.info(f"Starting tcpdump on {self.protocol_host[protocol]}")
        pcap_filename = self.output_name + ".pcap"
        self.__start_tcpdump(pcap_filename)

        # run iperf3 client on glomma
        logger.info("Executing iperf3 on client")
        self.__start_iperf3_client(self.protocol_host[protocol])

        # shutdown tcpdump and iperf3 server
        logger.info("Stopping tcpdump and iperf3...")
        self.__shutdown_tasks()

        # export pcap to csv
        logger.info("Exporting pcap data to csv...")
        csv_filename = self.output_name + ".csv"
        self.__pcap_to_csv(pcap_filename, csv_filename)

        # download csv
        logger.info("Downloading the csv file...")
        self.__download_mlcnet_file(f"/home/{self.username}/{csv_filename}",
                                    f"{os.getcwd()}/csv_files/{csv_filename}")
        logger.info(f"CSV saved to csv_files/{csv_filename}")

        # clear temp files on mlcnet server
        logger.info("Cleaning files on servers...")
        self.mlcnet_ssh.exec_command(f"rm -rf {pcap_filename} {csv_filename}")

        logger.info("Trial done.")

        self.mlcnet_client.close()

    def run(self):
        self.__run_a_trial(self.protocol)

    def get_name(self):
        return self.output_name

    def __del__(self):
        self.glomma_ssh.close()


def main():
    username = ""
    password = ""
    protocol = "cubic"

    trial = Trial(protocol, username, password, iperf_time=60)
    trial.run()

    p = PlotOneProtocol(protocol, f"{os.getcwd()}/csv_files/{trial.get_name()}.csv", trial.get_name())
    p.plot_tput_vs_time()


if __name__ == "__main__":
    main()
