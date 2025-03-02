import struct
import hashlib
import hmac
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from collections import Counter

def rotate_left(x, n, bits=32):
    return ((x << n) & (2**bits - 1)) | (x >> (bits - n))

def modular_mix(x, y):
    return ((x * 33) ^ (y * 19) + rotate_left(x, 11) + rotate_left(y, 15) + (x >> 3) ^ (y << 2)) % (2**32)

def expand_message_deterministic(text):
    blocks = []
    seed = sum(ord(c) for c in text) * 137
    for i in range(0, len(text), 4):
        chunk = text[i:i+4].ljust(4, " ").encode()
        block = struct.unpack("<I", chunk)[0] ^ (seed >> (i % 16))
        seed = rotate_left(seed, 5) ^ (seed * 71)
        blocks.append(block)
    return blocks

def secure_plir_256(text, rounds=8, stages=1): 
    GOLDEN_RATIO_CONST = 0x9E3779B9

    def single_stage_hash(input_text, prev_state=0):
        h = [
            0x6a09e667 ^ prev_state, 0xbb67ae85 ^ prev_state, 0x3c6ef372 ^ prev_state, 0xa54ff53a ^ prev_state,
            0x510e527f ^ prev_state, 0x9b05688c ^ prev_state, 0x1f83d9ab ^ prev_state, 0x5be0cd19 ^ prev_state
        ]
        message = expand_message_deterministic(input_text)
        message_length = len(message)
        
        for i in range(rounds):
            key = GOLDEN_RATIO_CONST ^ (i * 73) ^ (h[i % 8] << (i % 6)) ^ (h[(i+3) % 8] >> (i % 4)) ^ (h[(i+5) % 8] << (i % 8))
            
            for j in range(0, len(h), 2):
                prev_xor = h[(j+1) % 8] ^ h[(j+3) % 8] 
                h[j] = (modular_mix(h[j], key) ^ (message[j % message_length] + GOLDEN_RATIO_CONST) ^ prev_xor) & 0xFFFFFFFF
                h[j+1] = (modular_mix(h[j+1], rotate_left(h[j], 13)) ^ (h[(j+3) % 8] >> 5) ^ (h[(j+6) % 8] << 3) ^ rotate_left(h[(j+7) % 8], 17) ^ prev_xor) & 0xFFFFFFFF
        
        return "".join(f"{x:08x}" for x in h[:8])
    
    hashed_output = text
    state = 0
    for _ in range(stages):
        hashed_output = single_stage_hash(hashed_output, state)
        state ^= int(hashed_output[:8], 16) 
    hashed_output = hashed_output[:64]
    return hashed_output

def md5_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

def sha256_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def plir256_hash(text):
    return secure_plir_256(text)

def hex_to_bitstream(hex_string):
    return ''.join(f"{int(c, 16):04b}" for c in hex_string)

def bit_distribution(hash_func, test_strings):
    bit_counts = np.zeros(256)  

    for text in test_strings:
        bitstream = hex_to_bitstream(hash_func(text))
        for i, bit in enumerate(bitstream):
            if bit == '1':
                bit_counts[i % 256] += 1 

    return bit_counts / len(test_strings)

def generate_random_strings(num_samples=50000, length=32):
    return [''.join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=length)) for _ in range(num_samples)]

num_samples = 50000  
test_strings = generate_random_strings(num_samples)

bit_dist_results = {
    "SHA-256": bit_distribution(sha256_hash, test_strings),
    "PLIR-256": bit_distribution(plir256_hash, test_strings),
}

bit_dist_df = pd.DataFrame({
    "Bit Position": list(range(256)) * 2,
    "Bit Probability": np.concatenate([bit_dist_results["SHA-256"], bit_dist_results["PLIR-256"]]),
    "Hashing Algorithm": ["SHA-256"] * 256 + ["PLIR-256"] * 256,
})

plt.figure(figsize=(12, 6))
sns.lineplot(x="Bit Position", y="Bit Probability", hue="Hashing Algorithm", data=bit_dist_df)
plt.axhline(y=0.5, color='r', linestyle='--', label="Ideal (50%)")
plt.title("Bit Distribution Comparison: SHA-256 vs PLIR-256")
plt.xlabel("Bit Position")
plt.ylabel("Probability of Bit being 1")
plt.legend()
plt.show()
