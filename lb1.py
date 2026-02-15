import numpy as np

class SignCoder:
    BITS = 6
    
    @staticmethod
    def sign_encoder(text):
        if not text or len(text) < 30 or len(text) > 100:
            return None
        
        bits = []
        for c in text:
            if 'A' <= c <= 'Z':
                code = ord(c) - ord('A')
            elif 'a' <= c <= 'z':
                code = ord(c) - ord('a') + 26
            elif '0' <= c <= '9':
                code = ord(c) - ord('0') + 52
            elif c == ' ':
                code = 62
            elif c == '.':
                code = 63
            else:
                return None
            
            bits.append(format(code, '06b'))
        
        return ''.join(bits)
    
    @staticmethod
    def sign_decoder(bits):
        if not bits or len(bits) % 6 != 0:
            return None
        
        text = []
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .'
        
        for i in range(0, len(bits), 6):
            code = int(bits[i:i+6], 2)
            if code < 64:
                text.append(chars[code])
            else:
                return None
        
        return ''.join(text)


class HammingCoder:
    K = 11
    N = 15
    
    @staticmethod
    def encode(bits):
        if not bits:
            return bits
        
        remainder = len(bits) % 11
        if remainder:
            bits = bits + '0' * (11 - remainder)
        
        encoded = []
        
        for i in range(0, len(bits), 11):
            data = [int(b) for b in bits[i:i+11]]
            
            p1 = data[0] ^ data[1] ^ data[3] ^ data[4] ^ data[6] ^ data[8] ^ data[10]
            p2 = data[0] ^ data[2] ^ data[3] ^ data[5] ^ data[6] ^ data[9] ^ data[10]
            p3 = data[1] ^ data[2] ^ data[3] ^ data[7] ^ data[8] ^ data[9] ^ data[10]
            p4 = data[4] ^ data[5] ^ data[6] ^ data[7] ^ data[8] ^ data[9] ^ data[10]
            
            codeword = [0] * 15
            data_idx = 0
            for pos in range(15):
                if pos+1 not in [1, 2, 4, 8]:
                    codeword[pos] = data[data_idx]
                    data_idx += 1
            
            codeword[0] = p1
            codeword[1] = p2
            codeword[3] = p3
            codeword[7] = p4
            
            encoded.extend([str(b) for b in codeword])
        
        return ''.join(encoded)
    
    @staticmethod
    def decode(bits):
        if not bits or len(bits) % 15 != 0:
            return bits if not bits else None
        
        decoded = []
        
        for i in range(0, len(bits), 15):
            r = [int(b) for b in bits[i:i+15]]
            
            p1, p2, p3, p4 = r[0], r[1], r[3], r[7]
            
            d = []
            for pos in range(15):
                if pos+1 not in [1, 2, 4, 8]:
                    d.append(r[pos])
            
            s1 = p1 ^ d[0] ^ d[1] ^ d[3] ^ d[4] ^ d[6] ^ d[8] ^ d[10]
            s2 = p2 ^ d[0] ^ d[2] ^ d[3] ^ d[5] ^ d[6] ^ d[9] ^ d[10]
            s3 = p3 ^ d[1] ^ d[2] ^ d[3] ^ d[7] ^ d[8] ^ d[9] ^ d[10]
            s4 = p4 ^ d[4] ^ d[5] ^ d[6] ^ d[7] ^ d[8] ^ d[9] ^ d[10]
            
            syndrome = (s4 << 3) | (s3 << 2) | (s2 << 1) | s1
            
            if syndrome:
                pos = syndrome - 1
                if 0 <= pos < 15:
                    r[pos] ^= 1
                    d = []
                    for p in range(15):
                        if p+1 not in [1, 2, 4, 8]:
                            d.append(r[p])
            
            decoded.extend([str(b) for b in d])
        
        return ''.join(decoded)


def main():
    msg = "Hello World. This is test message and no more"
    print(f"Исходное: {msg}\n")
    
    encoded = SignCoder.sign_encoder(msg)
    if not encoded:
        print("Ошибка кодирования")
        return
    
    print(f"После символьного: {len(encoded)} бит")
    
    hamming_encoded = HammingCoder.encode(encoded)
    print(f"После Хэмминга: {len(hamming_encoded)} бит")
    
    np.random.seed(42)
    received = list(hamming_encoded)
    errors = 0
    for i in range(len(received)):
        if np.random.random() < 0.05:
            received[i] = '1' if received[i] == '0' else '0'
            errors += 1
    
    print(f"Ошибок в канале: {errors}")
    
    hamming_decoded = HammingCoder.decode(''.join(received))
    if not hamming_decoded:
        print("Ошибка декодирования")
        return
    
    decoded = SignCoder.sign_decoder(hamming_decoded[:len(encoded)])
    
    print(f"Результат: {decoded}")
    print(f"Успех: {msg == decoded}")

main()
