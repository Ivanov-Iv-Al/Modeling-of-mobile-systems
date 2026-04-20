import numpy as np

class SignCoder:
    BITS = 8

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

            bits.append(format(code, '08b'))

        return ''.join(bits)

    def sign_decoder(bits):
        if not bits or len(bits) % 8 != 0:
            return None

        text = []
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .'

        for i in range(0, len(bits), 8):
            code = int(bits[i:i + 8], 2)
            if code < 64:
                text.append(chars[code])
            else:
                return None

        return ''.join(text)

class HammingCoder:
    def __init__(self, k_bits):
        self.K = k_bits
        self.m = 0
        while (2**self.m) < (self.K + self.m + 1):
            self.m += 1
        self.N = self.K + self.m

    def encode(self, bits):
        if not bits: return bits
        remainder = len(bits) % self.K
        if remainder:
            bits = bits + '0' * (self.K - remainder)
        encoded = []
        for i in range(0, len(bits), self.K):
            data = [int(b) for b in bits[i:i + self.K]]
            codeword = [0] * self.N
            data_idx = 0
            for pos in range(1, self.N + 1):
                if not (pos & (pos - 1) == 0):
                    codeword[pos-1] = data[data_idx]
                    data_idx += 1
            for j in range(self.m):
                p_pos = 2**j
                parity = 0
                for pos in range(1, self.N + 1):
                    if pos & p_pos:
                        parity ^= codeword[pos-1]
                codeword[p_pos-1] = parity
            encoded.extend([str(b) for b in codeword])
        return ''.join(encoded)

    def decode(self, bits):
        if not bits or len(bits) % self.N != 0:
            return bits if not bits else None
        decoded = []
        for i in range(0, len(bits), self.N):
            r = [int(b) for b in bits[i:i + self.N]]
            syndrome = 0
            for j in range(self.m):
                p_pos = 2**j
                parity = 0
                for pos in range(1, self.N + 1):
                    if pos & p_pos:
                        parity ^= r[pos-1]
                if parity:
                    syndrome += p_pos
            if 0 < syndrome <= self.N:
                r[syndrome-1] ^= 1
            for pos in range(1, self.N + 1):
                if not (pos & (pos - 1) == 0):
                    decoded.append(str(r[pos-1]))
        return ''.join(decoded)

class Modulator:
    def modulate(bits):
        if not bits:
            return []

        if len(bits) % 2 != 0:
            bits = bits + '0'

        symbols = []
        for i in range(0, len(bits), 2):
            bit_pair = bits[i:i + 2]

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


# ====================== OFDM модулятор / демодулятор ======================
class OfdmModulator:
    def __init__(self, n_subcarriers=64, cp_len=16):
        self.n_subcarriers = n_subcarriers
        self.cp_len = cp_len
        self.original_len = None

    def modulate(self, symbols):
        """Преобразует список комплексных QPSK символов в OFDM сигнал (IFFT + CP)."""
        if not symbols:
            return []
        self.original_len = len(symbols)
        # Дополнение нулями до кратности n_subcarriers
        n_sym = len(symbols)
        pad_len = (self.n_subcarriers - (n_sym % self.n_subcarriers)) % self.n_subcarriers
        if pad_len > 0:
            symbols = np.append(symbols, [0+0j] * pad_len)
        # Разбиваем на блоки
        symbols = np.array(symbols)
        blocks = symbols.reshape(-1, self.n_subcarriers)
        ofdm_signal = []
        for block in blocks:
            # IFFT
            ifft_block = np.fft.ifft(block, self.n_subcarriers)
            # Добавление циклического префикса
            cp = ifft_block[-self.cp_len:]
            ofdm_signal.extend(np.concatenate([cp, ifft_block]))
        return np.array(ofdm_signal)


