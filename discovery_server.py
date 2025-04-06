import socket

# Port für UDP-Broadcast
BROADCAST_PORT = 6000

# Nachricht, die Clients senden, um einen Leader zu finden
BROADCAST_MSG = b"DISCOVER_SERVER"

# Nachricht, die ein Server zurückschickt, wenn er Leader ist
def build_response_msg(server_id, port):
    return f"LEADER:{server_id}:{port}".encode()

# Von Clients aufgerufen: sendet Broadcast und wartet auf Leader-Antwort
def broadcast_discover(timeout=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.settimeout(timeout)
    s.sendto(BROADCAST_MSG, ('<broadcast>', BROADCAST_PORT))

    try:
        data, addr = s.recvfrom(1024)
        if data.startswith(b"LEADER:"):
            parts = data.decode().split(":")
            return addr[0], int(parts[1]), int(parts[2])  # IP, Leader-ID, Port
    except socket.timeout:
        return None, None, None
