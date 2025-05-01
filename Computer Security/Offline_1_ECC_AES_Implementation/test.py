from BitVector import *

# Create a simple bit vector from hex string
bv = BitVector(hexstring="1A")

# Print the bit vector in different formats
print("Hex representation:", bv.get_bitvector_in_hex())
print("Binary representation:", bv.get_bitvector_in_ascii())
print("Integer value:", bv.intValue()) 