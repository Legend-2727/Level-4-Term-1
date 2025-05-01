import socket
import pickle
import time
from _2005042_aes import aes_cbc_decrypt
from _2005042_elliptic_curve_DH import scalar_mult, point_add

HOST = 'localhost'
PORT = 5000

def start_server():
    print(f"\nStarting server on {HOST}:{PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("\nServer is now listening for connections...")
        print("Waiting for client to connect...")
        conn, addr = s.accept()
        print(f"\nConnected to client at {addr}")

        with conn:
            # Receive parameters silently
            print("Waiting to receive parameters from client...")
            data = conn.recv(8192)
            a, b, p, G, A = pickle.loads(data)
            print("Received parameters from client")
            Kb = int.from_bytes(conn.recv(32), 'big')
            B = scalar_mult(Kb, G, a, p)
            conn.sendall(pickle.dumps(B))
            print("Sent public key to client")

            # Compute shared key and measure time
            key_start_time = time.time()
            shared_point = scalar_mult(Kb, A, a, p)
            if shared_point is None:
                raise ValueError("Failed to compute shared point")
            aes_key = shared_point[0].to_bytes(16, 'big')[:16]
            key_time = (time.time() - key_start_time) * 1000

            while True:
                try:
                    # Receive encrypted message
                    iv = conn.recv(16)
                    if not iv:
                        break
                    ciphertext = conn.recv(8192)

                    # Decrypt and measure time
                    dec_start_time = time.time()
                    plaintext = aes_cbc_decrypt(iv + ciphertext, aes_key)
                    dec_time = (time.time() - dec_start_time) * 1000

                    print("\nDeciphered Text:")
                    print("Before Unpadding:")
                    padded_hex = ' '.join([f'{b:02x}' for b in plaintext])
                    print(f"In HEX: {padded_hex}")
                    print(f"In ASCII: {plaintext.decode()}")

                    # Remove padding
                    unpadded = plaintext.rstrip(b'\x02')
                    print("After Unpadding:")
                    print(f"In ASCII: {unpadded.decode()}")
                    print(f"In HEX: {' '.join([f'{b:02x}' for b in unpadded])}")

                    print("\nExecution Time Details:")
                    print(f"Key Schedule Time: {key_time:.3f} ms")
                    print(f"Decryption Time: {dec_time:.3f} ms")

                except Exception as e:
                    print(f"Error: {e}")
                    break

if __name__ == "__main__":
    start_server()
