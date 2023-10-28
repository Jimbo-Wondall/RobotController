import robot_controller
import hardware_interface
import uasyncio as a
import communication_manager

class MainLogic:
    def __init__(self):
        self.hw_interface = hardware_interface.HardwareInterface()
        self.controller = robot_controller.RobotController(self.hw_interface)
        self.comms = communication_manager.CommunicationManager(self, self.controller)
    
    def execute(self, data):
        try:
            print("Executing: ", data)
            self_ref = { }
            self_ref['self'] = self
            return exec(data, self_ref)
        except Exception as e:
            print(e)
            return False
    
    def execute_command(self, command):
        if isinstance(command, robot_controller.ConfigCommand):
            return command.execute(self)
        return None
    
    def write_to_file(self, filename, data):
        with open(filename, 'w') as file:
            file.write(data)

    def read_from_file(self, filename):
        with open(filename, 'r') as file:
            return file.read()

    async def run(self):
        self.controller.run()
        await self.comms.run()

robot_ctrlr = MainLogic()
while True:
    a.run(robot_ctrlr.run())