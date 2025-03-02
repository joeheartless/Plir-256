#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

#define GOLDEN_RATIO_CONST 0x9E3779B9
#define ROUNDS 8
#define CHUNK_SIZE 4096

static inline uint32_t rotate_left(uint32_t x, uint32_t n) {
    return (x << n) | (x >> (32 - n));
}

uint32_t modular_mix(uint32_t x, uint32_t y) {
    return ((x * 33) ^ (y * 19) + rotate_left(x, 11) + rotate_left(y, 15) + (x >> 3) ^ (y << 2)) & 0xFFFFFFFF;
}

void expand_message_deterministic(const char *text, size_t len, uint32_t **blocks, size_t *num_blocks) {
    uint32_t seed = 137;
    *num_blocks = (len + 3) / 4;

    *blocks = (uint32_t *)calloc(*num_blocks, sizeof(uint32_t));
    if (!*blocks) {
        perror("Memory allocation failed");
        exit(1);
    }

    for (size_t i = 0; i < *num_blocks; i++) {
        memcpy(&((*blocks)[i]), text + i * 4, (len - i * 4) > 4 ? 4 : (len - i * 4));
        (*blocks)[i] ^= (seed >> (i % 16));
        seed = rotate_left(seed, 5) ^ (seed * 71);
    }
}

void secure_plir_256(const char *text, size_t len, uint32_t *hash_state) {
    uint32_t *blocks = NULL;
    size_t num_blocks;
    expand_message_deterministic(text, len, &blocks, &num_blocks);

    for (int i = 0; i < ROUNDS; i++) {
        uint32_t key = GOLDEN_RATIO_CONST ^ (i * 73) ^ (hash_state[i % 8] << (i % 6)) ^
                       (hash_state[(i + 3) % 8] >> (i % 4)) ^ (hash_state[(i + 5) % 8] << (i % 8));

        for (int j = 0; j < 8; j += 2) {
            uint32_t prev_xor = hash_state[(j + 1) % 8] ^ hash_state[(j + 3) % 8];
            hash_state[j] = (modular_mix(hash_state[j], key) ^ (blocks[j % num_blocks] + GOLDEN_RATIO_CONST) ^ prev_xor) & 0xFFFFFFFF;
            hash_state[j + 1] = (modular_mix(hash_state[j + 1], rotate_left(hash_state[j], 13)) ^
                                 (hash_state[(j + 3) % 8] >> 5) ^ (hash_state[(j + 6) % 8] << 3) ^
                                 rotate_left(hash_state[(j + 7) % 8], 17) ^ prev_xor) & 0xFFFFFFFF;
        }
    }

    free(blocks);
}

void hash_file(const char *filename, char *output) {
    FILE *file = fopen(filename, "rb");
    if (!file) {
        perror("File error");
        return;
    }

    uint32_t h[8] = {
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    };

    char buffer[CHUNK_SIZE];
    size_t bytes_read;

    while ((bytes_read = fread(buffer, 1, CHUNK_SIZE, file)) > 0) {
        secure_plir_256(buffer, bytes_read, h);
    }

    fclose(file);
    snprintf(output, 65, "%08x%08x%08x%08x%08x%08x%08x%08x",
             h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <filename>\n", argv[0]);
        return 1;
    }

    char hash_output[65];
    hash_file(argv[1], hash_output);

    printf("%s  %s\n", hash_output, argv[1]);

    return 0;
}
