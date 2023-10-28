import json

class NetworkCredential:
    def __init__(self, ssid="", password="", attempts=10, timeout_msec=2000):
        self.ssid = ssid
        self.password = password
        self.attempts = attempts
        self.timeout_msec = timeout_msec

class ServerInfo:
    def __init__(self, ip="", client_port=5000, socket_port=5000, socket_endpoint="", socket_delay_ms=0):
        self.ip = ip
        self.client_port = client_port
        self.socket_port = socket_port
        self.socket_endpoint = socket_endpoint
        self.socket_delay_ms = socket_delay_ms

class Config:
    def __init__(self):
        self.saved_networks = []
        self.server_info = ServerInfo()

    @classmethod
    def from_dict(cls, data):
        config = cls()
        config.saved_networks = [NetworkCredential(**cred) for cred in data.get("saved_networks", [])]
        config.server_info = ServerInfo(**data.get("server_info", {}))
        return config

    def to_dict(self):
        return {
            "saved_credentials": [vars(cred) for cred in self.saved_networks], # type: ignore
            "server_info": vars(self.server_info) # type: ignore
        }

class _ConfigManager:
    def __init__(self, filename='config.json'):
        self.filename = filename
        self.config = Config()
        self.load_config()

    def load_config(self):
        try:
            print("Loading config.")
            with open(self.filename, 'r') as file:
                data = json.load(file)
                print("File loaded: ", data)
                self.config = Config.from_dict(data)
        except OSError:
            print("File error")
            self.reset_config()

    def reset_config(self):
        json_obj = json.loads('''{
            "saved_networks": [{
                "ssid": "Jimbo's Hotspot",
                "password": "753273DCBA",
                "attempts": 10,
                "delay_in_msec": 200
            },
            {
                "ssid": "WiFi-5E80_EXT",
                "password": "753273DCBA",
                "attempts": 10,
                "delay_in_msec": 200
            }],
            "server_info": {
                "ip": "192.168.1.200",
                "client_port": "5001",
                "socket_port": "5000",
                "socket_endpoint": "/pico/",
                "socket_delay_ms": 5
            }
        }''')

        with open(self.filename, 'w') as file:
            json.dump(json_obj, file)


    def save_config(self):
        print("Config saved.")
        with open(self.filename, 'w') as file:
            json.dump(self.config.to_dict(), file)

    def get_network(self, ssid) -> NetworkCredential:
        return [cred for cred in self.config.saved_networks if cred.ssid == ssid][0]

    def remove_credential(self, ssid):
        self.config.saved_networks = [cred for cred in self.config.saved_networks if cred.ssid != ssid]
        self.save_config()

    def add_credential(self, ssid, password, attempts=10, delay_in_msec=200):
        self.config.saved_networks.append(NetworkCredential(ssid, password, attempts, delay_in_msec))
        self.save_config()

    def update_server_info(self, ip=None, client_port=None, socket_port=None, socket_endpoint=None, socket_delay_ms=None):
        if ip:
            self.config.server_info.ip = ip
        if client_port:
            self.config.server_info.client_port = client_port
        if socket_port:
            self.config.server_info.socket_port = socket_port
        if socket_endpoint:
            self.config.server_info.socket_endpoint = socket_endpoint
        if socket_delay_ms:
            self.config.server_info.socket_delay_ms = socket_delay_ms
        self.save_config()

manager_instance = _ConfigManager()

def get_config_manager():
    return manager_instance