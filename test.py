import numpy as np
import matplotlib.pyplot as plt

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
        while (2 ** self.m) < (self.K + self.m + 1):
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
                    codeword[pos - 1] = data[data_idx]
                    data_idx += 1
            for j in range(self.m):
                p_pos = 2 ** j
                parity = 0
                for pos in range(1, self.N + 1):
                    if pos & p_pos:
                        parity ^= codeword[pos - 1]
                codeword[p_pos - 1] = parity
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
                p_pos = 2 ** j
                parity = 0
                for pos in range(1, self.N + 1):
                    if pos & p_pos:
                        parity ^= r[pos - 1]
                if parity:
                    syndrome += p_pos
            if 0 < syndrome <= self.N:
                r[syndrome - 1] ^= 1
            for pos in range(1, self.N + 1):
                if not (pos & (pos - 1) == 0):
                    decoded.append(str(r[pos - 1]))
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

class OfdmModulator:
    def __init__(self, n_subcarriers=64, cp_len=16):
        self.n_subcarriers = n_subcarriers
        self.cp_len = cp_len
        self.original_len = None

    def modulate(self, symbols):

        if not symbols:
            return []
        self.original_len = len(symbols)

        n_sym = len(symbols)
        pad_len = (self.n_subcarriers - (n_sym % self.n_subcarriers)) % self.n_subcarriers
        if pad_len > 0:
            symbols = np.append(symbols, [0 + 0j] * pad_len)

        symbols = np.array(symbols)
        blocks = symbols.reshape(-1, self.n_subcarriers)
        ofdm_signal = []
        for block in blocks:

            ifft_block = np.fft.ifft(block, self.n_subcarriers)

            cp = ifft_block[-self.cp_len:]
            ofdm_signal.extend(np.concatenate([cp, ifft_block]))
        return np.array(ofdm_signal)


class OfdmDemodulator:
    def __init__(self, modulator):
        self.n_subcarriers = modulator.n_subcarriers
        self.cp_len = modulator.cp_len
        self.original_len = modulator.original_len

    def demodulate(self, ofdm_signal):

        if len(ofdm_signal) == 0:
            return []
        block_len = self.n_subcarriers + self.cp_len
        n_blocks = len(ofdm_signal) // block_len
        if len(ofdm_signal) % block_len != 0:

            ofdm_signal = ofdm_signal[:n_blocks * block_len]
        symbols = []
        for i in range(n_blocks):
            block = ofdm_signal[i * block_len: (i + 1) * block_len]

            data_part = block[self.cp_len:]

            fft_block = np.fft.fft(data_part, self.n_subcarriers)
            symbols.extend(fft_block)

        if self.original_len is not None:
            symbols = symbols[:self.original_len]
        return symbols



class MultipathChannel:
    def __init__(self, fc=2.4e9, bandwidth=9e6, num_paths=3, n0_db=-100):

        self.fc = fc
        self.bandwidth = bandwidth
        self.num_paths = num_paths
        self.n0_db = n0_db
        self.c = 3e8
        self.Ts = 1.0 / bandwidth

    def propagate(self, tx_signal):

        if len(tx_signal) == 0:
            return tx_signal

        distances = np.random.uniform(10, 500, self.num_paths)
        min_dist = np.min(distances)

        delays = []
        for d in distances:
            tau = (d - min_dist) / (self.c * self.Ts)
            delays.append(int(round(tau)))

        gains = []
        for d in distances:
            gain = self.c / (4 * np.pi * d * self.fc)
            gains.append(gain)

        max_delay = max(delays)
        L = len(tx_signal)

        rx_sum = np.zeros(L + max_delay, dtype=complex)

        for i in range(self.num_paths):
            shift = delays[i]
            gain = gains[i]

            shifted = np.zeros(L + shift, dtype=complex)
            shifted[shift:] = tx_signal * gain

            if len(shifted) > len(rx_sum):
                shifted = shifted[:len(rx_sum)]
            rx_sum[:len(shifted)] += shifted


        rx_signal = rx_sum[:L]

        n0_linear = 10 ** (self.n0_db / 10.0)

        noise_power = n0_linear * self.bandwidth

        noise_std = np.sqrt(noise_power / 2.0)
        noise = noise_std * (np.random.randn(L) + 1j * np.random.randn(L))
        rx_signal += noise

        return rx_signal


def main():
    msg = "Hello World. This is test message and no more..."
    print(f"Исходное сообщение: {msg}\n")
    print(f"Исходное сообщение(длительность): {len(msg) * 8}\n")

    user_input = input("Введите количество информационных бит для кода Хэмминга: ")
    k_bits = int(user_input) if user_input else 11

    encoded = SignCoder.sign_encoder(msg)
    if not encoded:
        print("Ошибка кодирования")
        return
    print(f"Символьное кодирование:")
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
    print(f"  Первые 10 бит: {interleaved[:10]}")
    print(f"  Первые 10 бит до перемежения: {hamming_encoded[:10]}")

    print(f"\nQPSK модуляция:")
    qpsk_symbols = Modulator.modulate(interleaved)
    print(f"  До модуляции: {len(interleaved)} бит")
    print(f"  После модуляции: {len(qpsk_symbols)} символов")

    N_SUBCARRIERS = 64
    CP_LEN = 16
    ofdm_mod = OfdmModulator(n_subcarriers=N_SUBCARRIERS, cp_len=CP_LEN)
    ofdm_signal = ofdm_mod.modulate(qpsk_symbols)

    print(f"\nOFDM модуляция:")
    print(f"  Символов на входе: {len(qpsk_symbols)}")
    print(f"  OFDM отсчётов на выходе (с CP): {len(ofdm_signal)}")

    nl_input = 9 #input("Введите количество лучей (Nl): ")
    num_paths = int(nl_input) if nl_input else 3
    n0_input = input("Введите мощность АБГШ (N0, дБ): ")
    n0_db = float(n0_input) if n0_input else -100.0

    FC = 2.4e9
    BANDWIDTH = 1e6

    channel = MultipathChannel(fc=FC, bandwidth=BANDWIDTH,
                               num_paths=num_paths, n0_db=n0_db)

    received_signal = channel.propagate(ofdm_signal)
    print(f"\nМноголучевость и АБГШ")
    print(f"  Количество лучей: {num_paths}")
    print(f"  N0 = {n0_db} дБ")
    print(f"  Длина принятого сигнала: {len(received_signal)} отсчётов")

    ofdm_demod = OfdmDemodulator(ofdm_mod)
    recovered_qpsk = ofdm_demod.demodulate(received_signal)
    print(f"\nOFDM демодуляция:")
    print(f"  Восстановлено QPSK символов: {len(recovered_qpsk)} (ожидалось {len(qpsk_symbols)})")

    demodulated_bits = Demodulator.demodulate(recovered_qpsk)
    print(f"\nQPSK демодуляция:")
    print(f"  После демодуляции: {len(demodulated_bits)} бит")
    print(f"  Первые 30 бит: {demodulated_bits[:30]}...")

    correct = sum(
        1 for i in range(len(interleaved)) if i < len(demodulated_bits) and interleaved[i] == demodulated_bits[i])
    print(f"  Совпадение бит (до деперемежения): {correct}/{len(interleaved)}")

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
    print(f"\nПолученное сообщение: {decoded}")

main()