class OfdmDemodulator:
    def __init__(self, modulator):
        self.n_subcarriers = modulator.n_subcarriers
        self.cp_len = modulator.cp_len
        self.original_len = modulator.original_len

    def demodulate(self, ofdm_signal):
        """Восстанавливает QPSK символы из OFDM сигнала (удаление CP, FFT)."""
        if len(ofdm_signal) == 0:
            return []
        block_len = self.n_subcarriers + self.cp_len
        n_blocks = len(ofdm_signal) // block_len
        if len(ofdm_signal) % block_len != 0:
            # Обрезаем лишнее
            ofdm_signal = ofdm_signal[:n_blocks * block_len]
        symbols = []
        for i in range(n_blocks):
            block = ofdm_signal[i*block_len : (i+1)*block_len]
            # Удаление CP
            data_part = block[self.cp_len:]
            # FFT
            fft_block = np.fft.fft(data_part, self.n_subcarriers)
            symbols.extend(fft_block)
        # Обрезаем до исходной длины (убираем добавленные нули)
        if self.original_len is not None:
            symbols = symbols[:self.original_len]
        return symbols


# ====================== Многолучевой канал с АБГШ ======================
class MultipathChannel:
    def __init__(self, fc=2.4e9, bandwidth=1e6, num_paths=3, n0_db=-100):
        """
        fc: несущая частота (Гц)
        bandwidth: полоса сигнала (Гц)
        num_paths: количество лучей (Nl)
        n0_db: спектральная плотность мощности шума (дБ)
        """
        self.fc = fc
        self.bandwidth = bandwidth
        self.num_paths = num_paths
        self.n0_db = n0_db
        self.c = 3e8          # скорость света
        self.Ts = 1.0 / bandwidth   # длительность отсчета

    def propagate(self, tx_signal):
        """
        Вход: комплексный сигнал (массив numpy)
        Выход: сигнал после многолучевого канала + АБГШ (обрезанный до длины входа)
        """
        if len(tx_signal) == 0:
            return tx_signal

        # Генерация случайных расстояний для каждого луча (10...500 м)
        distances = np.random.uniform(10, 500, self.num_paths)
        min_dist = np.min(distances)
        # Задержки (в отсчётах) относительно прямого луча
        delays = []
        for d in distances:
            tau = (d - min_dist) / (self.c * self.Ts)
            delays.append(int(round(tau)))   # округление до целого
        # Коэффициенты ослабления
        gains = []
        for d in distances:
            gain = self.c / (4 * np.pi * d * self.fc)
            gains.append(gain)

        max_delay = max(delays)
        L = len(tx_signal)
        # Инициализация результирующего сигнала (нулевой)
        rx_sum = np.zeros(L + max_delay, dtype=complex)

        # Наложение всех лучей
        for i in range(self.num_paths):
            shift = delays[i]
            gain = gains[i]
            # Сдвиг и ослабление
            shifted = np.zeros(L + shift, dtype=complex)
            shifted[shift:] = tx_signal * gain
            # Суммирование с учётом разной длины
            if len(shifted) > len(rx_sum):
                shifted = shifted[:len(rx_sum)]
            rx_sum[:len(shifted)] += shifted

        # Обрезаем до длины L (исходная длина сигнала)
        rx_signal = rx_sum[:L]

        # Добавление АБГШ
        # Переводим N0 из дБ в линейную величину
        n0_linear = 10 ** (self.n0_db / 10.0)
        # Мощность шума в полосе: N0 * B
        noise_power = n0_linear * self.bandwidth
        # Дисперсия на комплексную размерность: noise_power / 2
        noise_std = np.sqrt(noise_power / 2.0)
        noise = noise_std * (np.random.randn(L) + 1j * np.random.randn(L))
        rx_signal += noise

        return rx_signal


