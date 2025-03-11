#!/usr/bin/python
#
#
# Written by Prima Agus Setiawan 
# a.k.a joeheartless / joefryme@gmail.com

def rotate_left(x, n):
    x &= 0xFFFFFFFF
    return ((x << n) & 0xFFFFFFFF) | (x >> (32 - n))

def modular_mix(x, y):
    x &= 0xFFFFFFFF
    y &= 0xFFFFFFFF

    part = ((x * 33) ^ (y * 19)) & 0xFFFFFFFF
    part = (part + rotate_left(x, 11)) & 0xFFFFFFFF
    part = (part + rotate_left(y, 15)) & 0xFFFFFFFF
    part = (part + (x >> 3)) & 0xFFFFFFFF

    result = part ^ (y << 2)
    return result & 0xFFFFFFFF

def sum_ascii(text):
    total = 0
    for ch in text:
        total += ord(ch)
    return total

def expand_message_deterministic(text):
    text_len = len(text)
    out_len = (text_len + 3) // 4 

    blocks = []
    s_val = sum_ascii(text)
    seed = (s_val * 137) & 0xFFFFFFFF

    for i in range(out_len):
        chunk = [ord(' '), ord(' '), ord(' '), ord(' ')]
        start_idx = i * 4
        for j in range(4):
            if (start_idx + j) < text_len:
                chunk[j] = ord(text[start_idx + j])

        block_val = (chunk[0]
                    | (chunk[1] << 8)
                    | (chunk[2] << 16)
                    | (chunk[3] << 24))
        block_val &= 0xFFFFFFFF

        shift_val = (seed >> (i % 16)) & 0xFFFFFFFF

        block_val ^= shift_val
        block_val &= 0xFFFFFFFF

        seed = rotate_left(seed, 5) ^ ((seed * 71) & 0xFFFFFFFF)
        seed &= 0xFFFFFFFF

        blocks.append(block_val)

    return blocks, out_len

def single_stage_hash(input_text, prev_state, rounds):
    seed = (sum_ascii(input_text) * 137) & 0xFFFFFFFF

    h = [0]*8
    h[0] = ((0x86B47C4C ^ seed) ^ prev_state) & 0xFFFFFFFF
    h[1] = ((0xEEDFCBB3 ^ seed) ^ prev_state) & 0xFFFFFFFF
    h[2] = ((0x1105DC08 ^ seed) ^ prev_state) & 0xFFFFFFFF
    h[3] = ((0x21FB8A71 ^ seed) ^ prev_state) & 0xFFFFFFFF
    h[4] = ((0x43B675C9 ^ seed) ^ prev_state) & 0xFFFFFFFF
    h[5] = ((0x75B803D5 ^ seed) ^ prev_state) & 0xFFFFFFFF
    h[6] = ((0x864FAAE8 ^ seed) ^ prev_state) & 0xFFFFFFFF
    h[7] = ((0xD7C261FF ^ seed) ^ prev_state) & 0xFFFFFFFF

    message, message_length = expand_message_deterministic(input_text)
    GOLDEN_RATIO_CONST = 0x9E3779B9

    for i in range(rounds):
        key = (GOLDEN_RATIO_CONST
               ^ ((i * 73) & 0xFFFFFFFF)
               ^ ((h[i % 8] << (i % 6)) & 0xFFFFFFFF)
               ^ (h[(i + 3) % 8] >> (i % 4))
               ^ ((h[(i + 5) % 8] << (i % 8)) & 0xFFFFFFFF))
        key &= 0xFFFFFFFF

        for j in range(0, 8, 2):
            prev_xor = h[(j + 1) % 8] ^ h[(j + 3) % 8]
            prev_xor &= 0xFFFFFFFF

            mix_val = modular_mix(h[j], key)
            mix_val ^= (message[j % message_length] + GOLDEN_RATIO_CONST)
            mix_val ^= prev_xor
            mix_val &= 0xFFFFFFFF
            h[j] = mix_val

            mix_val2 = modular_mix(h[j + 1], rotate_left(h[j], 13))
            mix_val2 ^= (h[(j + 3) % 8] >> 5)
            mix_val2 ^= ((h[(j + 6) % 8] << 3) & 0xFFFFFFFF)
            mix_val2 ^= rotate_left(h[(j + 7) % 8], 17)
            mix_val2 ^= prev_xor
            mix_val2 &= 0xFFFFFFFF
            h[j + 1] = mix_val2

    out_hex = ''.join(f'{val:08x}' for val in h)
    return out_hex

def secure_plir_256(text, rounds, stages):
    state = 0
    current_input = text

    stage_hash = ""
    for s in range(stages):
        stage_hash = single_stage_hash(current_input, state, rounds)

        partial_str = stage_hash[:8]  
        partial_val = int(partial_str, 16)
        state ^= partial_val
        state &= 0xFFFFFFFF

        current_input = stage_hash

    return stage_hash

def constant_time_compare(val1, val2):
    if len(val1) != len(val2):
        return False

    result = 0
    for x, y in zip(val1, val2):
        result |= (ord(x) ^ ord(y))
    return (result == 0)

def main():
    input_text = input("Enter text to hash: ").rstrip('\n')

    hash_result = secure_plir_256(input_text, rounds=8, stages=2)
    print(f"PLIR-256 Hash: {hash_result}")

if __name__ == "__main__":
    main()
