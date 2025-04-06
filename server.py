import socket, threading, time
from discovery import BROADCAST_PORT, BROADCAST_MSG, build_response_msg

server_id = int(input("Server ID (z. B. 1,2,3...): "))
is_leader = False
leader_id = None
server_ids = [1, 2, 3]  # IDs aller bekannten Server
clients = []

# ========== CLIENT HANDLING ==========

def handle_client(conn, addr):
    print(f"[Client verbunden] {addr}")
    while True:
        try:
            msg = conn.recv(1024).decode()
            if msg:
                print(f"[{addr}] {msg}")
                broadcast_to_clients(msg, conn)
        except:
            break

def broadcast_to_clients(msg, sender):
    for client in clients:
        if client != sender:
            try:
                client.send(msg.encode())
            except:
                pass

def accept_clients():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 6000 + server_id))
    s.listen()
    print(f"[Server {server_id}] wartet auf Clients auf Port {6000 + server_id}")
    while True:
        conn, addr = s.accept()
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# ========== LEADER UDP-ANTWORT ==========

def udp_responder():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('', BROADCAST_PORT))
    except OSError as e:
        print(f"[Server {server_id}] ⚠️ Konnte UDP-Port nicht binden (läuft evtl. schon woanders): {e}")
        return

    while True:
        msg, addr = s.recvfrom(1024)
        if msg == BROADCAST_MSG and is_leader:
            response = build_response_msg(server_id, 6000 + server_id)
            s.sendto(response, addr)

# ========== HEARTBEATS ==========

def heartbeat_sender():
    while True:
        for sid in server_ids:
            if sid == server_id:
                continue
            try:
                s = socket.socket()
                s.settimeout(1)
                s.connect(('127.0.0.1', 5000 + sid))
                s.send(b'PING')
                s.close()
            except:
                continue
        time.sleep(2)

def heartbeat_listener():
    s = socket.socket()
    s.bind(('0.0.0.0', 5000 + server_id))  # Für PING / ELECTION / VICTORY
    s.listen()
    while True:
        conn, _ = s.accept()
        try:
            msg = conn.recv(1024)
            global is_leader, leader_id
            if msg == b'ELECTION':
                start_election()
            elif msg == b'VICTORY':
                is_leader = False
                print(f"[Server {server_id}] 🏳️ Neuer Leader wurde bekanntgegeben.")
            elif msg == b'PING':
                pass
        finally:
            conn.close()

# ========== LEADER CHECK & WAHL ==========

def udp_check_for_leader(timeout=3):
    global leader_id
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.settimeout(timeout)
    try:
        s.sendto(BROADCAST_MSG, ('<broadcast>', BROADCAST_PORT))
        data, addr = s.recvfrom(1024)
        if data.startswith(b"LEADER:"):
            parts = data.decode().split(":")
            found_leader_id = int(parts[1])
            found_leader_port = int(parts[2])
            leader_id = found_leader_id
            print(f"[Server {server_id}] 🛰️ Gefundener Leader: ID {found_leader_id} @ {addr[0]}:{found_leader_port}")
            return True
    except socket.timeout:
        return False

def start_election():
    global is_leader, leader_id
    higher = [sid for sid in server_ids if sid > server_id]
    got_response = False

    for hid in higher:
        try:
            s = socket.socket()
            s.connect(('127.0.0.1', 5000 + hid))
            s.send(b'ELECTION')
            s.close()
            got_response = True
        except:
            continue

    if not got_response:
        is_leader = True
        leader_id = server_id
        print(f"[Server {server_id}] 👑 Ich bin der neue LEADER!")

        for sid in server_ids:
            if sid != server_id:
                try:
                    s = socket.socket()
                    s.connect(('127.0.0.1', 5000 + sid))
                    s.send(b'VICTORY')
                    s.close()
                except:
                    continue

        # ✅ UDP-Responder jetzt hier starten!
        threading.Thread(target=udp_responder, daemon=True).start()
    else:
        print(f"[Server {server_id}] ➤ Höherer Server aktiv. Warte auf Leader.")

# ========== MONITORING DES LEADERS ==========

def monitor_leader():
    global is_leader, leader_id
    while True:
        if not is_leader and leader_id is not None:
            try:
                s = socket.socket()
                s.settimeout(2)
                s.connect(('127.0.0.1', 5000 + leader_id))
                s.send(b'PING')
                s.close()
            except:
                print(f"[Server {server_id}] ⚠️ Leader {leader_id} antwortet nicht – starte Neuwahl...")
                leader_id = None
                start_election()
        time.sleep(5)

# ========== START ==========

if __name__ == "__main__":
    threading.Thread(target=heartbeat_listener, daemon=True).start()
    threading.Thread(target=heartbeat_sender, daemon=True).start()
    threading.Thread(target=accept_clients, daemon=True).start()
    threading.Thread(target=monitor_leader, daemon=True).start()

    time.sleep(1)

    if not udp_check_for_leader():
        start_election()
    else:
        print(f"[Server {server_id}] ✔️ Es existiert bereits ein Leader – keine Wahl nötig.")

    if is_leader:
        threading.Thread(target=udp_responder, daemon=True).start()

    while True:
        time.sleep(1)
