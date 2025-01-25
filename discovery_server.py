import socket
import threading
import os

HOST = '0.0.0.0'
PORT = 5014

server_list = set()  # Set verwenden, um doppelte Einträge zu vermeiden

print(f"[DISCOVERY] Server startet auf {HOST}:{PORT}")

def handle_client(client_socket, addr):
    """
    Verarbeitet Registrierungsanfragen von Leader-Servern und sendet die aktuelle Serverliste.
    """
    global server_list

    try:
        data = client_socket.recv(1024).decode().strip()
        print(f"[DEBUG] Erhaltene Nachricht von {addr}: {data}")

        if data.startswith("REGISTER:"):
            leader_info = data.replace("REGISTER:", "").strip()

            # 🚀 Fix: `0.0.0.0` wird NICHT gespeichert!
            if leader_info != "0.0.0.0" and leader_info not in server_list:
                server_list.add(leader_info)
                print(f"[DISCOVERY] Neuer Server registriert: {leader_info}")

            response = "SERVER_LIST:" + ",".join(server_list)
            client_socket.send(response.encode())

        elif data == "GET_SERVERS":
            if server_list:
                response = "SERVER_LIST:" + ",".join(server_list)
            else:
                response = "SERVER_LIST:EMPTY"
            
            print(f"[DISCOVERY] Sende Serverliste: {response}")
            client_socket.send(response.encode())

    except Exception as e:
        print(f"[ERROR] Fehler beim Registrieren von {addr}: {e}")
    finally:
        client_socket.close()

def start_discovery_server():
    """
    Startet den Discovery-Server und speichert registrierte Server korrekt.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[DISCOVERY] Server läuft auf {HOST}:{PORT}")

    while True:
        try:
            client_socket, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
        except Exception as e:
            print(f"[ERROR] Fehler bei accept(): {e}")

if __name__ == "__main__":
    start_discovery_server()
