from tqdm import tqdm
import struct
import random

# Implementasi PLIR-256 Asli
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
                # Tambahan XOR dengan nilai dari iterasi sebelumnya
                prev_xor = h[(j+1) % 8] ^ h[(j+3) % 8]  # Menggunakan dua elemen hash state sebelumnya
                h[j] = (modular_mix(h[j], key) ^ (message[j % message_length] + GOLDEN_RATIO_CONST) ^ prev_xor) & 0xFFFFFFFF
                h[j+1] = (modular_mix(h[j+1], rotate_left(h[j], 13)) ^ (h[(j+3) % 8] >> 5) ^ (h[(j+6) % 8] << 3) ^ rotate_left(h[(j+7) % 8], 17) ^ prev_xor) & 0xFFFFFFFF
        
        return "".join(f"{x:08x}" for x in h[:8])
    
    hashed_output = text
    state = 0
    for _ in range(stages):
        hashed_output = single_stage_hash(hashed_output, state)
        state ^= int(hashed_output[:8], 16)  # Update state dengan bagian awal hash
    hashed_output = hashed_output[:64]
    return hashed_output

# Implementasi SHA-256 Python
def rotate_right(value, shift, bits=32):
    return ((value >> shift) | (value << (bits - shift))) & 0xFFFFFFFF

def sha256_padding(message):
    message = bytearray(message, "utf-8")
    original_length = len(message) * 8
    message.append(0x80)
    while (len(message) * 8) % 512 != 448:
        message.append(0)
    message += original_length.to_bytes(8, "big")
    return message

K = [  # Konstanta SHA-256 (64 Elemen)
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]

def sha256_process_chunk(chunk, h):
    w = [0] * 64
    for i in range(16):
        w[i] = int.from_bytes(chunk[i * 4:(i + 1) * 4], "big")
    for i in range(16, 64):
        s0 = rotate_right(w[i - 15], 7) ^ rotate_right(w[i - 15], 18) ^ (w[i - 15] >> 3)
        s1 = rotate_right(w[i - 2], 17) ^ rotate_right(w[i - 2], 19) ^ (w[i - 2] >> 10)
        w[i] = (w[i - 16] + s0 + w[i - 7] + s1) & 0xFFFFFFFF

    a, b, c, d, e, f, g, h_old = h

    for i in range(64):
        S1 = rotate_right(e, 6) ^ rotate_right(e, 11) ^ rotate_right(e, 25)
        ch = (e & f) ^ (~e & g)
        temp1 = (h_old + S1 + ch + K[i] + w[i]) & 0xFFFFFFFF
        S0 = rotate_right(a, 2) ^ rotate_right(a, 13) ^ rotate_right(a, 22)
        maj = (a & b) ^ (a & c) ^ (b & c)
        temp2 = (S0 + maj) & 0xFFFFFFFF

        h_old = g
        g = f
        f = e
        e = (d + temp1) & 0xFFFFFFFF
        d = c
        c = b
        b = a
        a = (temp1 + temp2) & 0xFFFFFFFF

    return [(x + y) & 0xFFFFFFFF for x, y in zip(h, [a, b, c, d, e, f, g, h_old])]

def sha256_manual(message):
    h = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    ]
    message = sha256_padding(message)
    for i in range(0, len(message), 64):
        h = sha256_process_chunk(message[i:i+64], h)
    return "".join(f"{x:08x}" for x in h)

#  Benchmark Collision Test
def collision_test(hash_function, label, num_tests=100000):
    seen_hashes = set()
    collisions = 0

    for _ in tqdm(range(num_tests), desc=f"Collision Test ({label})", unit=" hash"):
        test_str = str(random.randint(0, 10**18))
        hash_value = hash_function(test_str)

        if hash_value in seen_hashes:
            collisions += 1
        else:
            seen_hashes.add(hash_value)

    return collisions

#  Benchmark Avalanche Effect Test
def avalanche_test(hash_function, label, num_tests=1000):
    total_bit_changes = 0
    total_bits = len(hash_function("test")) * 4

    for _ in tqdm(range(num_tests), desc=f"Avalanche Test ({label})", unit=" test"):
        test_str = str(random.randint(0, 10**18))
        hash1 = hash_function(test_str)

        test_str_modified = test_str[:-1] + chr(ord(test_str[-1]) ^ 1)
        hash2 = hash_function(test_str_modified)

        bit_changes = sum(bin(int(a, 16) ^ int(b, 16)).count("1") for a, b in zip(hash1, hash2))
        total_bit_changes += bit_changes

    return (total_bit_changes / (num_tests * total_bits)) * 100

if __name__ == "__main__":
    num_collision_tests = 100000
    num_avalanche_tests = 1000

    print("\nRunning Collision Test")
    plir_collisions = collision_test(lambda x: secure_plir_256(x, rounds=9, stages=1), "PLIR-256", num_collision_tests)
    sha_collisions = collision_test(lambda x: sha256_manual(x), "SHA-256", num_collision_tests)

    print("\nRunning Avalanche Effect Test")
    plir_avalanche = avalanche_test(lambda x: secure_plir_256(x, rounds=9, stages=1), "PLIR-256", num_avalanche_tests)
    sha_avalanche = avalanche_test(lambda x: sha256_manual(x), "SHA-256", num_avalanche_tests)

    print(f"\nHasil Benchmark:")
    print(f"PLIR-256 Collisions: {plir_collisions} dari {num_collision_tests} tes")
    print(f"SHA-256 Collisions: {sha_collisions} dari {num_collision_tests} tes")
    print(f"PLIR-256 Avalanche Effect: {plir_avalanche:.2f}% perubahan bit")
    print(f"SHA-256 Avalanche Effect: {sha_avalanche:.2f}% perubahan bit")
