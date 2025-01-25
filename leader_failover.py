import socket
import time

DISCOVERY_SERVER = '127.0.0.1'
DISCOVERY_PORT = 5014

server_list = []
leader = None

def get_server_list():
    """
    Holt die aktuelle Serverliste vom Discovery-Server.
    """
    global server_list
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((DISCOVERY_SERVER, DISCOVERY_PORT))
        sock.send("GET_SERVERS".encode())

        response = sock.recv(1024).decode().strip()
        if response.startswith("SERVER_LIST:"):
            server_list = response.replace("SERVER_LIST:", "").split(",")
            server_list = [s.strip() for s in server_list if s.strip() and s != "0.0.0.0"]  # 🚀 Fix: `0.0.0.0` entfernen

        sock.close()
    except Exception as e:
        print(f"[FAILOVER] Fehler beim Abrufen der Serverliste: {e}")

def elect_new_leader():
    """
    Wählt einen neuen Leader, falls der aktuelle nicht mehr erreichbar ist.
    """
    global leader
    get_server_list()
    if server_list:
        leader = min(server_list)
        print(f"[FAILOVER] Neuer Leader ist: {leader}")
    else:
        print("[FAILOVER] Keine verfügbaren Server für Leader-Wahl!")

def start_failover_monitor():
    """
    Startet die Überwachung des Leaders und wählt bei Ausfall automatisch einen neuen.
    """
    get_server_list()
    elect_new_leader()

    while True:
        time.sleep(5)
        elect_new_leader()

if __name__ == "__main__":
    start_failover_monitor()
