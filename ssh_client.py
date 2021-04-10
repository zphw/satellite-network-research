import paramiko
from log import logger


# Connect a host (glomma or mlcnets) over the proxy
class SSHClientOverProxy:
    def __init__(self, username, password, proxy_host, host):
        self.username = username
        self.password = password
        self.proxy_host = proxy_host
        self.host = host

        self.proxy_client = paramiko.SSHClient()
        self.client = paramiko.SSHClient()

    def get_client(self):
        logger.debug("Connecting to proxy " + self.proxy_host)

        self.proxy_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.proxy_client.connect(self.proxy_host, 22, self.username, self.password)

        logger.debug("Connected to proxy " + self.proxy_host)

        # get proxy host IP address
        stdin, stdout, stderr = self.proxy_client.exec_command("hostname -I")
        proxy_host_addr = stdout.readlines()[0].replace("\n", "")

        # get destination host IP address
        stdin, stdout, stderr = self.proxy_client.exec_command("resolveip -s " + self.host)
        host_addr = stdout.readlines()[0].replace("\n", "")

        # logger.debug("Proxy host address: " + proxy_host_addr)
        # logger.debug("Dest. host address: " + host_addr)

        transport = self.proxy_client.get_transport()
        dest_addr = (host_addr, 22)
        local_addr = (proxy_host_addr, 22)
        channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)

        logger.debug("Connecting to " + self.host)

        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.host, 22, self.username, self.password, sock=channel)

        logger.debug("Connected to " + self.host)
        return self.client

    def close(self):
        self.client.close()
        self.proxy_client.close()
