import socket
import threading

# Discovery-Server Konfiguration
DISCOVERY_SERVER = '127.0.0.1'
DISCOVERY_PORT = 5014

def get_leader():
    """
    Holt die aktuelle Serverliste und verbindet sich mit dem ersten erreichbaren Leader.
    """
    for _ in range(3):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((DISCOVERY_SERVER, DISCOVERY_PORT))
            sock.send("GET_SERVERS".encode())
            response = sock.recv(1024).decode().strip()
            sock.close()

            if response.startswith("SERVER_LIST:"):
                servers = response.replace("SERVER_LIST:", "").split(",")
                servers = [s.strip() for s in servers if s.strip() and s != "0.0.0.0"]
                if servers:
                    return servers
        except Exception:
            pass
    return None

def receive_messages(sock):
    """
    Hört dauerhaft auf eingehende Nachrichten vom Server und zeigt sie an.
    """
    while True:
        try:
            message = sock.recv(1024).decode('utf-8').strip()
            if message:
                print(message)  # 🚀 Fix: Zeigt empfangene Nachrichten sofort an!
        except Exception:
            print("[CLIENT] Verbindung zum Server verloren.")
            break

def connect_to_leader():
    """
    Verbindet sich mit dem Leader & startet die Chat-Funktion mit automatischem Failover.
    """
    servers = get_leader()
    if not servers:
        print("[CLIENT] Kein Leader verfügbar.")
        return

    try:
        username = input("Gib deinen Namen ein: ").strip()
        if not username:
            username = "Unbekannt"
    except EOFError:
        username = "Client_Unknown"

    for server in servers:
        try:
            leader_ip, leader_port = server.split(":")
            leader_port = int(leader_port)

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((leader_ip, leader_port))
            print(f"[CLIENT] Verbunden mit Leader {leader_ip}:{leader_port}")

            sock.send(f"NAME:{username}".encode('utf-8'))

            # 🚀 Fix: Starte Thread, um Nachrichten dauerhaft zu empfangen!
            threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

            while True:
                msg = input("> ")
                if msg.lower() == "exit":
                    break
                sock.send(f"{msg}".encode('utf-8'))  # 🚀 Fix: Sendet NUR die Nachricht, ohne den Namen doppelt!

            sock.close()
            return  # Erfolgreich verbunden
        except Exception:
            print(f"[CLIENT] Verbindung zu {server} fehlgeschlagen. Versuche den nächsten...")

    print("[CLIENT] Kein verfügbarer Server gefunden.")

if __name__ == "__main__":
    connect_to_leader()
