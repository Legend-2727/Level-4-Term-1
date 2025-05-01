# ECC and AES Implementation

This project implements a secure client-server communication system using Elliptic Curve Cryptography (ECC) for key exchange and AES for message encryption.

## Features

- Elliptic Curve Cryptography (ECC) for secure key exchange
- AES-128 encryption in CBC mode
- Secure client-server communication
- PKCS#7 padding implementation
- Proper key generation and management

## Implementation Details

- `_2005042_elliptic_curve_DH.py`: ECC implementation for key exchange
- `_2005042_aes.py`: AES-128 implementation in CBC mode
- `2005042_client.py`: Client implementation
- `2005042_server.py`: Server implementation
- `_2005042_bit_vector.py`: Bit manipulation utilities

## Usage

1. Start the server:
```bash
python 2005042_server.py
```

2. Start the client in a separate terminal:
```bash
python 2005042_client.py
```

3. Enter messages in the client terminal to send encrypted messages to the server.

## Security Features

- Secure key exchange using ECC
- AES-128 encryption in CBC mode
- Random IV generation for each message
- Proper padding implementation
- Secure prime number generation

## Author

Farhad Al-Amin (Legend-2727) 