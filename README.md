# PLIR-256 Hash Implementation

This repository contains a C implementation of a custom hashing algorithm called **PLIR-256**. The code is intended as a demonstrative project, showcasing how to create and combine several bitwise operations, shifts, and arithmetic manipulations to produce a 256-bit hash value from a given input string.

## Overview

1. **rotate_left**  
   Performs a bitwise left rotation on a 32-bit integer.

2. **modular_mix**  
   Combines two 32-bit integers using multiplication, rotation, and XOR operations. This serves as one of the key mixing functions within the hashing process.

3. **sum_ascii**  
   Calculates the sum of the ASCII values of all characters in a given string.

4. **expand_message_deterministic**  
   Splits the input string into 32-bit blocks, appending whitespace characters (`' '`) if the input is not large enough to fill a full block. The process involves applying a seed-based shift to each block, thus adding variability dependent on the input's ASCII sum.

5. **single_stage_hash**  
   Produces a 256-bit hash (in hex format) by processing the input text through the above utility functions. It initializes an array of eight 32-bit values, then iteratively refines these values using `modular_mix`, rotation, shifting, and XOR.

6. **secure_plir_256**  
   Builds upon `single_stage_hash` to perform multiple _stages_ of hashing. It also incorporates an internal `state` that updates with a partial component of the hash between each stage.

7. **constant_time_compare**  
   Compares two hash strings in a way that mitigates timing-based side-channel leaks. The comparison does not short-circuit upon finding the first mismatch; it processes all characters in a uniform time.

## Features

- Generates a deterministic 256-bit hash string from any input text.
- Conducts multiple hashing stages, increasing the complexity and potential collision resistance of the result.
- Demonstrates a rudimentary approach to timing-attack mitigation with `constant_time_compare`.

## Requirements

- A C compiler (for example, `gcc`, `clang`).
- Standard C libraries: `stdio.h`, `stdlib.h`, `string.h`, `stdint.h`.

## Compilation

Use your preferred C compiler to compile the program. For instance:

```bash
gcc -o plir-256 plir-256.c
```
```bash
./plir-256
```
## Example Output
```bash
Enter text to hash: Password
PLIR-256 Hash: 7a368ff539c86b89f6819bdc881dcc796e5848c0b18860f206d7f35e37a38afb
```
## Includes
- **plirsum.c**
- **plir-256-udf.c**


# plirsum.c

## Usage
PLIR-256 supports various operation modes:

### **Hashing a File**
```sh
plirsum [FILE]
```
Example:
```sh
plirsum example.txt
```

### **Hashing from Standard Input**
```sh
echo "password" | plirsum
```
Output:
```
d8b9f1a3c481619eab12c6400434d18f72b279b9c00b75b03fed302b7d2a758c13bd28c606  -
```

### **Generate Random Salt (8-64 characters)**
```sh
plirsum --rand 16
```
Example output:
```
3a4f8d1b9c2e7f6a
```

### **Generate Dynamic Iteration Count for Hashing**
```sh
plirsum --randit 4
```
Example output:
```
1255
```

### **Help and Version Information**
```sh
plirsum --help   # Display full guide
plirsum --version  # Show version
```

---

## Hashing Scheme with Salt & Dynamic Iteration
PLIR-256 can be used for **more secure password hashing** with the following method:

1. **Generate Salt**:
   ```sh
   SALT=$(plirsum --rand 8)
   ```
2. **Generate Dynamic Iteration Count**:
   ```sh
   ITER=$(plirsum --randit 4)
   ```
3. **Hash Password + Salt**:
   ```sh
   HASH=$(echo "mypassword$SALT" | plirsum)
   ```
4. **Store the result in the following format for the database:**
   ```plaintext
   ITER + SALT + HASH
   ```
   Example:
   ```plaintext
   1255a1b2c3d481619eab12c6400434d18f72b279b9c00b75b03fed302b7d2a758c13bd28c606
   ```

---
