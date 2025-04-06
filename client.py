import socket, threading, time
from discovery import broadcast_discover

current_socket = None
connected = False
name = ""

def receive(sock):
    global connected
    try:
        while True:
            msg = sock.recv(1024).decode()
            if not msg:
                raise Exception("Verbindung verloren.")
            print("\n" + msg)
    except:
        connected = False
        print("[Client] Verbindung verloren – versuche Reconnect...")
        reconnect()

def send_loop(sock):
    global connected
    while True:
        try:
            msg = input()
            sock.send(f"{name}: {msg}".encode())
        except:
            print("[Client] Senden fehlgeschlagen – Verbindung möglicherweise verloren.")
            connected = False
            reconnect()
            break  # Wichtig: Beende aktuelle send_loop

def reconnect():
    global current_socket, connected
    while not connected:
        ip, lid, port = broadcast_discover()
        if ip:
            try:
                s = socket.socket()
                s.connect((ip, port))
                current_socket = s
                connected = True
                print(f"[Client] 🔁 Reconnected zu Leader (ID: {lid}) @ {ip}:{port}")
                threading.Thread(target=receive, args=(s,), daemon=True).start()
                threading.Thread(target=send_loop, args=(s,), daemon=True).start()  # NEU
                return
            except:
                pass
        print("[Client] Reconnect fehlgeschlagen. Neuer Versuch in 3 Sekunden...")
        time.sleep(3)

def main():
    global current_socket, connected, name
    name = input("Dein Name: ")

    ip, lid, port = broadcast_discover()
    if not ip:
        print("❌ Kein Leader gefunden.")
        return

    print(f"[Client] Verbinde zum Leader (ID: {lid}) @ {ip}:{port}")
    try:
        s = socket.socket()
        s.connect((ip, port))
        current_socket = s
        connected = True
        threading.Thread(target=receive, args=(s,), daemon=True).start()
        send_loop(s)
    except:
        print("[Client] Verbindung fehlgeschlagen. Starte Reconnect...")
        reconnect()

if __name__ == "__main__":
    main()
