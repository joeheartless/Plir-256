# Plir-256
Plir 256 is a custom hashing algorithm that leverages bit rotation, modular mix, and deterministic message expansion to generate strong hashes with multiple stage processing.

## Key Features
- **Dynamic Bit Rotation**: Utilizes bitwise shift & rotate to enhance diffusion.
- **Modular Mixing**: Combines modular arithmetic & shifting to improve collision resistance.
- **Deterministic Message Expansion**: Breaks input into smaller blocks to ensure better information distribution.
- **Constant-Time Comparison**: Uses `hmac.compare_digest()` to prevent timing attacks.

## Usage
```bash
python plir_256.py
```
Enter the text you want to hash, and the hash result will be displayed.

## Code Structure
- `rotate_left(x, n)`: Bitwise left rotation function.
- `modular_mix(x, y)`: Modular mixing operation to spread entropy.
- `expand_message_deterministic(text)`: Converts input text into numeric blocks.
- `secure_plir_256(text, rounds=8, stages=1)`: Main hashing function with multiple processing stages.
- `constant_time_compare(val1, val2)`: String comparison function safe from timing attacks.

## Example Output
```bash
Enter text to hash: hello
PLIR-256 Hash: 4cbb43eef2c600196355285b4029664135704367acb77177d5b1058a49aff63f
```
## Benchmarks
- **Bit Distribution**
- **NIST STS**
- **Hash Time**
- **Avalanche Effect & Collision Test**
