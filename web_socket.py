import socket
import ubinascii
import os
from config_manager import get_config_manager


# WebSocket opcodes
OP_TEXT = 0x81
OP_CLOSE = 0x88
OP_PING = 0x89
OP_PONG = 0x8A

class WebSocket:
    def __init__(self, message_handle):
        self.handle_message = message_handle
        self.server_info = get_config_manager().config.server_info
        self.sock = socket.socket()
        self.connected = False

    def isconnected(self):
        return self.connected

    def websocket_handshake(self, host, port, path):
        port = int(port)
        print(host, port, path)
        try:
            addr_info = socket.getaddrinfo(host, port)
            addr = addr_info[0][-1]

            sock = socket.socket()
            sock.connect(addr)

            key = ubinascii.b2a_base64(os.urandom(16)).strip()
            request = (
                "GET {} HTTP/1.1\r\n"
                "Host: {}:{}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Key: {}\r\n"
                "Sec-WebSocket-Version: 13\r\n\r\n"
            ).format(path, host, port, key.decode('utf-8'))

            sock.send(request)
            response = sock.recv(1024)
            print("Handshake response: ", response)
            if b"101 Switching Protocols" not in response:
                raise Exception("Handshake failed: {}".format(response))
            self.connected = True
            return sock
        except Exception as e:
            print("Error: ", e)

    async def read_from_socket(self, num_bytes):
        if self.sock is None:
            print("Error: WebSocket connection not established.")
            return None
        buffer = bytearray()
        while num_bytes > 0:
            chunk = self.sock.recv(num_bytes)
            if not chunk:
                raise OSError("Socket connection broken")
            buffer.extend(chunk)
            num_bytes -= len(chunk)
        return buffer

    def websocket_send(self, message):
        if self.sock is None:
            return
        masking_key = os.urandom(4)
        masked_message = bytearray()
        for i, byte in enumerate(message.encode('utf-8')):
            masked_message.append(byte ^ masking_key[i % 4])

        header = bytearray()
        header.append(OP_TEXT)
        message_length = len(message)

        if message_length < 126:
            header.append(message_length | 0x80)
        elif message_length < 65536:
            header.append(126 | 0x80)
            header.extend(message_length.to_bytes(2, byteorder='big'))
        else:
            header.append(127 | 0x80)
            header.extend(message_length.to_bytes(8, byteorder='big'))

        header.extend(masking_key)
        self.sock.send(header + masked_message)

    async def websocket_recv(self):
        if self.sock is None:
            print("Error: WebSocket connection not established.")
            return None

        header = await self.read_from_socket(2)
        opcode, payload_length = header[0], header[1] & 0x7F # type: ignore

        if opcode == OP_CLOSE:
            print("Connection closed by server")
            return None  # Connection closed by peer

        if payload_length == 126:
            extended_payload_length = await self.read_from_socket(2)
            payload_length = int.from_bytes(extended_payload_length, byteorder='big')
        elif payload_length == 127:
            extended_payload_length = await self.read_from_socket(8)
            payload_length = int.from_bytes(extended_payload_length, byteorder='big')

        payload = await self.read_from_socket(payload_length)
        
        if opcode == OP_PING:
            pong_frame = bytearray([OP_PONG])
            # Set the payload length with the masking bit set
            pong_frame.append(payload_length | 0x80)  

            masking_key = os.urandom(4)
            masked_payload = bytearray()
            for i, byte in enumerate(payload): # type: ignore
                masked_payload.append(byte ^ masking_key[i % 4])

            pong_frame.extend(masking_key)
            pong_frame.extend(masked_payload)

            print("Received ping.\nHeader: {}\nPayload: {}\nResponse: {}".format(header, payload, pong_frame))
            self.sock.send(pong_frame)
            return await self.websocket_recv()
        return payload.decode('utf-8') # type: ignore

    def websocket_close(self):
        if self.sock is None:
            print("Error: WebSocket connection not established.")
            return
        self.sock.send(bytes([OP_CLOSE, 0]))
        self.sock.close()
        self.connected = False

    async def run_socket(self):
        try:
            self.sock = self.websocket_handshake(self.server_info.ip, self.server_info.socket_port, self.server_info.socket_endpoint)
            if self.sock:
                print("WebSocket connected")
            else:
                print("WebSocket failed to connect")
                return
            self.websocket_send("Hello from Pico W")
            while True:
                msg = await self.websocket_recv()
                if msg is None:
                    print("WebSocket closed")
                    break
                response = self.handle_message(msg)
                self.websocket_send("Command returned: {}".format(response))
        except Exception as e:
            print("Error:", e)
        finally:
            if self.sock:
                self.websocket_close()
            print("WebSocket closed")