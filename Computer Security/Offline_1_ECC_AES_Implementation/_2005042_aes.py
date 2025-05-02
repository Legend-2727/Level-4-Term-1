import secrets, time
import logging
from BitVector import BitVector

from _2005042_bit_vector import Sbox, InvSbox, Mixer, InvMixer

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Set to WARNING to disable most output
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Disable all logging
# logger.setLevel(logging.ERROR)

AES_MOD = BitVector(bitstring='100011011')
def bytes2matrix(block: bytes) -> list:
    """
    Convert a 16-byte block into a 4x4 matrix in column-major format.
    """
    matrix = []  # This will be a list of 4 columns

    # Go through 0, 4, 8, 12 → 4 columns
    for i in range(0, 16, 4):
        column = []  # each column will be a list of 4 values
        column.append(block[i])
        column.append(block[i + 1])
        column.append(block[i + 2])
        column.append(block[i + 3])
        matrix.append(column)

    return matrix

def matrix2bytes(matrix: list) -> bytes:
    """
    Convert a 4x4 matrix back to a 16-byte block.
    """
    result = []

    for col in matrix:
        result.append(col[0])
        result.append(col[1])
        result.append(col[2])
        result.append(col[3])

    return bytes(result)

def sub_bytes(state: list) -> None:
    """
    Apply the AES SubBytes step on the state matrix.
    Each byte is replaced using the S-box.
    """
    for col in range(4):
        for row in range(4):
            byte_value = state[col][row]
            substituted = Sbox[byte_value]   # look up in the S-box
            state[col][row] = substituted    # replace with new byte

def shift_rows(state: list) -> None:
    """
    Shift the rows of the state matrix to the left.
    """
    for row in range(4):
        temp = [state[0][row], state[1][row], state[2][row], state[3][row]]
        for col in range(4):
            state[col][row] = temp[(col + row) % 4]

def mix_single_column(column: list) -> list:
    """
    Mix one 4-byte column using GF(2⁸) multiplication and the AES matrix.
    Input: list of 4 integers
    Output: new list of 4 mixed integers
    """
    mixed = [0, 0, 0, 0]

    # Convert input bytes to BitVectors
    b = [BitVector(intVal=val, size=8) for val in column]

    # Multiply with Mixer matrix
    for row in range(4):
        temp = BitVector(intVal=0, size=8)
        for col in range(4):
            product = Mixer[row][col].gf_multiply_modular(b[col], AES_MOD, 8)
            temp ^= product  # XOR result
        mixed[row] = int(temp)  # Convert back to int

    return mixed

def mix_columns(state: list) -> None:
    """
    Mix the columns of the state matrix using the AES matrix.
    """
    for col in range(4):
        state[col] = mix_single_column(state[col])
        
def add_round_key(state: list, key: list) -> None:
    """
    Add the round key to the state matrix.
    """
    for col in range(4):
        for row in range(4):
            state[col][row] ^= key[col][row]
            
def encrypt_block(plaintext: bytes, round_keys: list) -> bytes:
    """
    Encrypt a single 16-byte block using AES-128 and 11 round keys.
    """
    state = bytes2matrix(plaintext)

    # Initial round (round 0)
    add_round_key(state, round_keys[0])

    # Rounds 1 to 9
    for round in range(1, 10):
        sub_bytes(state)
        shift_rows(state)
        mix_columns(state)
        add_round_key(state, round_keys[round])

    # Final round (round 10)
    sub_bytes(state)
    shift_rows(state)
    add_round_key(state, round_keys[10])

    return matrix2bytes(state)

RCON = [0x01, 0x02, 0x04, 0x08, 0x10,
        0x20, 0x40, 0x80, 0x1B, 0x36]

def key_expansion(key: bytes) -> list:
    """
    Expand 16-byte AES key into 11 round keys (each a 4×4 matrix).
    """
    # Step 1: Initial 4 words from the key
    key_columns = bytes2matrix(key)  # 4 columns of 4 bytes each
    logger.debug(f"Initial key columns: {key_columns}")

    # Step 2: Expand to 44 words (4 words per round × 11 rounds)
    i = 0
    while len(key_columns) < 44:
        word = key_columns[-1][:]  # copy last word
        logger.debug(f"word: {word}")
        if len(key_columns) % 4 == 0:
            # Rotate left
            word = word[1:] + word[:1]
            # SubBytes
            word = [Sbox[b] for b in word]
            # XOR with RCON
            word[0] ^= RCON[i]
            i += 1

        # XOR with word 4 positions back
        prev_word = key_columns[-4]
        word = [b1 ^ b2 for b1, b2 in zip(word, prev_word)]

        key_columns.append(word)

    # Step 3: Group 4 words = 1 round key matrix
    round_keys = [key_columns[i:i+4] for i in range(0, 44, 4)]
    return round_keys

