
def prettyHex(input, size = 64):
    def hex2(v):
        if isinstance(input, int):
            s = hex(v)[2:]
        elif isinstance(input, str):
            if "0x" in input:
                s = v[2:]
            else:
                s = hex(int(input))[2:]
        elif isinstance(input, bytes):
            s = input.hex()
        else:
            raise Exception("Unknown input number type")
        return s if len(s) % 2 == 0 else '0' + s
    return "0x" + hex2(input).zfill(size)

def prettyAddressHex(input):
    return prettyHex(input, size = 40)

def prettyHashHex(input):
    return prettyHex(input, size = 64)

def prettyEvenHex(input):
    return prettyHex(input, size = 0)