import socket, threading

# Test server for Hydra
# Correct password: TestPass123!
VALID_PASSWORDS = ["TestPass123!", "letmein123"]
HOST = "127.0.0.1"
PORT = 2222

def handle_client(conn, addr):
    try:
        conn.sendall(b"Test Login Service v1.0\r\n")
        conn.sendall(b"User: testuser\r\n")
        conn.sendall(b"Password: ")
        data = conn.recv(1024)
        if data:
            pwd = data.decode().strip()
            if pwd in VALID_PASSWORDS:
                conn.sendall(b"\r\nLogin successful!\r\n")
            else:
                conn.sendall(b"\r\nLogin incorrect\r\n")
        conn.close()
    except:
        pass

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"Test server listening on {HOST}:{PORT}")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
