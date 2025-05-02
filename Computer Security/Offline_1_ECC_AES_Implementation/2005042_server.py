import socket
import pickle
import time
import msvcrt
import os
import random
import logging
from _2005042_aes import aes_cbc_decrypt
from _2005042_elliptic_curve_DH import scalar_mult, point_add

HOST = 'localhost'
PORT = 5000

# Configure logging  ── add force=True so it overrides any prior setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('client_debug.log'),
        logging.StreamHandler()
    ],
    force=True               # <- make basicConfig override earlier handlers
)
# To turn off debug logging, uncomment the following line:
# logging.getLogger().setLevel(logging.INFO)
def is_q_pressed():
    """Check if 'q' key is pressed"""
    if msvcrt.kbhit():
        key = msvcrt.getch()
        return key == b'q' or key == b'Q'
    return False

def handle_client(conn, addr):
    print(f"\nConnected to client at {addr}")
    try:
        # Receive parameters silently
        print("Waiting to receive parameters from client...")
        data = conn.recv(8192)
        a, b, p, G, A = pickle.loads(data)
        print("Received parameters from client")
        print(f"Parameters received: (a, b, p, G, A) = ({a}, {b}, {p}, {G}, {A})")
        # print("Received parameters from client")
        Kb = random.randint(1, p - 1)               # Bob keeps this secret
        B  = scalar_mult(Kb, G, a, p)               # Bob’s public key
        conn.sendall(pickle.dumps(B))               # send *only* B
        print("Sent public key to client")

        # Compute shared key and measure time
        key_start_time = time.time()
        shared_point = scalar_mult(Kb, A, a, p)
        if shared_point is None:
            raise ValueError("Failed to compute shared point")
        # Use 24 bytes for AES-192
        aes_key = shared_point[0].to_bytes(24, 'big')[:24]
        key_time = (time.time() - key_start_time) * 1000
        print(f"[Server] Shared Key Computation Time: {key_time:.3f} ms")
        print(f"[Server] Shared Key (bytes): {aes_key}")
        print(f"[Server] Shared Key (string): {aes_key.decode('ascii', errors='replace')}")
        while True:
            if is_q_pressed():
                print("\n'q' pressed. Shutting down server...")
                return

            # Receive menu choice
            choice_bytes = conn.recv(4)\
            
            if not choice_bytes:
                break
            choice = int.from_bytes(choice_bytes, 'big')
            logging.debug(f"Choice received from client: {choice}")
            if choice == 0:
                # MESSAGE: receive and decrypt
                msg_len = int.from_bytes(conn.recv(4), 'big')
                encrypted_message = b''
                while len(encrypted_message) < msg_len:
                    encrypted_message += conn.recv(min(4096, msg_len - len(encrypted_message)))

                dec_start_time = time.time()
                plaintext = aes_cbc_decrypt(encrypted_message, aes_key)
                dec_time = (time.time() - dec_start_time) * 1000

                print("\n[Server] Decrypted Message:")
                print(plaintext.decode())
                print(f"[Server] Decryption Time: {dec_time:.3f} ms")

            else:
                # FILE: receive file name + encrypted data
                filename_len = int.from_bytes(conn.recv(4), 'big')
                filename = conn.recv(filename_len).decode()

                file_len = int.from_bytes(conn.recv(8), 'big')
                encrypted_file = b''
                remaining      = file_len
                while remaining:
                    packet = conn.recv(min(4096, remaining))
                    if not packet:
                        raise ConnectionError("Connection lost while receiving file")
                    encrypted_file += packet
                    remaining     -= len(packet)


                dec_start_time = time.time()
                decrypted_data = aes_cbc_decrypt(encrypted_file, aes_key)
                dec_time = (time.time() - dec_start_time) * 1000

                save_path = os.path.join('2005042_server_folder', filename)
                with open(save_path, 'wb') as f:
                    f.write(decrypted_data)

                print(f"\n[Server] File received: {filename}")
                print(f"[Server] Saved to: {save_path}")
                print(f"[Server] Decryption Time: {dec_time:.3f} ms")


    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        conn.close()
        print(f"\nClient {addr} disconnected")

def start_server():
    print(f"\nStarting server on {HOST}:{PORT}")
    print("Press 'q' to quit the server")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("\nServer is now listening for connections...")
        
        while True:
            # Check for 'q' key press
            if is_q_pressed():
                print("\n'q' pressed. Shutting down server...")
                break
                
            print("\nWaiting for client to connect...")
            conn, addr = s.accept()
            handle_client(conn, addr)

if __name__ == "__main__":
    start_server()
