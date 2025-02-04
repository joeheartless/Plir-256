#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define GOLDEN_RATIO_CONST 0x9E3779B9
#define ROUNDS 8

// Rotasi kiri
static inline uint32_t rotate_left(uint32_t x, uint32_t n) {
    return (x << n) | (x >> (32 - n));
}

// Mixing function
uint32_t modular_mix(uint32_t x, uint32_t y) {
    return ((x * 33) ^ (y * 19) + rotate_left(x, 11) + rotate_left(y, 15) + (x >> 3) ^ (y << 2)) & 0xFFFFFFFF;
}

// Ekspansi pesan ke blok 32-bit
void expand_message_deterministic(const char *text, uint32_t *blocks, size_t *num_blocks) {
    uint32_t seed = 137;
    size_t len = strlen(text);
    *num_blocks = (len + 3) / 4;

    for (size_t i = 0; i < *num_blocks; i++) {
        uint32_t chunk = 0;
        memcpy(&chunk, text + i * 4, (len - i * 4) > 4 ? 4 : (len - i * 4));
        blocks[i] = chunk ^ (seed >> (i % 16));
        seed = rotate_left(seed, 5) ^ (seed * 71);
    }
}

// Fungsi hashing utama
void secure_plir_256(const char *text, char *output) {
    uint32_t h[8] = {
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    };

    uint32_t blocks[64];
    size_t num_blocks;
    expand_message_deterministic(text, blocks, &num_blocks);

    for (int i = 0; i < ROUNDS; i++) {
        uint32_t key = GOLDEN_RATIO_CONST ^ (i * 73) ^ (h[i % 8] << (i % 6)) ^ (h[(i+3) % 8] >> (i % 4)) ^ (h[(i+5) % 8] << (i % 8));

        for (int j = 0; j < 8; j += 2) {
            uint32_t prev_xor = h[(j+1) % 8] ^ h[(j+3) % 8];
            h[j] = (modular_mix(h[j], key) ^ (blocks[j % num_blocks] + GOLDEN_RATIO_CONST) ^ prev_xor) & 0xFFFFFFFF;
            h[j+1] = (modular_mix(h[j+1], rotate_left(h[j], 13)) ^ (h[(j+3) % 8] >> 5) ^ (h[(j+6) % 8] << 3) ^ rotate_left(h[(j+7) % 8], 17) ^ prev_xor) & 0xFFFFFFFF;
        }
    }

    // Konversi hasil ke hex string
    snprintf(output, 65, "%08x%08x%08x%08x%08x%08x%08x%08x",
             h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]);
}

int main() {
    char input[256];
    char hash_output[65];

    printf("Enter text to hash: ");
    fgets(input, sizeof(input), stdin);
    input[strcspn(input, "\n")] = 0; // Hapus newline

    secure_plir_256(input, hash_output);
    printf("PLIR-256 Hash: %s\n", hash_output);

    return 0;
}