# ====================== Основная программа ======================
def main():
    msg = "Hello World. This is test message and no more..."
    print(f"Исходное сообщение: {msg}\n")
    print(f"Исходное сообщение(длительность): {len(msg) * 8}\n")

    try:
        user_input = input("Введите количество информационных бит для кода Хэмминга: ")
        k_bits = int(user_input) if user_input else 11
    except ValueError:
        print("Ошибка ввода, используется 11")
        k_bits = 11

    # ---- Символьное кодирование ----
    encoded = SignCoder.sign_encoder(msg)
    if not encoded:
        print("Ошибка кодирования")
        return
    print(f"Символьное кодирование:")
    print(f"  Битовое представление: {len(encoded)} бит")
    print(f"  Первые 30 бит: {encoded[:30]}...")

    # ---- Код Хэмминга ----
    hamming_coder = HammingCoder(k_bits)
    hamming_encoded = hamming_coder.encode(encoded)
    print(f"\nКодирование Хэмминга ({k_bits} инф. бит):")
    print(f"  Закодировано: {len(hamming_encoded)} бит")
    print(f"  Первые 30 бит: {hamming_encoded[:30]}...")

    # ---- Перемежение ----
    interleaver = Interleaver(seed=42)
    interleaved = interleaver.interleave(hamming_encoded)
    print(f"\nПеремежение:")
    print(f"  После перемежения: {len(interleaved)} бит")
    print(f"  Первые 10 бит: {interleaved[:10]}")
    print(f"  Первые 10 бит до перемежения: {hamming_encoded[:10]}")

    # ---- QPSK модуляция ----
    print(f"\nQPSK модуляция:")
    qpsk_symbols = Modulator.modulate(interleaved)
    print(f"  До модуляции: {len(interleaved)} бит")
    print(f"  После модуляции: {len(qpsk_symbols)} символов")

    # ====================== НОВЫЙ БЛОК: OFDM ======================
    # Параметры OFDM (можно изменить при необходимости)
    N_SUBCARRIERS = 64
    CP_LEN = 16
    ofdm_mod = OfdmModulator(n_subcarriers=N_SUBCARRIERS, cp_len=CP_LEN)
    ofdm_signal = ofdm_mod.modulate(qpsk_symbols)
    print(f"\nOFDM модуляция:")
    print(f"  Символов на входе: {len(qpsk_symbols)}")
    print(f"  OFDM отсчётов на выходе (с CP): {len(ofdm_signal)}")

    # ---- Параметры многолучевого канала ----
    try:
        nl_input = input("Введите количество лучей (Nl) [по умолчанию 3]: ")
        num_paths = int(nl_input) if nl_input else 3
        n0_input = input("Введите мощность АБГШ (N0, дБ) [по умолчанию -100]: ")
        n0_db = float(n0_input) if n0_input else -100.0
    except ValueError:
        print("Ошибка ввода, используются значения по умолчанию: Nl=3, N0=-100 дБ")
        num_paths = 3
        n0_db = -100.0

    # Константы канала (вариант задания)
    FC = 2.4e9          # несущая частота, Гц
    BANDWIDTH = 1e6     # полоса сигнала, Гц

    channel = MultipathChannel(fc=FC, bandwidth=BANDWIDTH,
                               num_paths=num_paths, n0_db=n0_db)
    # Передача через многолучевой канал с шумом
    received_signal = channel.propagate(ofdm_signal)
    print(f"\nМноголучевой канал + АБГШ:")
    print(f"  Количество лучей: {num_paths}")
    print(f"  N0 = {n0_db} дБ")
    print(f"  Длина принятого сигнала: {len(received_signal)} отсчётов")

    # ---- OFDM демодуляция ----
    ofdm_demod = OfdmDemodulator(ofdm_mod)
    recovered_qpsk = ofdm_demod.demodulate(received_signal)
    print(f"\nOFDM демодуляция:")
    print(f"  Восстановлено QPSK символов: {len(recovered_qpsk)} (ожидалось {len(qpsk_symbols)})")

    # ---- QPSK демодуляция ----
    demodulated_bits = Demodulator.demodulate(recovered_qpsk)
    print(f"\nQPSK демодуляция:")
    print(f"  После демодуляции: {len(demodulated_bits)} бит")
    print(f"  Первые 30 бит: {demodulated_bits[:30]}...")

    # Сравнение с исходными битами после перемежения (без учёта ошибок OFDM)
    correct = sum(1 for i in range(len(interleaved)) if i < len(demodulated_bits) and interleaved[i] == demodulated_bits[i])
    print(f"  Совпадение бит (до деперемежения): {correct}/{len(interleaved)}")

    # ---- Деиеремежение ----
    deinterleaver = Deinterleaver(interleaver)
    deinterleaved = deinterleaver.deinterleave(demodulated_bits)
    print(f"\nДеинтерливинг:")
    print(f"  После деинтерливинга: {len(deinterleaved)} бит")

    # ---- Декодирование Хэмминга ----
    hamming_decoded = hamming_coder.decode(deinterleaved)
    if not hamming_decoded:
        print("Ошибка декодирования Хэмминга")
        return
    print(f"\nДекодирование Хэмминга:")
    print(f"  После декодирования: {len(hamming_decoded)} бит")

    # ---- Символьное декодирование ----
    decoded = SignCoder.sign_decoder(hamming_decoded[:len(encoded)])
    print(f"\nПолученное сообщение: {decoded}")

