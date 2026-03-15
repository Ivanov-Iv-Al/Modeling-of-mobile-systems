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


class Modulator:
    """
    Модулятор QPSK (QPSK - Quadrature Phase Shift Keying)
    Преобразует биты в комплексные символы согласно таблице:
    00 -> 0.707 + 0.707j
    01 -> 0.707 - 0.707j
    10 -> -0.707 + 0.707j
    11 -> -0.707 - 0.707j
    """
    
    # Таблица модуляции: словарь {биты: комплексный символ}
    MODULATION_TABLE = {
        '00': complex(0.707, 0.707),   # I = 0.707, Q = 0.707 (верхний правый)
        '01': complex(0.707, -0.707),  # I = 0.707, Q = -0.707 (нижний правый)
        '10': complex(-0.707, 0.707),  # I = -0.707, Q = 0.707 (верхний левый)
        '11': complex(-0.707, -0.707)  # I = -0.707, Q = -0.707 (нижний левый)
    }
    
    @staticmethod
    def modulate(bits):
        """
        Модуляция битового потока в комплексные символы
        
        Вход: строка битов (например, "01001110")
        Выход: список комплексных чисел (длина в 2 раза меньше)
        """
        if not bits:
            return []
        
        # Проверяем, что количество бит четное
        if len(bits) % 2 != 0:
            # Добавляем нулевой бит в конец для четности
            bits = bits + '0'
            print(f"Добавлен нулевой бит для четности. Новая длина: {len(bits)}")
        
        symbols = []
        
        # Берем биты парами
        for i in range(0, len(bits), 2):
            bit_pair = bits[i:i+2]
            # Получаем комплексный символ по таблице
            symbol = Modulator.MODULATION_TABLE[bit_pair]
            symbols.append(symbol)
        
        return symbols
    
    @staticmethod
    def print_constellation():
        """Выводит созвездие модуляции"""
        print("\nСозвездие QPSK модуляции:")
        print("Биты -> I (Re), Q (Im)")
        for bits, symbol in Modulator.MODULATION_TABLE.items():
            print(f"{bits} -> {symbol.real:.3f}, {symbol.imag:.3f}j")


class Demodulator:
    """
    Демодулятор QPSK
    Преобразует комплексные символы обратно в биты
    Использует правило областей декодирования:
    - Если I > 0 и Q > 0 -> 00
    - Если I > 0 и Q < 0 -> 01
    - Если I < 0 и Q > 0 -> 10
    - Если I < 0 и Q < 0 -> 11
    """
    
    @staticmethod
    def demodulate(symbols):
        """
        Демодуляция комплексных символов в битовый поток
        
        Вход: список комплексных чисел
        Выход: строка битов (длина в 2 раза больше)
        """
        if not symbols:
            return ""
        
        bits = []
        
        for symbol in symbols:
            # Определяем область по знакам реальной и мнимой частей
            if symbol.real >= 0 and symbol.imag >= 0:
                bits.append('00')  # Верхний правый квадрант
            elif symbol.real >= 0 and symbol.imag < 0:
                bits.append('01')  # Нижний правый квадрант
            elif symbol.real < 0 and symbol.imag >= 0:
                bits.append('10')  # Верхний левый квадрант
            else:  # real < 0 and imag < 0
                bits.append('11')  # Нижний левый квадрант
        
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
    """
    Добавляет шум к комплексным символам для демонстрации работы демодулятора
    
    Вход: список комплексных символов
    Выход: список комплексных символов с шумом
    """
    noisy_symbols = []
    for symbol in symbols:
        # Добавляем нормальный шум к реальной и мнимой частям
        noise_real = np.random.normal(0, noise_level)
        noise_imag = np.random.normal(0, noise_level)
        noisy_symbol = complex(symbol.real + noise_real, symbol.imag + noise_imag)
        noisy_symbols.append(noisy_symbol)
    
    return noisy_symbols


