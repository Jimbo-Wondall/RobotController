import time

from ws_connection import ClientClosedError
from ws_server import WebSocketServer, WebSocketClient

deadline = time.ticks_add(time.ticks_ms(), 300)

class TestClient(WebSocketClient):
    def __init__(self, conn, message_handle):
        super().__init__(conn)
        self.process_message = message_handle

    def process(self):
        try:
            data = self.connection.read()
            if not data:
                return
            data = data.decode("utf-8")
            #msg = msg.split("\n")[-2]
            #msg = msg.split(" ")
            deadline = time.ticks_add(time.ticks_ms(), 300)
            messages = data.split(";")
            for msg in messages:
                if msg is not "":
                    self.process_message(msg)
            
        except ClientClosedError:
            print("Connection close error")
            self.connection.close()
        except Exception as e:
            print("exception:" + str(e) + "\n")
            raise e
        
class TestServer(WebSocketServer):
    def __init__(self, message_handle):
        super().__init__("index.html", 100)
        self.process_message = message_handle

    def _make_client(self, conn):
        return TestClient(conn, self.process_message)