if __name__ == "__main__":
    main()   r[syndrome - 1] ^= 1
            
            data_bits = []
            for pos in range(1, self.N + 1):
                if pos not in parity_positions:
                    data_bits.append(str(r[pos - 1]))
            
            decoded.extend(data_bits)
        
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
    
    print(f"Этап 1 - Символьное кодирование:")
    print(f"  Сообщение: {msg}")
    print(f"  Битовое представление: {len(encoded)} бит")
    print(f"  Первые 30 бит: {encoded[:30]}...")
    
    hamming_coder = HammingCoder(k_bits)
    print(f"\nАвтоматический расчет для кода Хэмминга:")
    print(f"  Информационных бит (K): {hamming_coder.K}")
    print(f"  Проверочных бит (R): {hamming_coder.R}")
    print(f"  Общая длина блока (N = K+R): {hamming_coder.N}")
    print(f"  Проверочные биты на позициях: {hamming_coder.get_parity_positions(hamming_coder.N)}")
    
    hamming_encoded = hamming_coder.encode(encoded)
    print(f"\nЭтап 2 - Кодирование Хэмминга:")
    print(f"  Сообщение: {msg}")
    print(f"  Закодировано: {len(hamming_encoded)} бит")
    print(f"  Первые 30 бит: {hamming_encoded[:30]}...")
    
    interleaver = Interleaver(seed=42)
    interleaved = interleaver.interleave(hamming_encoded)
    print(f"\nЭтап 3 - Перемежение:")
    print(f"  Сообщение: {msg}")
    print(f"  После перемежения: {len(interleaved)} бит")
    print(f"  Первые 30 бит: {interleaved[:30]}...")
    
    print(f"\nЭтап 4 - QPSK модуляция:")
    print(f"  Сообщение: {msg}")
    print(f"  До модуляции: {len(interleaved)} бит")
    modulated_symbols = Modulator.modulate(interleaved)
    print(f"  После модуляции: {len(modulated_symbols)} символов")
    print(f"  Первые 3 символа:")
    for i, sym in enumerate(modulated_symbols[:3]):
        print(f"    Символ {i+1}: I={sym.real:.3f}, Q={sym.imag:.3f}j")
    
    print(f"\nЭтап 5 - Канал связи (добавление шума):")
    print(f"  Сообщение: {msg}")
    np.random.seed(42)
    noisy_symbols = add_channel_noise(modulated_symbols, noise_level=0.2)
    print(f"  Добавлен шум с уровнем 0.2")
    print(f"  Первые 3 символа после шума:")
    for i, sym in enumerate(noisy_symbols[:3]):
        print(f"    Символ {i+1}: I={sym.real:.3f}, Q={sym.imag:.3f}j")
    
    print(f"\nЭтап 6 - QPSK демодуляция:")
    print(f"  Сообщение: {msg}")
    print(f"  До демодуляции: {len(noisy_symbols)} символов")
    demodulated_bits = Demodulator.demodulate(noisy_symbols)
    print(f"  После демодуляции: {len(demodulated_bits)} бит")
    print(f"  Первые 30 бит: {demodulated_bits[:30]}...")
    
    correct = sum(1 for i in range(len(interleaved)) if interleaved[i] == demodulated_bits[i])
    print(f"  Совпадение бит: {correct}/{len(interleaved)} ({correct/len(interleaved)*100:.1f}%)")
    
    deinterleaver = Deinterleaver(interleaver)
    deinterleaved = deinterleaver.deinterleave(demodulated_bits)
    print(f"\nЭтап 7 - Деинтерливинг:")
    print(f"  Сообщение: {msg}")
    print(f"  После деинтерливинга: {len(deinterleaved)} бит")
    
    hamming_decoded = hamming_coder.decode(deinterleaved)
    if not hamming_decoded:
        print("Ошибка декодирования Хэмминга")
        return
    
    print(f"\nЭтап 8 - Декодирование Хэмминга:")
    print(f"  Сообщение: {msg}")
    print(f"  После декодирования: {len(hamming_decoded)} бит")
    
    decoded = SignCoder.sign_decoder(hamming_decoded[:len(encoded)])
    
    print(f"\nЭтап 9 - Символьное декодирование:")
    print(f"  Исходное сообщение: {msg}")
    print(f"  Декодированное сообщение: {decoded}")
    print(f"  Успех: {msg == decoded}")

