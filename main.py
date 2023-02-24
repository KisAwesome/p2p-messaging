from zono.events import event
import zono.socket.server
import zono.socket.client
import threading
import zono.colorlogger

request = zono.socket.server.request


def format_message(message):
    sender = message["sender"]
    nick = sender["nickname"]
    ip = sender["ip"]
    message = message["message"]
    return f"{nick} ({ip}): {message}"


class ChatClient(zono.socket.client.Client):
    def __init__(self, nickname, password):
        self.nickname = nickname
        self.password = password

    @event()
    def client_info(self):
        return dict(nickname=self.nickname, password=self.password)

    @event()
    def socket_event(self, event):
        if event["event"] == "new_message":
            print(format_message(event))
        elif event["event"] == "join":
            nick = event["nickname"]
            ip = event["ip"]
            zono.colorlogger.major_log(f"{nick} ({ip}) has connected")
        elif event["event"] == "leave":
            nick = event["nickname"]
            ip = event["ip"]
            zono.colorlogger.major_log(f"{nick} ({ip}) has disconnected")

    def send_message(self, message):
        self.send(dict(path="message", message=message))

    def connect(self, addr):
        self.thread = threading.Thread(target=self.connect, args=(addr,))
        self.thread.start()


class ChatHost(zono.socket.server.Server):
    def __init__(self, nickname, password):
        self.password = password
        self.nickname = nickname
        self.server.load_loggers()
        self.connections = []

    @event()
    def server_info(self):
        return dict(nickname=self.nickname)

    @event()
    def client_info(self, info):
        if self.password:
            if info.get("password", None) != self.password:
                return False
        self.server.sessions[info["addr"]]["nickname"] = (
            info.get("nickname", None) or "Unknown"
        )
        return True

    @request("message")
    def message_received(self, ctx):
        msg = ctx.pkt.get("message", None)
        if msg is None:
            return
        message = dict(
            sender=dict(ip=ctx.addr[0], nickname=ctx.session.nickname),
            message=msg,
            event="new_message",
        )

        print(format_message(message))
        for i in self.server.sessions.keys():
            if self.server.is_event_socket(i):
                continue
            self.send_event(i, message)

    @event()
    def on_session_close(self, ctx):
        if self.server.is_event_socket(ctx.addr):
            return

        if ctx.addr in self.connections:
            self.connections.remove(ctx.addr)
        message = dict(event="leave", ip=ctx.addr[0], nickname=ctx.session.nickname)
        for i in self.connections:
            if self.server.get_session(i) is None:
                continue
            self.send_event(i, message)

    @event()
    def event_socket_registered(self, ctx):
        if self.server.is_event_socket(ctx.parent_addr):
            return
        self.connections.append(ctx.parent_addr)
        message = dict(
            event="join", ip=ctx.parent_addr[0], nickname=ctx.client_session.nickname
        )
        for i in self.server.sessions.keys():
            if i == ctx.parent_addr or self.server.is_event_socket(i):
                continue

            self.send_event(i, message)

    def send_message(self, msg):
        message = dict(
            sender=dict(ip=self.server.ip, nickname=self.nickname),
            message=msg,
            event="new_message",
        )

        for i in self.server.sessions.keys():
            if self.server.is_event_socket(i):
                continue
            self.send_event(i, message)

    def start(self):
        self.thread = threading.Thread(target=self.server.run)
        self.thread.start()