def pkcs7_pad(data: bytes, block_size=16) -> bytes:
    pad_len = block_size - len(data) % block_size
    return data + bytes([pad_len] * pad_len)

def aes_cbc_encrypt(plaintext: bytes, key: bytes) -> bytes:
    """
    Encrypt any length plaintext using AES-128 in CBC mode.
    Returns: IV + ciphertext
    """
    logger.debug(f"Plaintext bytes: {list(plaintext)}")
    logger.debug(f"Key bytes: {list(key)}")
    logger.debug(f"Plaintext length: {len(plaintext)}, Key length: {len(key)}")
    
    round_keys = key_expansion(key)
    logger.debug(f"Number of round keys: {len(round_keys)}")
    logger.debug(f"First round key: {round_keys[0]}")
    logger.debug(f"Second round key: {round_keys[1]}")
    
    plaintext = pkcs7_pad(plaintext)
    iv = secrets.token_bytes(16)

    ciphertext = b""
    prev = iv

    for i in range(0, len(plaintext), 16):
        block = plaintext[i:i+16]
        block_xored = bytes([a ^ b for a, b in zip(block, prev)])
        enc_block = encrypt_block(block_xored, round_keys)
        ciphertext += enc_block
        prev = enc_block

    return iv + ciphertext

def inv_sub_bytes(state):
    for col in range(4):
        for row in range(4):
            state[col][row] = InvSbox[state[col][row]]

def inv_shift_rows(state):  
    for row in range(4):
        temp = [state[0][row], state[1][row], state[2][row], state[3][row]]
        for col in range(4):
            state[col][row] = temp[(col - row) % 4]

def inv_mix_columns(state):
    for col in range(4):
        state[col] = inv_mix_single_column(state[col])

def inv_mix_single_column(column):
    mixed = [0, 0, 0, 0]
    b = [BitVector(intVal=val, size=8) for val in column]
    for row in range(4):
        temp = BitVector(intVal=0, size=8)
        for col in range(4):
            product = InvMixer[row][col].gf_multiply_modular(b[col], AES_MOD, 8)
            temp ^= product
        mixed[row] = int(temp)
    return mixed

def pkcs7_unpad(padded: bytes) -> bytes:
    pad_len = padded[-1]
    if pad_len < 1 or pad_len > 16:
        raise ValueError("Invalid padding length.")
    if padded[-pad_len:] != bytes([pad_len] * pad_len):
        raise ValueError("Invalid PKCS#7 padding.")
    return padded[:-pad_len]


def decrypt_block(cipher_block: bytes, round_keys: list) -> bytes:
    """
    Decrypt a single 16-byte AES block using the 11 round keys.
    """
    state = bytes2matrix(cipher_block)

    # Initial round: add final round key
    add_round_key(state, round_keys[10])
    inv_shift_rows(state)
    inv_sub_bytes(state)

    # Rounds 9 to 1
    for round in range(9, 0, -1):
        add_round_key(state, round_keys[round])
        inv_mix_columns(state)
        inv_shift_rows(state)
        inv_sub_bytes(state)

    # Final round: add initial round key
    add_round_key(state, round_keys[0])

    return matrix2bytes(state)

def aes_cbc_decrypt(ciphertext: bytes, key: bytes) -> bytes:
    """
    Decrypts AES-CBC encrypted data (expects IV + ciphertext).
    Returns: original plaintext
    """
    round_keys = key_expansion(key)
    iv = ciphertext[:16]
    ciphertext = ciphertext[16:]

    prev = iv
    plaintext = b""

    for i in range(0, len(ciphertext), 16):
        block = ciphertext[i:i+16]
        decrypted = decrypt_block(block, round_keys)
        xored = bytes([a ^ b for a, b in zip(decrypted, prev)])
        plaintext += xored
        prev = block

    return pkcs7_unpad(plaintext)


# if __name__ == "__main__":
#     key = b'Thats my Kung Fu'
#     message = b"Hello AES CBC mode test!!"

#     ciphertext = aes_cbc_encrypt(message, key)
#     print("Encrypted (hex):", ciphertext.hex())

#     decrypted = aes_cbc_decrypt(ciphertext, key)
#     print("Decrypted text:", decrypted)
