import main
import socketserver
import atexit


serv = main.ChatHost("localhost", 60061, True, "Kareem", "123")
# serv.event_maneger._debug = True
host = serv.parent

atexit.register(serv.shutdown)
host.start()

if serv.wait("on_start", 1):
    while True:
        try:
            inp = input(">")
        except:
            serv.shutdown()
            break
        if inp.startswith("/"):
            line = inp[1:].split(" ")
            command = line.pop(0)

            if command == "listconnections":
                for i in host.connections:
                    print(i, ":", serv.sessions[i].nickname)

            elif command == "kick":
                f = False
                try:
                    session_number = int(line.pop(0))
                except ValueError:
                    print("Invalid session number must be an integer")
                    continue
                except IndexError:
                    print("You must provide a session number")
                    continue
                for i in host.connections:
                    if i[1] == session_number:
                        n = serv.sessions[i].nickname
                        serv.close_socket(serv.sessions[i].conn, i)
                        print("Kicked", i, ":", n)
                        f = True
                if f is False:
                    print("Session does not exist")

            elif command == "sockets":
                for i in serv.sessions.keys():
                    print(i)

            continue

        host.send_message(inp)
