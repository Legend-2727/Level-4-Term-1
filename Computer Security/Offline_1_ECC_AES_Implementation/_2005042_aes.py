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
    if len(block) != 16:
        raise ValueError("AES block size must be exactly 16 bytes")

    return [[block[r + 4 * c] for r in range(4)] for c in range(4)]

def key2matrix(key: bytes) -> list:
    """
    Convert a key (16/24/32 bytes) into a list of 4-byte columns.
    """
    key_len = len(key)
    if key_len not in (16, 24, 32):
        raise ValueError("Key must be 16, 24, or 32 bytes")
    
    return [[key[r + 4 * c] for r in range(4)] for c in range(key_len // 4)]

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
    Encrypt a single block using AES.
    Supports 128/192/256-bit keys based on round_keys length.
    """
    state = bytes2matrix(plaintext)
    Nr = len(round_keys) - 1  # Number of rounds based on key size

    # Initial round
    add_round_key(state, round_keys[0])

    # Main rounds
    for rnd in range(1, Nr):
        sub_bytes(state)
        shift_rows(state)
        mix_columns(state)
        add_round_key(state, round_keys[rnd])

    # Final round (no MixColumns)
    sub_bytes(state)
    shift_rows(state)
    add_round_key(state, round_keys[-1])
    return matrix2bytes(state)

RCON = [0x01, 0x02, 0x04, 0x08, 0x10,
        0x20, 0x40, 0x80, 0x1B, 0x36]

def key_expansion(key: bytes) -> list:
    """
    Expand an AES key (16/24/32 bytes) into the full round-key schedule.
    Returns a list of (4×4) column-major matrices, one per round.
    """
    key_len = len(key)
    if key_len not in (16, 24, 32):
        raise ValueError("Key must be 16, 24, or 32 bytes")

    # Nb is always 4; look-up Nk and Nr for the key size
    NB = 4
    NK_NR = {16: (4, 10), 24: (6, 12), 32: (8, 14)}  # (Nk, Nr) pairs
    Nk, Nr = NK_NR[key_len]

    # Convert key to matrix format
    key_columns = key2matrix(key)  # Use key2matrix instead of bytes2matrix
    i = 0  # Rcon counter

    # Generate round keys
    total_words = NB * (Nr + 1)
    while len(key_columns) < total_words:
        word = key_columns[-1].copy()

        # For every Nk words
        if len(key_columns) % Nk == 0:
            # RotWord
            word = word[1:] + word[:1]
            # SubWord
            word = [Sbox[b] for b in word]
            # XOR with Rcon
            word[0] ^= RCON[i]
            i += 1
        # Special case for 256-bit keys
        elif Nk == 8 and len(key_columns) % Nk == 4:
            word = [Sbox[b] for b in word]

        # XOR with the word Nk positions earlier
        prev_word = key_columns[-Nk]
        word = [b ^ p for b, p in zip(word, prev_word)]
        key_columns.append(word)

    # Group into round keys
    round_keys = [key_columns[j:j+NB] for j in range(0, total_words, NB)]
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
    Decrypt a single block using AES.
    Supports 128/192/256-bit keys based on round_keys length.
    """
    state = bytes2matrix(cipher_block)
    Nr = len(round_keys) - 1  # Number of rounds based on key size

    # Initial round
    add_round_key(state, round_keys[-1])
    inv_shift_rows(state)
    inv_sub_bytes(state)

    # Main rounds
    for rnd in range(Nr-1, 0, -1):
        add_round_key(state, round_keys[rnd])
        inv_mix_columns(state)
        inv_shift_rows(state)
        inv_sub_bytes(state)

    # Final round
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
#     # Test all key sizes
#     test_block = b"Attack at dawn!!"  # 16 bytes

#     # Test AES-128
#     key_128 = b"A"*16
#     rk = key_expansion(key_128)
#     encrypted = encrypt_block(test_block, rk)
#     decrypted = decrypt_block(encrypted, rk)
#     print(f"AES-128: {'Passed' if decrypted == test_block else 'Failed'}")

#     # Test AES-192
#     key_192 = b"B"*24
#     rk = key_expansion(key_192)
#     encrypted = encrypt_block(test_block, rk)
#     decrypted = decrypt_block(encrypted, rk)
#     print(f"AES-192: {'Passed' if decrypted == test_block else 'Failed'}")

#     # Test AES-256
#     key_256 = b"C"*32
#     rk = key_expansion(key_256)
#     encrypted = encrypt_block(test_block, rk)
#     decrypted = decrypt_block(encrypted, rk)
#     print(f"AES-256: {'Passed' if decrypted == test_block else 'Failed'}")
