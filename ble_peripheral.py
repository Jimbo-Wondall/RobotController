import bluetooth
import ble_advertising
from micropython import const
import uasyncio as asyncio

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_LED_SERVICE_UUID = bluetooth.UUID(0xA000)
_LED_CHAR = (
    bluetooth.UUID(0xA001),
    bluetooth.FLAG_READ | bluetooth.FLAG_WRITE,
)

_LED_SERVICE = (
    _LED_SERVICE_UUID,
    (_LED_CHAR,),
)

class BLESocket:
    def __init__(self, message_handler, name="Jimbo's Wanderer"):
        self.message_queue = ''
        self.handle_message = message_handler
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle,),) = self._ble.gatts_register_services((_LED_SERVICE,))
        self._connections = set()
        self._payload = ble_advertising.advertising_payload(
            name=name, services=[_LED_SERVICE_UUID]
        )
        self._advertise()
        mac = self._ble.config('mac')
        print("BLE Advertising:", mac)

    def isconnected(self):
        return len(self._connections) > 0

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _, = data
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _, = data
            self._connections.remove(conn_handle)
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle, = data
            data = self._ble.gatts_read(value_handle).decode('utf-8')
            print("Data received:", data)
            if data[-1] is ';':
                data = self.message_queue + data
                self.message_queue = ''
                data = str(data).rstrip(";")
                result = self.handle_message(data)
                result = "None" if result is None else result
                self._ble.gatts_write(value_handle, result.encode('utf-8'))
                print("Command processed: {}\nReturned: {}".format(data, result))
            else:
                self.message_queue = self.message_queue + data
                print('Added segment "{}" to queue\nCurrent queue: {}'.format(data, self.message_queue))

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)