import struct
import hashlib
import hmac
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from collections import Counter
from scipy.stats import chi2, norm

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

def monobit_test(bitstream):
    ones = bitstream.count("1")
    zeros = bitstream.count("0")
    total = len(bitstream)
    expected = total / 2
    chi_square = ((ones - expected) ** 2 + (zeros - expected) ** 2) / expected
    p_value = 1 - chi2.cdf(chi_square, df=1)
    return p_value

def runs_test_fixed(bitstream):
    ones = bitstream.count("1")
    zeros = bitstream.count("0")
    total = len(bitstream)

    runs = 1
    for i in range(1, total):
        if bitstream[i] != bitstream[i - 1]:
            runs += 1

    expected_runs = ((2 * ones * zeros) / total) + 1
    std_dev = np.sqrt((2 * ones * zeros * (2 * ones * zeros - total)) / ((total ** 2) * (total - 1)))
    
    if std_dev == 0:
        return 1.0
    
    z = (runs - expected_runs) / std_dev
    p_value = 2 * (1 - norm.cdf(abs(z)))
    
    return p_value

test_bitstream = ''.join(random.choices("01", k=1024))

monobit_result = monobit_test(test_bitstream)

runs_result_fixed = runs_test_fixed(test_bitstream)

nist_results_df = pd.DataFrame({
    "Test Type": ["Monobit Test", "Runs Test"],
    "P-Value": [monobit_result, runs_result_fixed]
})

plt.figure(figsize=(8, 5))
sns.barplot(x="Test Type", y="P-Value", hue="Test Type", data=nist_results_df, palette="viridis", legend=False)
plt.axhline(y=0.01, color='r', linestyle='--', label="Threshold (p=0.01)")
plt.title("NIST STS Test Results (Monobit & Runs Test)")
plt.ylabel("P-Value")
plt.legend()
plt.ylim(0, 1)
plt.show()
