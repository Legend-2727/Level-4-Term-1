import socket
import pickle
import time
import random
import sys
from sympy import nextprime, sqrt_mod
from _2005042_aes import aes_cbc_encrypt
from _2005042_elliptic_curve_DH import (
    generate_equation_parameters,
    find_point_on_curve,
    scalar_mult,
    point_add
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

def start_client():
    print(f"\nAttempting to connect to server at {HOST}:{PORT}")
    
    # Connect to server with retry logic
    s = connect_to_server()
    
    try:
        # Generate curve parameters with retry logic
        print("Generating curve parameters...")
        p, a, b, G = generate_curve_parameters()
        
        # Generate private key and compute public key
        Ka = random.randint(1, p-1)
        A = scalar_mult(Ka, G, a, p)

        # Send parameters
        print("Sending parameters to server...")
        data = pickle.dumps((a, b, p, G, A))
        s.sendall(data)
        print("Parameters sent successfully")
        
        # Send private key
        s.sendall(Ka.to_bytes(32, 'big'))
        print("Sent private key to server")
        
        # Receive server's public key
        B = pickle.loads(s.recv(8192))
        print("Received public key from server")

        # Derive shared key and measure time
        key_start_time = time.time()
        shared_point = scalar_mult(Ka, B, a, p)
        if shared_point is None:
            raise ValueError("Failed to compute shared point")
        aes_key = shared_point[0].to_bytes(16, 'big')[:16]
        key_time = (time.time() - key_start_time) * 1000

        while True:
            try:
                message = input("\nEnter your message (or 'quit' to exit): ").encode()
                if message.decode().lower() == 'quit':
                    break

                print("\nKey:")
                print(f"In ASCII: {aes_key.decode('ascii', errors='replace')}")
                print(f"In HEX: {' '.join([f'{b:02x}' for b in aes_key])}")

                print("\nPlain Text:")
                print(f"In ASCII: {message.decode()}")
                print(f"In HEX: {' '.join([f'{b:02x}' for b in message])}")

                # Add padding info
                padded_message = message + (b'\x02' * (16 - (len(message) % 16)))
                print(f"In ASCII (After Padding): {padded_message.decode('ascii', errors='replace')}")
                print(f"In HEX (After Padding): {' '.join([f'{b:02x}' for b in padded_message])}")

                # Encrypt and measure time
                enc_start_time = time.time()
                ciphertext = aes_cbc_encrypt(message, aes_key)
                enc_time = (time.time() - enc_start_time) * 1000

                print("\nCiphered Text:")
                print(f"In HEX: {' '.join([f'{b:02x}' for b in ciphertext])}")
                print(f"In ASCII: {ciphertext.decode('ascii', errors='replace')}")

                # Send the encrypted message
                iv, encrypted = ciphertext[:16], ciphertext[16:]
                s.sendall(iv)
                s.sendall(encrypted)

                print("\nExecution Time Details:")
                print(f"Key Schedule Time: {key_time:.3f} ms")
                print(f"Encryption Time: {enc_time:.3f} ms")

            except Exception as e:
                print(f"Error during message handling: {e}")
                break

    except Exception as e:
        print(f"Error during key exchange: {e}")
    finally:
        s.close()
        print("\nConnection closed.")

if __name__ == "__main__":
    start_client()
