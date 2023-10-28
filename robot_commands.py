from config_manager import get_config_manager

class CommandType:
    CONFIG = 0
    SENSE = 1
    MOVE = 2
    SETMOTOR = 3
    OUTPUT = 4
    CONTROL = 5

class Config:
    UPDATE_SOCKET = 0
    CONNECT_SOCKET = 1
    CONNECT_WIFI = 2
    ADD_WIFI = 3
    CODE_EXEC = 4

class Sense:
    DEPTH = 0
    SCAN = 1
    # TODO add others

class SetMotors:
    ALL = 0
    MOTOR_1 = 1
    MOTOR_2 = 2
    MOTOR_3 = 3
    MOTOR_4 = 4
    LEFT = 5
    RIGHT = 6
    SERVO = 7

class Move:
    FORWARD = 0
    BACK = 1
    FORWARD_LEFT = 2
    FORWARD_RIGHT = 3
    BACK_LEFT = 4
    BACK_RIGHT = 5
    ROTATE_LEFT = 6
    ROTATE_RIGHT = 7
    STOP = 8

class Output:
    NP = 0
    BEEP = 1
    LED_ON = 2
    LED_OFF = 3

class Control:
    MANUAL = 0
    FOLLOW_LIGHT = 1

# CONFIG COMMANDS
class ConfigCommand:
    def execute(self, main):
        pass

class CodeExecuteCommand(ConfigCommand):
    def __init__(self, code):
        self.code = code

    def execute(self, main):
        result = main.execute(self.code)
        return result if result else "Executed with no output."

class ConnectSocketCommand(ConfigCommand):
    def __init__(self, ip, port, endpoint):
        self.ip = ip
        self.port = port
        self.endpoint = endpoint
    def execute(self, main):
        main.comms.web_controller.websocket_close()
        main.comms.web_controller.websocket_handshake(self.ip, self.port, self.endpoint)

class UpdateSocketCommand(ConfigCommand):
    def __init__(self, ip, clientport, socketport, endpoint):
        self.ip = ip
        self.clientport = clientport
        self.socketport = socketport
        self.endpoint = endpoint

    def execute(self, main):
        get_config_manager().update_server_info(self.ip, self.clientport, self.socketport, self.endpoint)

class AddWifiCommand(ConfigCommand):
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password

    def execute(self, main):
        get_config_manager().add_credential(self.ssid, self.password)

class ConnectWifiCommand(ConfigCommand):
    def __init__(self, cred):
        self.cred = cred

    def execute(self, main):
        print("Connect command for: ", self.cred.ssid)
        result = main.comm.connect_wifi(self.cred)
        return "Connection successful." if result else "Failed to connect."
        

# CONTROL COMMANDS
class ControlCommand:
    def execute(self, controller):
        pass

class SetModeCommand(ControlCommand):
    def __init__(self, mode):
        self.mode = mode

    def execute(self, controller):
        controller.control_method = self.mode

# ROBOT COMMANDS
class RobotCommand:
    def execute(self, hw_interface):
        pass

class MoveCommand(RobotCommand):
    def __init__(self, direction, speed=1.0):
        self.direction = direction
        self.speed = speed

    def execute(self, hw_interface):
        hw_interface.move(self.direction, self.speed)

class GetDepthCommand(RobotCommand):
    def execute(self, hw_interface):
        value = hw_interface.get_distance()
        if value is None:
            value = "Error"
        return value

class ScanCommand(RobotCommand):
    def execute(self, hw_interface):
        pass1, pass2 = hw_interface.scan()
        return '''
        {
            "pass1": {},
            "pass2": {}
        }
        '''.format(pass1, pass2)

class SetLedCommand(RobotCommand):
    def __init__(self, state:bool):
        self.state = state

    def execute(self, hw_interface):
        hw_interface.set_led(self.state)

class SetNpCommand(RobotCommand):
    def __init__(self, x, y, z, w):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def execute(self, hw_interface):
        hw_interface.set_np(self.x, self.y, self.z, self.w)

class BeepCommand(RobotCommand):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def execute(self, hw_interface):
        hw_interface.beep(self.x, self.y, self.z)