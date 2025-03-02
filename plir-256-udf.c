#define MYSQL_DYNAMIC_PLUGIN
#include <mysql/mysql.h>
#include <mysql/udf_registration_types.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

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

bool PLIR256_init(UDF_INIT *initid, UDF_ARGS *args, char *message)
{
    if (args->arg_count != 1) {
        strncpy(message, "PLIR256() requires exactly one string argument.", MYSQL_ERRMSG_SIZE);
        return true; 
    }
    if (args->arg_type[0] != STRING_RESULT) {
        strncpy(message, "PLIR256() argument must be a string.", MYSQL_ERRMSG_SIZE);
        return true;
    }

    initid->maybe_null = 1; 
    return false;           
}

char *PLIR256(UDF_INIT *initid, UDF_ARGS *args, char *result,
              unsigned long *length, bool *is_null, bool *error)
{
    if (!args->args[0]) {
        *is_null = true;
        return NULL;
    }

    static char hash_result[65];
    hash_result[64] = '\0';

    secure_plir_256(args->args[0], 8, 1, hash_result);

    strcpy(result, hash_result);
    *length = (unsigned long)strlen(hash_result);

    return result;
}

void PLIR256_deinit(UDF_INIT *initid)
{

}

#ifdef __cplusplus
} 
#endif