if __name__ == "__main__":
    main()
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
    def __init__(self, chunk_length=8):
        self.CHUNK_LENGTH = chunk_length
        self.CHECK_BITS = [i for i in range(1, chunk_length + 1) if not i & (i - 1)]
        self.CODEWORD_LENGTH = chunk_length + len(self.CHECK_BITS)
    
    def _get_check_bits_data(self, value_bin):
        check_bits_count_map = {k: 0 for k in self.CHECK_BITS}
        for index, value in enumerate(value_bin, 1):
            if int(value):
                bin_char_list = list(bin(index)[2:].zfill(8))
                bin_char_list.reverse()
                for degree in [2 ** int(i) for i, value in enumerate(bin_char_list) if int(value)]:
                    if degree in check_bits_count_map:
                        check_bits_count_map[degree] += 1
        check_bits_value_map = {}
        for check_bit, count in check_bits_count_map.items():
            check_bits_value_map[check_bit] = 0 if not count % 2 else 1
        return check_bits_value_map
    
    def _set_empty_check_bits(self, value_bin):
        for bit in self.CHECK_BITS:
            value_bin = value_bin[:bit - 1] + '0' + value_bin[bit - 1:]
        return value_bin
    
    def _set_check_bits(self, value_bin):
        value_bin = self._set_empty_check_bits(value_bin)
        check_bits_data = self._get_check_bits_data(value_bin)
        for check_bit, bit_value in check_bits_data.items():
            value_bin = value_bin[:check_bit - 1] + str(bit_value) + value_bin[check_bit:]
        return value_bin
    
    def _get_check_bits(self, value_bin):
        check_bits = {}
        for index, value in enumerate(value_bin, 1):
            if index in self.CHECK_BITS:
                check_bits[index] = int(value)
        return check_bits
    
    def _exclude_check_bits(self, value_bin):
        clean_value_bin = ''
        for index, char_bin in enumerate(list(value_bin), 1):
            if index not in self.CHECK_BITS:
                clean_value_bin += char_bin
        return clean_value_bin
    
    def _check_and_fix_error(self, encoded_chunk):
        check_bits_encoded = self._get_check_bits(encoded_chunk)
        check_item = self._exclude_check_bits(encoded_chunk)
        check_item = self._set_check_bits(check_item)
        check_bits = self._get_check_bits(check_item)
        
        if check_bits_encoded != check_bits:
            invalid_bits = []
            for check_bit_encoded, value in check_bits_encoded.items():
                if check_bits[check_bit_encoded] != value:
                    invalid_bits.append(check_bit_encoded)
            num_bit = sum(invalid_bits)
            if 1 <= num_bit <= len(encoded_chunk):
                encoded_chunk = encoded_chunk[:num_bit - 1] + str(int(encoded_chunk[num_bit - 1]) ^ 1) + encoded_chunk[num_bit:]
        return encoded_chunk
    
    def encode(self, bits):
        if not bits:
            return bits
        
        remainder = len(bits) % self.CHUNK_LENGTH
        if remainder:
            bits = bits + '0' * (self.CHUNK_LENGTH - remainder)
        
        encoded = []
        for i in range(0, len(bits), self.CHUNK_LENGTH):
            chunk = bits[i:i+self.CHUNK_LENGTH]
            encoded_chunk = self._set_check_bits(chunk)
            encoded.append(encoded_chunk)
        
        return ''.join(encoded)
    
    def decode(self, bits, fix_errors=True):
        if not bits or len(bits) % self.CODEWORD_LENGTH != 0:
            return bits if not bits else None
        
        decoded = []
        for i in range(0, len(bits), self.CODEWORD_LENGTH):
            chunk = bits[i:i+self.CODEWORD_LENGTH]
            if fix_errors:
                chunk = self._check_and_fix_error(chunk)
            clean_chunk = self._exclude_check_bits(chunk)
            decoded.append(clean_chunk)
        
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
    
    print("Доступные варианты длины блока: 8, 16, 32")
    try:
        chunk_length = int(input("Введите длину блока для кода Хэмминга (по умолчанию 8): ") or "8")
        if chunk_length not in [8, 16, 32]:
            print("Неверное значение. Используется значение по умолчанию (8)")
            chunk_length = 8
    except ValueError:
        print("Ошибка ввода. Используется значение по умолчанию (8)")
        chunk_length = 8
    
    hamming_coder = HammingCoder(chunk_length)
    print(f"Длина блока: {hamming_coder.CHUNK_LENGTH}")
    print(f"Контрольные биты: {hamming_coder.CHECK_BITS}")
    print(f"Длина кодового слова: {hamming_coder.CODEWORD_LENGTH}\n")
    
    encoded = SignCoder.sign_encoder(msg)
    if not encoded:
        print("Ошибка кодирования")
        return
    
    print(f"Этап 1 - Символьное кодирование:")
    print(f"  Сообщение: {msg}")
    print(f"  Битов: {len(encoded)}")
    
    hamming_encoded = hamming_coder.encode(encoded)
    print(f"\nЭтап 2 - Кодирование Хэмминга:")
    print(f"  Сообщение: {msg}")
    print(f"  Закодировано: {len(hamming_encoded)} бит")
    
    interleaver = Interleaver(seed=42)
    interleaved = interleaver.interleave(hamming_encoded)
    print(f"\nЭтап 3 - Перемежение:")
    print(f"  Сообщение: {msg}")
    
    print(f"\nЭтап 4 - QPSK модуляция:")
    print(f"  Сообщение: {msg}")
    modulated_symbols = Modulator.modulate(interleaved)
    print(f"  Символов: {len(modulated_symbols)}")
    
    print(f"\nЭтап 5 - Канал с шумом:")
    print(f"  Сообщение: {msg}")
    np.random.seed(42)
    noisy_symbols = add_channel_noise(modulated_symbols, noise_level=0.2)
    
    print(f"\nЭтап 6 - QPSK демодуляция:")
    print(f"  Сообщение: {msg}")
    demodulated_bits = Demodulator.demodulate(noisy_symbols)
    
    correct = sum(1 for i in range(len(interleaved)) if interleaved[i] == demodulated_bits[i])
    print(f"  Совпадение бит до/после демодуляции: {correct}/{len(interleaved)} ({correct/len(interleaved)*100:.1f}%)")
    
    deinterleaver = Deinterleaver(interleaver)
    deinterleaved = deinterleaver.deinterleave(demodulated_bits)
    print(f"\nЭтап 7 - Деинтерливинг:")
    print(f"  Сообщение: {msg}")
    
    hamming_decoded = hamming_coder.decode(deinterleaved, fix_errors=True)
    if not hamming_decoded:
        print("Ошибка декодирования Хэмминга")
        return
    
    print(f"\nЭтап 8 - Декодирование Хэмминга с исправлением ошибок:")
    print(f"  Сообщение: {msg}")
    
    decoded = SignCoder.sign_decoder(hamming_decoded[:len(encoded)])
    
    print(f"\nЭтап 9 - Символьное декодирование:")
    print(f"  Исходное сообщение: {msg}")
    print(f"  Декодированное сообщение: {decoded}")
    print(f"  Успех: {msg == decoded}")
    
    print("\n" + "="*60)
    print("ОБЪЯСНЕНИЕ РАБОТЫ КОДА ХЭММИНГА")
    print("="*60)
    print(f"Длина информационного блока: {hamming_coder.CHUNK_LENGTH} бит")
    print(f"Контрольные биты на позициях: {hamming_coder.CHECK_BITS}")
    print(f"Общая длина кодового слова: {hamming_coder.CODEWORD_LENGTH} бит")
    print("\nПринцип работы:")
    print("1. Информационные биты размещаются на позициях, не являющихся степенями двойки")
    print("2. Контрольные биты рассчитываются как XOR определенных информационных бит")
    print("3. При декодировании вычисляется синдром для определения позиции ошибки")
    print("4. Код может исправить одну ошибку в блоке")

if __name__ == "__main__":
    main()
