import ble_peripheral
#import web_socket
from config_manager import NetworkCredential, get_config_manager
import uasyncio as a
import usocket
import time
import json
import webserver
import network as net
from robot_commands import *

class CommunicationManager:
    def __init__(self, main, controller):
        self.deadline = time.ticks_add(time.ticks_ms(), 300)
        self.server = webserver.TestServer(self.handle_message)
        self.main = main
        self.controller = controller
        self.config = get_config_manager()
        self.saved_networks = self.config.config.saved_networks
        self.wifi = net.WLAN(net.STA_IF)
        self.auto_connect_wifi()
        self.server.start()
        self.blesocket = ble_peripheral.BLESocket(self.handle_message)
        #self.web_controller = web_socket.WebSocket(self.handle_message)
    
    def auto_connect_wifi(self):
        print("Auto connecting...")
        for cred in self.saved_networks:
            a.run(self.connect_wifi(cred))
            if self.wifi.isconnected():
                return
        print("Auto connect failed.")

    async def connect_wifi(self, creds: NetworkCredential):
        print('Trying network "{}"'.format(creds.ssid))
        
        if self.wifi.isconnected():
            self.wifi.disconnect()
            self.wifi.active(False)
            self.wifi.deinit()

        self.wifi = net.WLAN(net.STA_IF)
        self.wifi.active(True)
        attempts = creds.attempts
    
        while not self.wifi.isconnected() and attempts > 0:
            try:
                print("Attempt {}/{}".format(creds.attempts - attempts + 1, creds.attempts))
                self.wifi.connect(creds.ssid, creds.password)
                start_time = time.ticks_ms()
                while self.wifi.status() == net.STAT_CONNECTING and a.ticks_diff(time.ticks_ms(), start_time) < creds.timeout_msec:
                    await a.sleep_ms(100)
                start_time = time.ticks_ms()
                while self.wifi.status() == 2 and a.ticks_diff(time.ticks_ms(), start_time) < 20000:
                    await a.sleep_ms(100)
                print("Attempt failed", self.wifi.status())
            except Exception as e:
                print("Error connecting to {}: {}".format(creds.ssid, e))
            attempts -= 1
    
        if self.wifi.isconnected():
            print("Connected to {}".format(creds.ssid))
            print("ifconfig: {}".format(self.wifi.ifconfig()))
            self.controller.execute_command(SetLedCommand(True))
            return True
        else:
            self.controller.execute_command(SetLedCommand(False))
            print("Couldn't connect to {}".format(creds.ssid))
            return False

    def ping(self, host, port):
        try:
            sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
            sock.connect((host, port))
            sock.send("test")
        except Exception as e:
            print("Unable to connect to {}:{} - {}".format(host, port, e))
            return False
        else:
            print("Successfully connected to: {}:{}".format(host, port))
            sock.close()
            return True

    def handle_message(self, data):
        print("Message Received:", data)
        command_type, command, args = self.parse_command(data)
        cmd = CommandFactory().create(command_type, command, args)
        if cmd:
            if isinstance(cmd, ConfigCommand):
                return str(self.main.execute_command(cmd))
            else:
                return str(self.controller.execute_command(cmd))
        return "Command creation failed."

    def parse_command(self, data):
        # 2:0:
        # MOVE:FORWARD:
        command_type, separator, remainder = data.partition(':')
        command, separator, args = remainder.partition(':')
        try:
            args = json.loads(args)
        except:
            args = None
        return int(command_type), int(command), args
    
    async def run(self):
        self.server.process_all()
        if time.ticks_diff(self.deadline, time.ticks_ms()) < 0:
            self.deadline = time.ticks_add(time.ticks_ms(), 100000)

class CommandFactory:
    def create(self, command_type, command, args):
        print("Creating command from:\ncommand_type: {}\ncommand: {}\nargs: {}".format(command_type, command, args))
        if command_type == CommandType.CONFIG:
            if args:
                if command == Config.UPDATE_SOCKET:
                    return UpdateSocketCommand(args['ip'], args['clientport'], args['socketport'], args['endpoint'])
                elif command == Config.CONNECT_SOCKET:
                    return ConnectSocketCommand(args['ip'], args['port'], args['endpoint'])
                elif command == Config.ADD_WIFI:
                    return AddWifiCommand(args['ssid'], args['password'])
                elif command == Config.CONNECT_WIFI:
                    creds = get_config_manager().get_network(args['ssid'])
                    if creds:
                        return ConnectWifiCommand(creds)
                    else:
                        print('No network found for "{}"'.format(args['ssid']))
                elif command == Config.CODE_EXEC:
                    return CodeExecuteCommand(args['code'])
        
        elif command_type == CommandType.MOVE:
            direction = self.to_string(command_type, command)[1].lower()
            if direction is not 'unknown':
                speed = 1.0
                if args and 'speed' in args:
                    speed = int(args['speed'])
                return MoveCommand(direction, speed)
        
        elif command_type == CommandType.SENSE:
            if command == Sense.DEPTH:
                return GetDepthCommand()
            elif command == Sense.SCAN:
                return ScanCommand()
        
        elif command_type == CommandType.OUTPUT:
            if command == Output.LED_ON:
                return SetLedCommand(True)
            elif command == Output.LED_OFF:
                return SetLedCommand(False)
            if args:
                if command == Output.NP:
                    return SetNpCommand(int(args['r']), int(args['g']), int(args['b']), int(args['duration']))
                elif command == Output.BEEP:
                    return BeepCommand(int(args['frequency']), int(args['duration']), int(args['volume']))
        
        elif command_type == CommandType.CONTROL:
            if command == Control.MANUAL:
                return SetModeCommand('MANUAL')
            elif command == Control.FOLLOW_LIGHT:
                return SetModeCommand('FOLLOW_LIGHT')
        return None
    
    def to_string(self, command_type, command):
        if command_type == CommandType.MOVE:
            if command == Move.FORWARD:
                return "MOVE", "FORWARD"
            elif command == Move.BACK:
                return "MOVE", "BACK"
            elif command == Move.FORWARD_LEFT:
                return "MOVE", "FORWARD_LEFT"
            elif command == Move.FORWARD_RIGHT:
                return "MOVE", "FORWARD_RIGHT"
            elif command == Move.BACK_LEFT:
                return "MOVE", "BACK_LEFT"
            elif command == Move.BACK_RIGHT:
                return "MOVE", "BACK_RIGHT"
            elif command == Move.ROTATE_LEFT:
                return "MOVE", "ROTATE_LEFT"
            elif command == Move.ROTATE_RIGHT:
                return "MOVE", "ROTATE_RIGHT"
            elif command == Move.STOP:
                return "MOVE", "STOP"
        elif command_type == CommandType.SENSE:
            if command == Sense.SCAN:
                return "SENSE", "SCAN"
        elif command_type == CommandType.OUTPUT:
            if command == Output.LED_ON:
                return "OUTPUT", "LED_ON"
            elif command == Output.LED_OFF:
                return "OUTPUT", "LED_OFF"
            elif command == Output.NP:
                return "OUTPUT", "NP"
            elif command == Output.BEEP:
                return "OUTPUT", "BEEP"
        elif command_type == CommandType.CONTROL:
            if command == Control.MANUAL:
                return "CONTROL", "MANUAL"
            elif command == Control.FOLLOW_LIGHT:
                return "CONTROL", "FOLLOW_LIGHT"
        return "UNKNOWN", "UNKNOWN"