def main():
    msg = "Hello World. This is test message and no more"
    print(f"Исходное сообщение: {msg}\n")
    
    # Выбор количества бит для кодировки Хэмминга
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
    
    # 1. Символьное кодирование
    encoded = SignCoder.sign_encoder(msg)
    if not encoded:
        print("Ошибка кодирования")
        return
    
    print(f"Этап 1 - Символьное кодирование:")
    print(f"  Битовое представление: {len(encoded)} бит")
    print(f"  Первые 30 бит: {encoded[:30]}...")
    
    # 2. Кодирование Хэмминга
    hamming_coder = HammingCoder(k_bits)
    hamming_encoded = hamming_coder.encode(encoded)
    print(f"\nЭтап 2 - Кодирование Хэмминга ({k_bits} инф. бит):")
    print(f"  Закодировано: {len(hamming_encoded)} бит")
    print(f"  Первые 30 бит: {hamming_encoded[:30]}...")
    
    # 3. Перемежение
    interleaver = Interleaver(seed=42)
    interleaved = interleaver.interleave(hamming_encoded)
    print(f"\nЭтап 3 - Перемежение:")
    print(f"  После перемежения: {len(interleaved)} бит")
    print(f"  Первые 30 бит: {interleaved[:30]}...")
    
    # 4. Модуляция (НОВОЕ!)
    print(f"\nЭтап 4 - Модуляция QPSK:")
    print(f"  До модуляции: {len(interleaved)} бит")
    
    # Показываем таблицу модуляции
    Modulator.print_constellation()
    
    # Выполняем модуляцию
    modulated_symbols = Modulator.modulate(interleaved)
    print(f"\n  После модуляции: {len(modulated_symbols)} комплексных символов")
    print(f"  Первые 3 символа:")
    for i, sym in enumerate(modulated_symbols[:3]):
        print(f"    Символ {i+1}: I={sym.real:.3f}, Q={sym.imag:.3f}j")
    
    # 5. Канал с шумом (НОВОЕ!)
    print(f"\nЭтап 5 - Канал с шумом:")
    np.random.seed(42)  # Для воспроизводимости
    noisy_symbols = add_channel_noise(modulated_symbols, noise_level=0.2)
    print(f"  Добавлен шум (уровень 0.2)")
    print(f"  Первые 3 символа с шумом:")
    for i, sym in enumerate(noisy_symbols[:3]):
        print(f"    Символ {i+1}: I={sym.real:.3f}, Q={sym.imag:.3f}j")
    
    # 6. Демодуляция (НОВОЕ!)
    print(f"\nЭтап 6 - Демодуляция QPSK:")
    print(f"  До демодуляции: {len(noisy_symbols)} символов")
    
    # Демодулируем зашумленные символы
    demodulated_bits = Demodulator.demodulate(noisy_symbols)
    print(f"  После демодуляции: {len(demodulated_bits)} бит")
    print(f"  Первые 30 бит: {demodulated_bits[:30]}...")
    
    # Проверяем, совпадают ли биты до и после модуляции-демодуляции
    original_bits = interleaved
    match_count = sum(1 for i in range(min(len(original_bits), len(demodulated_bits))) 
                     if original_bits[i] == demodulated_bits[i])
    match_percent = (match_count / len(original_bits)) * 100
    print(f"\n  Совпадение бит до/после модуляции: {match_count}/{len(original_bits)} ({match_percent:.1f}%)")
    
    # 7. Деинтерливинг
    deinterleaver = Deinterleaver(interleaver)
    deinterleaved = deinterleaver.deinterleave(demodulated_bits)
    print(f"\nЭтап 7 - Деинтерливинг:")
    print(f"  После деинтерливинга: {len(deinterleaved)} бит")
    
    # 8. Декодирование Хэмминга
    hamming_decoded = hamming_coder.decode(deinterleaved)
    if not hamming_decoded:
        print("Ошибка декодирования Хэмминга")
        return
    
    print(f"\nЭтап 8 - Декодирование Хэмминга:")
    print(f"  После декодирования: {len(hamming_decoded)} бит")
    
    # 9. Символьное декодирование
    decoded = SignCoder.sign_decoder(hamming_decoded[:len(encoded)])
    
    print(f"\nЭтап 9 - Символьное декодирование:")
    print(f"  Результат: {decoded}")
    print(f"  Успех: {msg == decoded}")
    
    # Дополнительно: показываем, как работает демодулятор с разными областями
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ ДЕМОДУЛЯТОРА")
    print("="*50)
    
    # Тестовые символы в разных областях
    test_symbols = [
        complex(0.8, 0.8),   # Должен быть 00
        complex(0.6, -0.6),  # Должен быть 01
        complex(-0.7, 0.7),  # Должен быть 10
        complex(-0.5, -0.5), # Должен быть 11
        complex(0.2, 0.1),   # На границе, но I>0, Q>0 -> 00
        complex(-0.1, -0.3)  # I<0, Q<0 -> 11
    ]
    
    print("\nТестовые символы и их демодуляция:")
    for sym in test_symbols:
        bits = Demodulator.demodulate([sym])
        print(f"  Символ I={sym.real:+.3f}, Q={sym.imag:+.3f}j -> биты: {bits}")

if __name__ == "__main__":
    main()
