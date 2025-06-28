# spn.py
from hashlib import shake_128

# ── 1) S-box & inverse (4-bit toy example) ──
SBOX     = [0x6,0x4,0xC,0x5,0x0,0x7,0x2,0xE,
            0x1,0xF,0x3,0xD,0x8,0xA,0x9,0xB]
INV_SBOX = [SBOX.index(x) for x in range(16)]

# ── 2) P-layer (64-bit) ──
P = [
   0, 9,18,27,36,45,54,63,
   1,10,19,28,37,46,55,56,
   2,11,20,29,38,47,48,57,
   3,12,21,30,39,40,49,58,
   4,13,22,31,32,41,50,59,
   5,14,23,24,33,42,51,60,
   6,15,16,25,34,43,52,61,
   7, 8,17,26,35,44,53,62
]

def permute64(x):
    out = 0
    for i in range(64):
        bit = (x >> i) & 1
        out |= bit << P[i]
    return out

def inv_permute64(x):
    out = 0
    for i, pi in enumerate(P):
        bit = (x >> pi) & 1
        out |= bit << i
    return out

# ── 3) S-box layer ──
def apply_sbox(x):
    out = 0
    for byte_i in range(8):
        b  = (x >> (8*byte_i)) & 0xFF
        hi, lo = b>>4, b&0xF
        hi2, lo2 = SBOX[hi], SBOX[lo]
        out |= (hi2<<4 | lo2) << (8*byte_i)
    return out

def inv_sbox_layer(x):
    out = 0
    for byte_i in range(8):
        b  = (x >> (8*byte_i)) & 0xFF
        hi, lo = b>>4, b&0xF
        hi2, lo2 = INV_SBOX[hi], INV_SBOX[lo]
        out |= (hi2<<4 | lo2) << (8*byte_i)
    return out

# ── 4) Key schedule ──
def expand_key(k1, k2, rounds=12):
    seed  = (k1 + k2).encode()
    shake = shake_128(seed)
    # produce rounds+1 64-bit subkeys
    return [
        int.from_bytes(shake.digest(8), 'big')
        for _ in range(rounds+1)
    ]

# ── 5) Round functions ──
def encrypt_block(x, round_keys):
    for k in round_keys[:-1]:
        x ^= k
        x  = apply_sbox(x)
        x  = permute64(x)
    # final whitening
    return x ^ round_keys[-1]

def decrypt_block(x, round_keys):
    x ^= round_keys[-1]
    for k in reversed(round_keys[:-1]):
        x  = inv_permute64(x)
        x  = inv_sbox_layer(x)
        x ^= k
    return x

# ── 6) Stream wrapper ──
def split_blocks(bitstr, block_size=64):
    """Split to 64-bit chunks, right-pad each with '0's."""
    out, n = [], block_size
    total = len(bitstr)
    for i in range(0, total, n):
        blk = bitstr[i:i+n].ljust(n, '0')
        out.append(int(blk, 2))
    return out

def encrypt_stream(bitstr, k1, k2):
    """
    Returns (cipher_bits, original_length).
    `cipher_bits` length = ceil(len(bitstr)/64)*64.
    """
    keys   = expand_key(k1, k2)
    blocks = split_blocks(bitstr)
    cints  = [encrypt_block(b, keys) for b in blocks]
    # join *all* bits, no truncation
    cipher_bits = ''.join(f"{x:064b}" for x in cints)
    return cipher_bits, len(bitstr)

def decrypt_stream(cipher_bits, k1, k2, orig_len):
    """
    Reverses `encrypt_stream`; uses `orig_len` to chop
    off the padding at the end.
    """
    keys   = expand_key(k1, k2)
    blocks = split_blocks(cipher_bits)
    pints  = [decrypt_block(b, keys) for b in blocks]
    bits   = ''.join(f"{x:064b}" for x in pints)
    return bits[:orig_len]


# ── 7) Self-test harness ──

## Run for testing reasons only
if __name__ == "__main__":
    # 7a) single-block sanity check
    sample = 0x0123456789ABCDEF
    print("PLAIN     :", f"{sample:064b}")
    ks     = expand_key("1", "2", rounds=4)
    ct     = encrypt_block(sample, ks)
    pt     = decrypt_block(ct, ks)
    print("CIPHER    :", f"{ct:064b}")
    print("ROUND-TRIP:", f"{pt:064b}")
    assert pt == sample, "✗ single-block SPN failed!"
    print("✔ single-block SPN OK\n")

    # 7b) stream-mode tests
    tests = [
        "", "0", "1", "101",
        "1101001", "0"*64, "1"*65, "101010"*11
    ]
    for bits in tests:
        ct_bits, length = encrypt_stream(bits, "123", "4567")
        pt_bits = decrypt_stream(ct_bits, "123", "4567", length)
        assert pt_bits == bits, (
            f"✗ STREAM-SPN fail on '{bits[:16]}…' → got '{pt_bits[:16]}…'"
        )
    print("✅ encrypt_stream/decrypt_stream round-trip OK")
