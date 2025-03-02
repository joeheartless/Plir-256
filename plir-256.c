#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

static inline uint32_t rotate_left(uint32_t x, int n) {
    return (x << n) | (x >> (32 - n));
}

uint32_t modular_mix(uint32_t x, uint32_t y) {

    uint32_t result = (x * 33U) ^ (y * 19U) 
                    + rotate_left(x, 11) 
                    + rotate_left(y, 15)
                    + (x >> 3) 
                    ^ (y << 2);

    return result & 0xFFFFFFFF;
}

static int sum_ascii(const char *text) {
    int total = 0;
    while (*text) {
        total += (unsigned char)(*text);
        text++;
    }
    return total;
}

uint32_t* expand_message_deterministic(const char *text, size_t *out_len) {
    size_t text_len = strlen(text);
    *out_len = (text_len + 3) / 4;

    uint32_t *blocks = (uint32_t*)malloc(*out_len * sizeof(uint32_t));
    if (!blocks) {
        fprintf(stderr, "Memory allocation failed.\n");
        exit(EXIT_FAILURE);
    }

    int sum_val = sum_ascii(text);
    uint32_t seed = (uint32_t)(sum_val * 137);

    for (size_t i = 0; i < *out_len; i++) {
        unsigned char chunk[4] = { ' ', ' ', ' ', ' ' };
        size_t start_idx = i * 4;
        for (size_t j = 0; j < 4; j++) {
            if (start_idx + j < text_len) {
                chunk[j] = (unsigned char)text[start_idx + j];
            }
        }

        uint32_t block_val = (uint32_t)(chunk[0])
                           | ((uint32_t)chunk[1] << 8)
                           | ((uint32_t)chunk[2] << 16)
                           | ((uint32_t)chunk[3] << 24);

        uint32_t shift_val = seed >> (i % 16);
        block_val ^= shift_val;

        seed = rotate_left(seed, 5) ^ (seed * 71U);

        blocks[i] = block_val;
    }

    return blocks;
}

void single_stage_hash(const char *input_text, uint32_t prev_state, int rounds, char *out_hex) {
    uint32_t h[8];
    h[0] = 0x6a09e667 ^ prev_state;
    h[1] = 0xbb67ae85 ^ prev_state;
    h[2] = 0x3c6ef372 ^ prev_state;
    h[3] = 0xa54ff53a ^ prev_state;
    h[4] = 0x510e527f ^ prev_state;
    h[5] = 0x9b05688c ^ prev_state;
    h[6] = 0x1f83d9ab ^ prev_state;
    h[7] = 0x5be0cd19 ^ prev_state;

    size_t message_length;
    uint32_t *message = expand_message_deterministic(input_text, &message_length);

    const uint32_t GOLDEN_RATIO_CONST = 0x9E3779B9;

    for (int i = 0; i < rounds; i++) {
        uint32_t key = GOLDEN_RATIO_CONST 
                     ^ (i * 73U)
                     ^ (h[i % 8] << (i % 6))
                     ^ (h[(i + 3) % 8] >> (i % 4))
                     ^ (h[(i + 5) % 8] << (i % 8));

        for (int j = 0; j < 8; j += 2) {
            uint32_t prev_xor = h[(j + 1) % 8] ^ h[(j + 3) % 8];

            h[j] = modular_mix(h[j], key)
                 ^ (message[j % message_length] + GOLDEN_RATIO_CONST)
                 ^ prev_xor;
            h[j] &= 0xFFFFFFFF; 

            h[j + 1] = modular_mix(h[j + 1], rotate_left(h[j], 13))
                     ^ (h[(j + 3) % 8] >> 5)
                     ^ (h[(j + 6) % 8] << 3)
                     ^ rotate_left(h[(j + 7) % 8], 17)
                     ^ prev_xor;
            h[j + 1] &= 0xFFFFFFFF;
        }
    }

    free(message);
    sprintf(out_hex,
        "%08x%08x%08x%08x%08x%08x%08x%08x",
        h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]
    );
}

void secure_plir_256(const char *text, int rounds, int stages, char *out_hex) {

    char stage_hash[65];
    stage_hash[64] = '\0';

    uint32_t state = 0U;

    char *current_input = (char*)malloc(strlen(text) + 1);
    if (!current_input) {
        fprintf(stderr, "Memory allocation failed.\n");
        exit(EXIT_FAILURE);
    }
    strcpy(current_input, text);

    for (int s = 0; s < stages; s++) {
        single_stage_hash(current_input, state, rounds, stage_hash);

        char temp[9];
        memcpy(temp, stage_hash, 8);
        temp[8] = '\0';
        uint32_t partial = (uint32_t)strtoul(temp, NULL, 16);
        state ^= partial;

        free(current_input);
        current_input = (char*)malloc(65);
        if (!current_input) {
            fprintf(stderr, "Memory allocation failed.\n");
            exit(EXIT_FAILURE);
        }
        strcpy(current_input, stage_hash);
    }

    strcpy(out_hex, stage_hash);
    free(current_input);
}

int constant_time_compare(const char *val1, const char *val2) {
    size_t len1 = strlen(val1);
    size_t len2 = strlen(val2);

    if (len1 != len2) {
        return 0;
    }

    unsigned char result = 0;
    for (size_t i = 0; i < len1; i++) {
        result |= (val1[i] ^ val2[i]);
    }
    return (result == 0);
}

int main(void) {
    char input_text[1024];
    printf("Enter text to hash: ");
    if (!fgets(input_text, sizeof(input_text), stdin)) {
        fprintf(stderr, "Error reading input.\n");
        return 1;
    }
    size_t len = strlen(input_text);
    if (len > 0 && input_text[len - 1] == '\n') {
        input_text[len - 1] = '\0';
    }

    char hash_result[65];
    hash_result[64] = '\0';

    secure_plir_256(input_text, 8, 1, hash_result);

    printf("PLIR-256 Hash: %s\n", hash_result);

    return 0;
}
