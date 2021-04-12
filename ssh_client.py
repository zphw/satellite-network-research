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
        self.proxy_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def get_client(self):
        logger.debug("Connecting to proxy " + self.proxy_host)

        self.proxy_client.connect(self.proxy_host, 22, self.username, self.password)

        logger.debug("Connected to proxy " + self.proxy_host)

        transport = self.proxy_client.get_transport()
        channel = transport.open_channel("direct-tcpip",
                                         dest_addr=(self.host, 22),
                                         src_addr=("", 0))

        logger.debug("Connecting to " + self.host)

        self.client.connect(self.host, 22, self.username, self.password, sock=channel)

        logger.debug("Connected to " + self.host)
        return self.client

    def close(self):
        self.client.close()
        self.proxy_client.close()
