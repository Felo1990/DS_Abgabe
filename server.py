import socket
import threading
import time
import random

# Discovery-Server Konfiguration
DISCOVERY_SERVER = '127.0.0.1'
DISCOVERY_PORT = 5014

def get_local_ip():
    return "127.0.0.1"  # 🚀 Fix: Immer `127.0.0.1` verwenden

HOST = get_local_ip()
PORT = random.randint(6000, 7000)

clients = {}  # Speichert verbundene Clients {addr: socket}
client_usernames = {}  # Speichert Namen der Clients

def register_with_discovery():
    """
    Registriert sich beim Discovery-Server mit `127.0.0.1`.
    """
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((DISCOVERY_SERVER, DISCOVERY_PORT))
            register_message = f"REGISTER:{HOST}:{PORT}"
            sock.send(register_message.encode())
            response = sock.recv(1024).decode().strip()
            sock.close()

            if "SERVER_LIST" in response:
                print(f"[LEADER] Erfolgreich registriert beim Discovery-Server mit IP {HOST}. Bestätigte Liste: {response}")
            else:
                print("[LEADER] Keine Bestätigung erhalten, erneuter Versuch...")

            return  
        except Exception as e:
            print(f"[LEADER] Fehler bei der Registrierung: {e}, erneuter Versuch in 5 Sekunden...")
            time.sleep(5)

def broadcast_message(message):
    """
    Sendet eine Nachricht an alle verbundenen Clients.
    """
    disconnected_clients = []
    for addr, sock in clients.items():
        try:
            sock.send(message.encode('utf-8'))
        except Exception:
            print(f"[LEADER] Verbindung zu {addr} verloren. Entferne Client.")
            disconnected_clients.append(addr)

    for addr in disconnected_clients:
        del clients[addr]

def handle_client(client_socket, address):
    """
    Verarbeitet Nachrichten von Clients & sendet sie an alle weiter.
    """
    try:
        clients[address] = client_socket
        username = "Unbekannt"
        print(f"[LEADER] {address} ist verbunden.")

        while True:
            msg = client_socket.recv(1024).decode('utf-8').strip()
            if not msg:
                continue

            if msg.startswith("NAME:"):
                username = msg.split(":", 1)[1].strip()
                client_usernames[address] = username
                print(f"[LEADER] {address} hat sich als {username} angemeldet.")
                client_socket.send(f"WELCOME {username}".encode("utf-8"))
                continue

            if address in client_usernames:
                username = client_usernames[address]

            print(f"[LEADER] Nachricht von {username}: {msg}")
            broadcast_message(f"[CHAT] {username}: {msg}")  # 🚀 Fix: Nachrichten an alle weiterleiten

    except Exception as e:
        print(f"[LEADER] Fehler mit {address}: {e}")
    finally:
        if address in clients:
            del clients[address]
        if address in client_usernames:
            del client_usernames[address]
        client_socket.close()
        print(f"[LEADER] {address} hat die Verbindung getrennt.")

def start_leader_server():
    """
    Startet den Leader-Server & registriert ihn automatisch beim Discovery-Server.
    """
    print(f"[DEBUG] Leader startet mit IP {HOST} auf Port {PORT}")
    register_with_discovery()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[LEADER] Server läuft auf {HOST}:{PORT}")

    while True:
        try:
            client_socket, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_socket, addr)).start()
        except Exception as e:
            print(f"[LEADER] Fehler bei accept(): {e}")

if __name__ == "__main__":
    start_leader_server()
