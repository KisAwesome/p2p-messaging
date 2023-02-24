import main
import os
import zono.socket.client


def socket_event_error(e):
    if isinstance(e, zono.socket.client.ConnectionClosed):
        print("The connection has been closed by the host")
        os._exit(0)


socket = main.ChatClient(input(">"), "123")
socket.register_event("event_listiner_error", socket_event_error)
client = socket.parent

addr = ("127.0.0.1", 60061)

try:
    client.connect(addr)
except KeyboardInterrupt:
    pass


socket.wait("on_connect")
nick = socket.server_info["nickname"]
print(f"Connected to {nick} ({addr[0]}:{addr[1]})")
while True:
    try:
        msg = input(">")
    except KeyboardInterrupt:
        socket.close()
        break
    client.send_message(msg)
