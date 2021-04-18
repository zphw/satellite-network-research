import os
import time
from log import logger
from scp import SCPClient
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
        self.output_names = []

        logger.info("Initializing Trial...")

        # init glomma client
        glomma_client = SSHClientOverProxy(username=self.username,
                                           password=self.password,
                                           proxy_host=self.proxy_host,
                                           host=self.client_host)
        self.glomma_ssh = glomma_client.get_client()

        # init MLCnet client
        self.mlcnet_client = SSHClientOverProxy(username=self.username,
                                                password=self.password,
                                                proxy_host=self.proxy_host,
                                                host=self.protocol_host[protocol])
        self.mlcnet_ssh = self.mlcnet_client.get_client()

    # Helpers Start #

    def sudo(self, ssh, command):
        stdin, stdout, stderr = ssh.exec_command(f"sudo -S {command}", get_pty=True)
        stdin.write(f'{self.password}\n')
        stdin.flush()
        return stdin, stdout, stderr

    # Helpers End #

    # Trial Procedure Functions Start #

    def _start_iperf3_server(self):
        self.mlcnet_ssh.exec_command("nohup iperf3 -s -p {} > /dev/null 2>&1 &".format(self.iperf_server_port))

    def _start_tcpdump(self, pcap_filename):
        self.sudo(self.mlcnet_ssh,
                  "tcpdump -i ens2 -s 96 port {} -w {}".format(self.iperf_server_port, pcap_filename))

    def _start_iperf3_client(self, server):
        if self.iperf3_data is not None:
            command = "iperf3 -R -c {} -p {} -n{}".format(server, self.iperf_server_port, self.iperf3_data)
        else:
            command = "iperf3 -R -c {} -p {} -t {}".format(server, self.iperf_server_port, self.iperf3_time)

        stdin, stdout, stderr = self.glomma_ssh.exec_command(command, get_pty=True)
        for line in iter(lambda: stdout.readline(1024), ""):
            logger.debug(line.replace("\n", ""))

    def _shutdown_tasks(self):
        self.sudo(self.mlcnet_ssh, "killall tcpdump")
        self.mlcnet_ssh.exec_command("killall iperf3")

    def _pcap_to_csv(self, pcap_filename, csv_filename):
        command = f'tshark -r ~/{pcap_filename} -T fields \
                                    -e frame.number \
                                    -e frame.len \
                                    -e tcp.window_size \
                                    -e tcp.srcport \
                                    -e tcp.dstport \
                                    -e tcp.analysis.ack_rtt \
                                    -e tcp.analysis.retransmission \
                                    -e tcp.analysis.fast_retransmission \
                                    -e tcp.analysis.bytes_in_flight \
                                    -e tcp.time_relative \
                                    -E header=y \
                                    -E separator=, \
                                    -E quote=d \
                                    -E occurrence=f \
                                    > ~/{csv_filename}'
        stdin, stdout, stderr = self.mlcnet_ssh.exec_command(command)
        while not stdout.channel.exit_status_ready():
            time.sleep(1)

    def _download_mlcnet_file(self, remote_file, download_to):
        scp = SCPClient(self.mlcnet_ssh.get_transport())
        scp.get(remote_file, download_to)
        scp.close()

    # Trial Procedure Functions End #

    def _run_a_trial(self):
        logger.info("Started trial for " + self.protocol)
        output_name = f"{self.protocol}-{int(time.time())}"
        self.output_names.append(output_name)

        # start iperf3 server on MLCnet
        logger.info(f"Starting iperf3 server on port {self.iperf_server_port}")
        self._start_iperf3_server()

        # start tcpdump on server
        logger.info(f"Starting tcpdump on {self.protocol_host[self.protocol]}")
        pcap_filename = output_name + ".pcap"
        self._start_tcpdump(pcap_filename)

        # run iperf3 client on glomma
        logger.info("Executing iperf3 on client")
        self._start_iperf3_client(self.protocol_host[self.protocol])

        # shutdown tcpdump and iperf3 server
        logger.info("Stopping tcpdump and iperf3...")
        self._shutdown_tasks()

        # export pcap to csv
        logger.info("Exporting pcap data to csv...")
        csv_filename = output_name + ".csv"
        self._pcap_to_csv(pcap_filename, csv_filename)

        # download csv
        logger.info("Downloading csv...")
        self._download_mlcnet_file(f"/home/{self.username}/{csv_filename}",
                                   f"{os.getcwd()}/csv_files/{csv_filename}")
        logger.info(f"File saved to csv_files/{csv_filename}")

        # clear temp files on mlcnet server
        logger.info("Cleaning files on servers...")
        self.mlcnet_ssh.exec_command(f"rm -rf {pcap_filename} {csv_filename}")

        logger.info("Trial done.")

    def run(self):
        self._run_a_trial()

    def get_names(self):
        return self.output_names

    def __del__(self):
        self.mlcnet_client.close()
        self.glomma_ssh.close()
