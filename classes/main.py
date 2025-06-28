#!/usr/bin/env python3
from pad_rotate import (
    text_to_bits, bits_to_text,
    pad1, unpad1,
    pad2_rotate, unpad2_rotate
)
from spn import encrypt_stream, decrypt_stream

if __name__ == "__main__":
    k1 = input("Key 1 (digits): ").strip()
    k2 = input("Key 2 (digits): ").strip()
    pt = input("Plain text: ")

    # ── 1) Convert to bits
    bits = text_to_bits(pt)

    # ── 2) SPN encrypt in stream mode
    ct_spn, orig_len = encrypt_stream(bits, k1, k2)

    # ── 3) Pad & rotate layer
    ct_pr, shifts = pad2_rotate(pad1(ct_spn, k1), k2)

    print("\nCipher text bits:\n", ct_pr)
    input("\nPress ENTER to decrypt → ")

    # ── 4) Reverse pad & rotate
    rec_bits = unpad2_rotate(ct_pr, shifts)
    rec_bits = unpad1(rec_bits, k1)

    # ── 5) SPN decrypt
    rec_bits = decrypt_stream(rec_bits, k1, k2, orig_len)

    # ── 6) Bits → text
    print("\nRecovered text:\n", bits_to_text(rec_bits))
