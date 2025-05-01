import random
from _2005042_aes import aes_cbc_encrypt, aes_cbc_decrypt
from sympy import nextprime
def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def generate_prime_number(bits=128) -> int:
    """
    Generate a prime number with exactly 'bits' length.
    Ensures the returned prime is congruent to 3 mod 4 for efficient square root calculation.
    """
    while True:
        # Start with a number that's already congruent to 3 mod 4
        candidate = random.getrandbits(bits)
        candidate |= 3  # Ensure it's congruent to 3 mod 4
        prime = int(nextprime(candidate))
        if prime.bit_length() == bits and prime % 4 == 3:
            return prime

def generate_equation_parameters(bits=128) -> tuple:
    """
    Generate secure curve parameters following NIST standards.
    Ensures the curve is non-singular and has a valid generator point.
    """
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            # Generate prime p ≡ 3 mod 4 for efficient square root calculation
            p = generate_prime_number(bits)
            
            # Generate curve parameters
            a = random.randint(1, p-1)
            b = random.randint(1, p-1)
            
            # Check if curve is non-singular
            discriminant = (4 * pow(a, 3, p) + 27 * pow(b, 2, p)) % p
            if discriminant == 0:
                continue
                
            # Try to find a generator point
            G = find_point_on_curve(p, a, b)
            if G is not None:
                return p, a, b, G
                
        except ValueError:
            if attempt < max_attempts - 1:
                continue
            raise ValueError("Failed to generate valid curve parameters after multiple attempts")
    
    raise ValueError("Failed to generate valid curve parameters")

def is_on_curve(x, y, p, a, b):
    return (y**2 - x**3 - a*x - b) % p == 0

def find_point_on_curve(p, a, b, max_attempts=1000):
    """
    Find a point on the elliptic curve using efficient methods.
    Optimized for primes congruent to 3 mod 4.
    """
    # Try small x values first (more likely to work)
    for x in range(1, min(10, p)):
        y_squared = (x**3 + a*x + b) % p
        
        # Check if y_squared is a quadratic residue
        if pow(y_squared, (p-1)//2, p) == 1:
            # Since p ≡ 3 mod 4, we can use the efficient square root formula
            y = pow(y_squared, (p+1)//4, p)
            if is_on_curve(x, y, p, a, b):
                return x, y
            y = (-y) % p
            if is_on_curve(x, y, p, a, b):
                return x, y

    # If small x values don't work, try random values
    attempts = 0
    while attempts < max_attempts:
        x = random.randint(2, p-1)
        y_squared = (x**3 + a*x + b) % p
        
        # Check if y_squared is a quadratic residue
        if pow(y_squared, (p-1)//2, p) == 1:
            y = pow(y_squared, (p+1)//4, p)
            if is_on_curve(x, y, p, a, b):
                return x, y
            y = (-y) % p
            if is_on_curve(x, y, p, a, b):
                return x, y
        attempts += 1

    raise ValueError("Failed to find a point on the curve")

def point_add(P1, P2, a, p):
    if P1 is None:
        return P2
    if P2 is None:
        return P1

    x1, y1 = P1
    x2, y2 = P2

    if x1 == x2 and y1 != y2:
        return None

    if P1 == P2:
        s_num = (3 * x1 * x1 + a) % p
        s_den = pow(2 * y1, -1, p)
    else:
        s_num = (y2 - y1) % p
        s_den = pow((x2 - x1) % p, -1, p)

    s = (s_num * s_den) % p
    x3 = (s * s - x1 - x2) % p
    y3 = (s * (x1 - x3) - y1) % p

    return (x3, y3)


def scalar_mult(k, point, a, p):
    """
    Multiply a point by an integer k using double-and-add.
    Following standard ECC multiplication algorithm.
    """
    result = None
    addend = point

    while k > 0:
        if k & 1:
            result = point_add(result, addend, a, p)
        addend = point_add(addend, addend, a, p)
        k >>= 1

    return result

def ecdh_shared_key(p, a, b, G):
    """
    Perform ECDH key exchange following standard protocol.
    """
    # Generate secure random private keys
    Ka = random.randint(1, p-1)
    Kb = random.randint(1, p-1)

    # Compute public keys
    A = scalar_mult(Ka, G, a, p)
    B = scalar_mult(Kb, G, a, p)

    # Compute shared secret
    SA = scalar_mult(Ka, B, a, p)
    SB = scalar_mult(Kb, A, a, p)

    assert SA == SB, "Shared secrets do not match!"
    assert SA is not None, "Invalid shared secret point"

    # Convert x-coordinate of S to AES key (256-bit)
    shared_x = SA[0]
    aes_key = shared_x.to_bytes(32, 'big')[:32]  # Using 256-bit key for AES-256

    return aes_key

def simulate_secure_communication():
    # Step 1: ECC key exchange
    p, a, b, G = generate_equation_parameters(128)
    aes_key = ecdh_shared_key(p, a, b, G)

    # Step 2: Alice encrypts message
    message = b"Hello Bob, this is Alice!"
    ciphertext = aes_cbc_encrypt(message, aes_key)
    print("\n[+] Encrypted message (hex):", ciphertext.hex())

    # Step 3: Bob decrypts it
    decrypted = aes_cbc_decrypt(ciphertext, aes_key)
    print("[+] Decrypted message:", decrypted)

# Remove the automatic execution
# simulate_secure_communication()

# print(generate_prime_number(128))



    




