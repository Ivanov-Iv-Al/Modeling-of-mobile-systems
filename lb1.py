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
    def __init__(self, k_bits):
        self.K = k_bits
        self.N = k_bits + 4  # Добавляем 4 проверочных бита
    
    def encode(self, bits):
        if not bits:
            return bits
        
        remainder = len(bits) % self.K
        if remainder:
            bits = bits + '0' * (self.K - remainder)
        
        encoded = []
        
        for i in range(0, len(bits), self.K):
            data = [int(b) for b in bits[i:i+self.K]]
            
            # Расчет проверочных бит для (15,11) кода Хэмминга
            # Используем все информационные биты для расчета
            if self.K == 11:
                p1 = data[0] ^ data[1] ^ data[3] ^ data[4] ^ data[6] ^ data[8] ^ data[10]
                p2 = data[0] ^ data[2] ^ data[3] ^ data[5] ^ data[6] ^ data[9] ^ data[10]
                p3 = data[1] ^ data[2] ^ data[3] ^ data[7] ^ data[8] ^ data[9] ^ data[10]
                p4 = data[4] ^ data[5] ^ data[6] ^ data[7] ^ data[8] ^ data[9] ^ data[10]
            else:
                # Для других значений используем простой XOR всех бит для каждого проверочного
                # Это упрощенный подход для демонстрации
                p1 = data[0] ^ data[1] if len(data) > 1 else data[0]
                p2 = data[2] ^ data[3] if len(data) > 3 else 0
                p3 = data[4] ^ data[5] if len(data) > 5 else 0
                p4 = data[6] ^ data[7] if len(data) > 7 else 0
            
            codeword = [0] * self.N
            data_idx = 0
            for pos in range(self.N):
                if pos+1 not in [1, 2, 4, 8]:  # Позиции для информационных бит
                    if data_idx < len(data):
                        codeword[pos] = data[data_idx]
                        data_idx += 1
            
            # Вставляем проверочные биты
            if pos < self.N:
                codeword[0] = p1
                codeword[1] = p2
                codeword[3] = p3
                codeword[7] = p4
            
            encoded.extend([str(b) for b in codeword])
        
        return ''.join(encoded)
    
    def decode(self, bits):
        if not bits or len(bits) % self.N != 0:
            return bits if not bits else None
        
        decoded = []
        
        for i in range(0, len(bits), self.N):
            r = [int(b) for b in bits[i:i+self.N]]
            
            p1, p2, p3, p4 = r[0], r[1], r[3], r[7]
            
            d = []
            for pos in range(self.N):
                if pos+1 not in [1, 2, 4, 8]:
                    d.append(r[pos])
            
            # Поиск и исправление ошибки
            if self.K == 11:
                s1 = p1 ^ d[0] ^ d[1] ^ d[3] ^ d[4] ^ d[6] ^ d[8] ^ d[10]
                s2 = p2 ^ d[0] ^ d[2] ^ d[3] ^ d[5] ^ d[6] ^ d[9] ^ d[10]
                s3 = p3 ^ d[1] ^ d[2] ^ d[3] ^ d[7] ^ d[8] ^ d[9] ^ d[10]
                s4 = p4 ^ d[4] ^ d[5] ^ d[6] ^ d[7] ^ d[8] ^ d[9] ^ d[10]
                
                syndrome = (s4 << 3) | (s3 << 2) | (s1 << 1) | s2
                
                if syndrome:
                    pos = syndrome - 1
                    if 0 <= pos < self.N:
                        r[pos] ^= 1
                        d = []
                        for p in range(self.N):
                            if p+1 not in [1, 2, 4, 8]:
                                d.append(r[p])
            
            decoded.extend([str(b) for b in d])
        
        return ''.join(decoded)


class Interleaver:
    def __init__(self, seed=42):
        self.seed = seed
        self.permutation = None
    
    def interleave(self, bits):
        if not bits:
            return bits
        
        np.random.seed(self.seed)
        n = len(bits)
        self.permutation = np.random.permutation(n)
        
        interleaved = ['0'] * n
        for i, pos in enumerate(self.permutation):
            interleaved[pos] = bits[i]
        
        return ''.join(interleaved)


class Deinterleaver:
    def __init__(self, interleaver):
        self.permutation = interleaver.permutation
    
    def deinterleave(self, bits):
        if not bits or self.permutation is None:
            return bits
        
        n = len(bits)
        deinterleaved = ['0'] * n
        
        for i, pos in enumerate(self.permutation):
            deinterleaved[i] = bits[pos]
        
        return ''.join(deinterleaved)


def main():
    msg = "Hello World. This is test message and no more"
    print(f"Исходное: {msg}\n")
    
    # Выбор количества бит для кодировки Хэмминга
    print("Доступные варианты: 4, 5, 6, 7, 8, 9, 10, 11")
    try:
        k_bits = int(input("Введите количество информационных бит для кода Хэмминга (по умолчанию 11): ") or "11")
        if k_bits not in [4, 5, 6, 7, 8, 9, 10, 11]:
            print("Неверное значение. Используется значение по умолчанию (11)")
            k_bits = 11
    except ValueError:
        print("Ошибка ввода. Используется значение по умолчанию (11)")
        k_bits = 11
    
    print(f"Выбрано: {k_bits} информационных бит\n")
    
    encoded = SignCoder.sign_encoder(msg)
    if not encoded:
        print("Ошибка кодирования")
        return
    
    print(f"После символьного: {len(encoded)} бит")
    
    hamming_coder = HammingCoder(k_bits)
    hamming_encoded = hamming_coder.encode(encoded)
    print(f"После Хэмминга ({k_bits} инф. бит): {len(hamming_encoded)} бит")
    
    interleaver = Interleaver(seed=42)
    interleaved = interleaver.interleave(hamming_encoded)
    print(f"После перемежения: {len(interleaved)} бит")
    
    np.random.seed(42)
    received = list(interleaved)
    errors = 0
    for i in range(len(received)):
        if np.random.random() < 0.05:
            received[i] = '1' if received[i] == '0' else '0'
            errors += 1
    
    print(f"Ошибок в канале: {errors}")
    
    deinterleaver = Deinterleaver(interleaver)
    deinterleaved = deinterleaver.deinterleave(''.join(received))
    
    hamming_decoded = hamming_coder.decode(deinterleaved)
    if not hamming_decoded:
        print("Ошибка декодирования")
        return
    
    decoded = SignCoder.sign_decoder(hamming_decoded[:len(encoded)])
    
    print(f"\nРезультат: {decoded}")
    print(f"Успех: {msg == decoded}")

main()
