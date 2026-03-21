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
        self.N = k_bits + 4
    
    def encode(self, bits):
        if not bits:
            return bits
        
        remainder = len(bits) % self.K
        if remainder:
            bits = bits + '0' * (self.K - remainder)
        
        encoded = []
        
        for i in range(0, len(bits), self.K):
            data = [int(b) for b in bits[i:i+self.K]]
            
            if self.K == 11:
                p1 = data[0] ^ data[1] ^ data[3] ^ data[4] ^ data[6] ^ data[8] ^ data[10]
                p2 = data[0] ^ data[2] ^ data[3] ^ data[5] ^ data[6] ^ data[9] ^ data[10]
                p3 = data[1] ^ data[2] ^ data[3] ^ data[7] ^ data[8] ^ data[9] ^ data[10]
                p4 = data[4] ^ data[5] ^ data[6] ^ data[7] ^ data[8] ^ data[9] ^ data[10]
            else:
                p1 = data[0] ^ data[1] if len(data) > 1 else data[0]
                p2 = data[2] ^ data[3] if len(data) > 3 else 0
                p3 = data[4] ^ data[5] if len(data) > 5 else 0
                p4 = data[6] ^ data[7] if len(data) > 7 else 0
            
            codeword = [0] * self.N
            data_idx = 0
            for pos in range(self.N):
                if pos+1 not in [1, 2, 4, 8]:
                    if data_idx < len(data):
                        codeword[pos] = data[data_idx]
                        data_idx += 1
            
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


class Modulator:
    @staticmethod
    def modulate(bits):
        if not bits:
            return []
        
        if len(bits) % 2 != 0:
            bits = bits + '0'
        
        symbols = []
        for i in range(0, len(bits), 2):
            bit_pair = bits[i:i+2]
            
            if bit_pair == '00':
                symbols.append(complex(0.707, 0.707))
            elif bit_pair == '01':
                symbols.append(complex(0.707, -0.707))
            elif bit_pair == '10':
                symbols.append(complex(-0.707, 0.707))
            else:
                symbols.append(complex(-0.707, -0.707))
        
        return symbols


class Demodulator:
    @staticmethod
    def demodulate(symbols):
        if not symbols:
            return ""
        
        bits = []
        for symbol in symbols:
            if symbol.real > 0 and symbol.imag > 0:
                bits.append('00')
            elif symbol.real > 0 and symbol.imag < 0:
                bits.append('01')
            elif symbol.real < 0 and symbol.imag > 0:
                bits.append('10')
            else:
                bits.append('11')
        
        return ''.join(bits)


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


def add_channel_noise(symbols, noise_level=0.1):
    noisy_symbols = []
    for symbol in symbols:
        noise_real = np.random.normal(0, noise_level)
        noise_imag = np.random.normal(0, noise_level)
        noisy_symbols.append(complex(symbol.real + noise_real, symbol.imag + noise_imag))
    return noisy_symbols


def main():
    msg = "Hello World. This is test message and no more"
    print(f"Исходное сообщение: {msg}\n")
    
    print("Доступные варианты для кода Хэмминга: 4, 5, 6, 7, 8, 9, 10, 11")
    try:
        k_bits = int(input("Введите количество информационных бит (по умолчанию 11): ") or "11")
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
    
    print(f" Символьное кодирование:")
    print(f"  Битовое представление: {len(encoded)} бит")
    print(f"  Первые 30 бит: {encoded[:30]}...")
    
    hamming_coder = HammingCoder(k_bits)
    hamming_encoded = hamming_coder.encode(encoded)
    print(f"\nКодирование Хэмминга ({k_bits} инф. бит):")
    print(f"  Закодировано: {len(hamming_encoded)} бит")
    print(f"  Первые 30 бит: {hamming_encoded[:30]}...")
    
    interleaver = Interleaver(seed=42)
    interleaved = interleaver.interleave(hamming_encoded)
    print(f"\nПеремежение:")
    print(f"  После перемежения: {len(interleaved)} бит")
    print(f"  Первые 30 бит: {interleaved[:30]}...")
    
    print(f"\nQPSK модуляция:")
    print(f"  До модуляции: {len(interleaved)} бит")
    modulated_symbols = Modulator.modulate(interleaved)
    print(f"  После модуляции: {len(modulated_symbols)} символов")
    print(f"  Первые 3 символа:")
    for i, sym in enumerate(modulated_symbols[:3]):
        print(f"    Символ {i+1}: I={sym.real:.3f}, Q={sym.imag:.3f}j")
    
    print(f"\nКанал связи (добавление шума):")
    np.random.seed(42)
    noisy_symbols = add_channel_noise(modulated_symbols, noise_level=0.2)
    print(f"  Добавлен шум с уровнем 0.2")
    print(f"  Первые 3 символа после шума:")
    for i, sym in enumerate(noisy_symbols[:3]):
        print(f"    Символ {i+1}: I={sym.real:.3f}, Q={sym.imag:.3f}j")
    
    print(f"\nQPSK демодуляция:")
    print(f"  До демодуляции: {len(noisy_symbols)} символов")
    demodulated_bits = Demodulator.demodulate(noisy_symbols)
    print(f"  После демодуляции: {len(demodulated_bits)} бит")
    print(f"  Первые 30 бит: {demodulated_bits[:30]}...")
    
    correct = sum(1 for i in range(len(interleaved)) if interleaved[i] == demodulated_bits[i])
    print(f"  Совпадение бит: {correct}/{len(interleaved)} ({correct/len(interleaved)*100:.1f}%)")
    
    deinterleaver = Deinterleaver(interleaver)
    deinterleaved = deinterleaver.deinterleave(demodulated_bits)
    print(f"\nДеинтерливинг:")
    print(f"  После деинтерливинга: {len(deinterleaved)} бит")
    
    hamming_decoded = hamming_coder.decode(deinterleaved)
    if not hamming_decoded:
        print("Ошибка декодирования Хэмминга")
        return
    
    print(f"\nДекодирование Хэмминга:")
    print(f"  После декодирования: {len(hamming_decoded)} бит")
    
    decoded = SignCoder.sign_decoder(hamming_decoded[:len(encoded)])
    

main()
