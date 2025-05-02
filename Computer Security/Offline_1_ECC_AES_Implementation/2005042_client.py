import socket
import pickle
import time
import random
import os
import sys
import logging
from sympy import nextprime, sqrt_mod
from _2005042_aes import aes_cbc_encrypt
from _2005042_elliptic_curve_DH import (
    generate_equation_parameters,
    find_point_on_curve,
    scalar_mult,
    point_add
)

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

HOST = 'localhost'
PORT = 5000
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def generate_prime(bits=128):
    while True:
        p = random.getrandbits(bits) | 1
        prime = int(nextprime(p))
        if prime.bit_length() == bits:
            return prime

def generate_curve_parameters(max_attempts=3):
    """Generate valid curve parameters with retry logic"""
    for attempt in range(max_attempts):
        try:
            p = generate_prime(128)
            a = random.randint(1, p-1)
            b = random.randint(1, p-1)
            if (4 * pow(a, 3, p) + 27 * pow(b, 2, p)) % p == 0:
                continue
            G = find_point_on_curve(p, a, b)
            if G is not None:
                return p, a, b, G
        except ValueError:
            if attempt < max_attempts - 1:
                print(f"Failed to generate curve parameters, attempt {attempt + 1}/{max_attempts}")
                time.sleep(1)
                continue
            raise
    raise ValueError("Failed to generate valid curve parameters after multiple attempts")

def connect_to_server():
    """Attempt to connect to server with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)  # Set a timeout for connection attempts
            s.connect((HOST, PORT))
            print("Successfully connected to server!")
            return s
        except ConnectionRefusedError:
            if attempt < MAX_RETRIES - 1:
                print(f"Connection refused, retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                print("Error: Could not connect to server after multiple attempts. Make sure the server is running.")
                sys.exit(1)
        except Exception as e:
            print(f"Error connecting to server: {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                sys.exit(1)

def client_menu(aes_key, conn):
    files = os.listdir('2005042_client_folder')
    print("\nAvailable files:")
    print("0. Send a message")
    for idx, filename in enumerate(files, start=1):
        print(f"{idx}.{filename}")

    choice = int(input("Enter your choice: "))

    # Send choice to server
    logging.debug(f"Choice: {choice}")
    conn.sendall(choice.to_bytes(4, 'big'))
    logging.debug(f"Choice sent to server: {choice}")
    if choice == 0:
        # Send a text message
        message = input("Enter your message: ").encode()
        encrypted_message = aes_cbc_encrypt(message, aes_key)
        msg_len = len(encrypted_message).to_bytes(4, 'big')
        conn.sendall(msg_len)
        conn.sendall(encrypted_message)
        print("[Client] Message sent successfully.")
        return True
    elif 1 <= choice <= len(files):
        # Send selected file
        filename = files[choice - 1]
        filepath = os.path.join('2005042_client_folder', filename)
        logging.debug(f"Sending file: {filepath}")
        logging.debug(f"File size: {os.path.getsize(filepath)} bytes")
        with open(filepath, 'rb') as f:
            file_data = f.read()
        # logging.debug(f"File data: {file_data}")
        encrypted_file = aes_cbc_encrypt(file_data, aes_key)
        preview = file_data[:64]          # first 64 bytes only
        logging.debug(f"File data (64 B preview): {preview.hex()} ...")

        enc_preview = encrypted_file[:64]
        logging.debug(f"Encrypted file (64 B preview): {enc_preview.hex()} ...")
        # Send filename first
        filename_bytes = filename.encode()
        filename_len = len(filename_bytes).to_bytes(4, 'big')
        conn.sendall(filename_len)
        conn.sendall(filename_bytes)
        
        # Send encrypted file data length and data
        file_len = len(encrypted_file).to_bytes(8, 'big')
        conn.sendall(file_len)
        conn.sendall(encrypted_file)
        
        print(f"[Client] File '{filename}' sent successfully.")
        return True
    else:
        print("[Client] Invalid choice. Exiting.")
        return False


def start_client():
    print(f"\nAttempting to connect to server at {HOST}:{PORT}")
    
    # Connect to server with retry logic
    s = connect_to_server()
    
    try:
        # Generate curve parameters with retry logic
        print("Generating curve parameters...")
        p, a, b, G = generate_curve_parameters()
        
        # Generate private key and compute public key
        Ka = random.randint(1, p - 1)
        A = scalar_mult(Ka, G, a, p)

        # Send parameters
        print(f"Sending parameters to server: (a, b, p, G, A) = ({a}, {b}, {p}, {G}, {A})")
        data = pickle.dumps((a, b, p, G, A))
        s.sendall(data)
        print("Parameters sent successfully")
        
        # Send private key (for simulation purposes)
        # s.sendall(Ka.to_bytes(32, 'big'))
        # print("Sent private key to server")
        
        # Receive server's public key
        B = pickle.loads(s.recv(8192))
        print(f"Received public key from server: B = {B}")

        # Derive shared AES key
        key_start_time = time.time()
        shared_point = scalar_mult(Ka, B, a, p)
        if shared_point is None:
            raise ValueError("Failed to compute shared point")
        aes_key = shared_point[0].to_bytes(16, 'big')[:16]
        key_time = (time.time() - key_start_time) * 1000
        print(f"[Server] Shared Key (bytes): {aes_key}")
        print(f"[Server] Shared Key (string): {aes_key.decode('ascii', errors='replace')}")
        print(f"[Client] Shared key derived in {key_time:.3f} ms")
        
        # Show user menu: send message or file
        while True:
            if not client_menu(aes_key, s):
                break


    except Exception as e:
        print(f"Error during client execution: {e}")
    finally:
        s.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    start_client()
