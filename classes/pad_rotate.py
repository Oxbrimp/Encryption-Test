# pad_rotate.py

def text_to_bits(s):
    return ''.join(f"{ord(c):07b}" for c in s)

def bits_to_text(b):
    chars = [b[i:i+7] for i in range(0, len(b), 7)]
    return ''.join(chr(int(x,2)) for x in chars)

def pad1(bitstr, key1):
    kd = list(map(int, key1))
    out = []
    for i, bit in enumerate(bitstr):
        z = kd[i % len(kd)]
        out.append(bit + "0"*z)
    return "".join(out)

def unpad1(bitstr, key1):
    kd = list(map(int, key1))
    out, i, j = [], 0, 0
    while j < len(bitstr):
        out.append(bitstr[j])
        j += 1 + kd[i % len(kd)]
        i += 1
    return "".join(out)

def pad2_rotate(bitstr, key2):
    out = bitstr
    shifts = []
    for i, d in enumerate(map(int, key2), start=1):
        if not out:
            break
        shift = (d * i) % len(out)
        shifts.append(shift)
        out = out[shift:] + out[:shift]
    return out, shifts

def unpad2_rotate(bitstr, shifts):
    out = bitstr
    for shift in reversed(shifts):
        if shift:
            out = out[-shift:] + out[:-shift]
    return out
