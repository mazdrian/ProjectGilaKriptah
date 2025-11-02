# steganography.py
# Fungsi steganografi LSB

from PIL import Image

def embed_text_in_image(input_path: str, output_path: str, text: str) -> bool:
    try:
        img = Image.open(input_path)
        img = img.convert('RGBA')
        pixels = list(img.getdata())
        data = text.encode('utf-8')
        length = len(data)
        length_bits = [int(b) for b in format(length, '032b')]
        data_bits = []
        for byte in data:
            data_bits.extend([int(b) for b in format(byte, '08b')])
        bits = length_bits + data_bits
        if len(bits) > len(pixels) * 3:
            return False
        new_pixels = []
        bi = 0
        for px in pixels:
            r, g, b, a = px
            nr = r
            ng = g
            nb = b
            if bi < len(bits):
                nr = (r & ~1) | bits[bi]; bi += 1
            if bi < len(bits):
                ng = (g & ~1) | bits[bi]; bi += 1
            if bi < len(bits):
                nb = (b & ~1) | bits[bi]; bi += 1
            new_pixels.append((nr, ng, nb, a))
        img.putdata(new_pixels)
        img.save(output_path, 'PNG')
        return True
    except Exception as e:
        print('embed error', e)
        return False

def extract_text_from_image(image_path: str) -> str | None:
    try:
        img = Image.open(image_path)
        img = img.convert('RGBA')
        pixels = list(img.getdata())
        bits = []
        for px in pixels:
            r, g, b, a = px
            bits.append(r & 1); bits.append(g & 1); bits.append(b & 1)
        length_bits = bits[:32]
        length = int(''.join(str(b) for b in length_bits), 2)
        needed = length * 8
        data_bits = bits[32:32 + needed]
        if len(data_bits) < needed:
            return None
        bytes_out = []
        for i in range(0, len(data_bits), 8):
            byte = data_bits[i:i+8]
            val = int(''.join(str(b) for b in byte), 2)
            bytes_out.append(val)
        return bytes(bytes_out).decode('utf-8', errors='replace')
    except Exception as e:
        print('extract error', e)
        return None
