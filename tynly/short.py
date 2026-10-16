# TYNLy - Day 1: Base62 logic

CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def encode(num):
    if num == 0:
        return CHARS[0]
    result = ""
    while num > 0:
        result = CHARS[num % 62] + result
        num //= 62
    return result

def decode(s):
    num = 0
    for c in s:
        num = num * 62 + CHARS.index(c)
    return num

counter = 1000

def generate_code():
    global counter
    counter += 1
    return encode(counter)

# Test
if __name__ == "__main__":
    for i in [0, 1, 61, 62, 100, 10000, 999999]:
        code = encode(i)
        back = decode(code)
        print(f"{i} -> {code} -> {back}")

