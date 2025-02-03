#!/usr/bin/python
#
#
# Written by Prima Agus Setiawan 
# a.k.a joeheartless / joefryme@gmail.com

import struct
import hmac
import time

def rotate_left(x, n, bits=32):
    return ((x << n) & (2**bits - 1)) | (x >> (bits - n))

def modular_mix(x, y):
    return ((x * 31) + (y * 17) + rotate_left(x, 7) + rotate_left(y, 11)) % (2**32)

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
                h[j] = modular_mix(h[j], key) ^ (message[j % message_length] + GOLDEN_RATIO_CONST) & 0xFFFFFFFF
                h[j+1] = modular_mix(h[j+1], rotate_left(h[j], 13)) ^ (h[(j+3) % 8] >> 5) ^ (h[(j+6) % 8] << 3) ^ rotate_left(h[(j+7) % 8], 17)
        
        return "".join(f"{x:08x}" for x in h[:8])
    
    hashed_output = text
    state = 0
    for _ in range(stages):
        hashed_output = single_stage_hash(hashed_output, state)
    hashed_output = hashed_output[:64]
    return hashed_output
    
def constant_time_compare(val1, val2):
    return hmac.compare_digest(val1, val2)

if __name__ == "__main__":
    user_input = input("Masukkan teks untuk di-hash: ")
    hash_result = secure_plir_256(user_input)
    print("PLIR-256 Hash:", hash_result)
