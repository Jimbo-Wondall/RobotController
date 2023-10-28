from hardware_interface import HardwareInterface
from robot_commands import *
LIGHT_THRESHOLD = 30000

class RobotController:
    def __init__(self, robot:HardwareInterface):
        self.control_method = "MANUAL"
        self.is_running = False
        self.robot = robot

    def execute_command(self, command):
        if isinstance(command, RobotCommand):
            if self.control_method is "MANUAL":
                return command.execute(self.robot)
        elif isinstance(command, ControlCommand):
            return command.execute(self)
        return "Invalid command type at RobotController"
    
    def stop(self):
        self.is_running = False

    def follow_light(self):
        left_intensity = self.robot.get_left_light_intensity()
        right_intensity = self.robot.get_right_light_intensity()

        if left_intensity > LIGHT_THRESHOLD and right_intensity > LIGHT_THRESHOLD:
            self.robot.motor_control.forward()
        elif left_intensity > LIGHT_THRESHOLD:
            self.robot.motor_control.forward_left()
        elif right_intensity > LIGHT_THRESHOLD:
            self.robot.motor_control.forward_right()
        else:
            self.robot.motor_control.stop()

    def run(self):
        if self.is_running and not self.control_method is "MANUAL":
            if self.control_method == "FOLLOW_LIGHT":
                self.follow_light()