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
    def __init__(self, delta_rs=6, cp_len=16, c_param=0.25, pilot_value=complex(0.707, 0.707)):
        self.delta_rs = delta_rs
        self.cp_len = cp_len
        self.c_param = c_param
        self.pilot_value = pilot_value
        self.n_pilots = None
        self.n_zeros = None
        self.total_carriers = None
        self.pilot_indices = None
        self.data_indices = None
        self.n_qpsk = None
        
    def modulate(self, symbols):
        if not symbols:
            return []
        
        self.n_qpsk = len(symbols)
        self.n_pilots = int(np.floor(self.n_qpsk / self.delta_rs))
        if self.n_pilots == 0:
            self.n_pilots = 1
        
        self.n_zeros = int(self.c_param * (self.n_pilots + self.n_qpsk))
        self.total_carriers = self.n_pilots + self.n_qpsk + 2 * self.n_zeros
        
        spectrum = np.zeros(self.total_carriers, dtype=complex)
        
        self.pilot_indices = []
        pilot_pos = self.n_zeros
        for i in range(self.n_pilots):
            idx = pilot_pos + i * self.delta_rs
            if idx < self.total_carriers - self.n_zeros:
                self.pilot_indices.append(int(idx))
                spectrum[idx] = self.pilot_value
        
        self.data_indices = []
        data_idx = 0
        for i in range(self.total_carriers):
            if i >= self.n_zeros and i < self.total_carriers - self.n_zeros:
                if i not in self.pilot_indices:
                    if data_idx < len(symbols):
                        spectrum[i] = symbols[data_idx]
                        self.data_indices.append(i)
                        data_idx += 1
        
        time_signal = np.fft.ifft(spectrum)
        
        cp = time_signal[-self.cp_len:]
        ofdm_symbol = np.concatenate([cp, time_signal])
        
        return ofdm_symbol


class OfdmDemodulator:
    def __init__(self, modulator):
        self.delta_rs = modulator.delta_rs
        self.cp_len = modulator.cp_len
        self.c_param = modulator.c_param
        self.pilot_value = modulator.pilot_value
        self.n_pilots = modulator.n_pilots
        self.n_zeros = modulator.n_zeros
        self.total_carriers = modulator.total_carriers
        self.pilot_indices = modulator.pilot_indices
        self.data_indices = modulator.data_indices
        self.n_qpsk = modulator.n_qpsk
        
    def demodulate(self, ofdm_signal):
        if len(ofdm_signal) == 0:
            return []
        
        time_signal = ofdm_signal[self.cp_len:self.cp_len + self.total_carriers]
        
        spectrum = np.fft.fft(time_signal)
        
        rx_pilots = np.array([spectrum[idx] for idx in self.pilot_indices])
        tx_pilots = np.array([self.pilot_value] * len(self.pilot_indices))
        
        h_est = rx_pilots / tx_pilots
        
        all_data_indices = list(range(self.n_zeros, self.total_carriers - self.n_zeros))
        h_full = np.interp(all_data_indices, self.pilot_indices, h_est)
        
        heq = 1.0 / h_full
        
        recovered_symbols = []
        for i, idx in enumerate(self.data_indices):
            if idx < len(spectrum):
                eq_idx = all_data_indices.index(idx) if idx in all_data_indices else i
                if eq_idx < len(heq):
                    recovered_symbols.append(spectrum[idx] * heq[eq_idx])
                else:
                    recovered_symbols.append(spectrum[idx])
        
        return np.array(recovered_symbols[:self.n_qpsk])


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


def calculate_ber(tx_bits, rx_bits):
    if len(tx_bits) != len(rx_bits):
        min_len = min(len(tx_bits), len(rx_bits))
        tx_bits = tx_bits[:min_len]
        rx_bits = rx_bits[:min_len]
    
    errors = sum(1 for i in range(len(tx_bits)) if tx_bits[i] != rx_bits[i])
    ber = errors / len(tx_bits) if len(tx_bits) > 0 else 0
    return ber, errors


def plot_spectrums(tx_spectrum, rx_spectrum_before, rx_spectrum_after):
    plt.figure(figsize=(12, 8))
    
    plt.subplot(3, 1, 1)
    plt.plot(np.abs(tx_spectrum))
    plt.title('Спектр переданного OFDM символа')
    plt.xlabel('Индекс поднесущей')
    plt.ylabel('Амплитуда')
    plt.grid(True)
    
    plt.subplot(3, 1, 2)
    plt.plot(np.abs(rx_spectrum_before))
    plt.title('Спектр принятого OFDM символа до эквалайзирования')
    plt.xlabel('Индекс поднесущей')
    plt.ylabel('Амплитуда')
    plt.grid(True)
    
    plt.subplot(3, 1, 3)
    plt.plot(np.abs(rx_spectrum_after))
    plt.title('Спектр принятого OFDM символа после эквалайзирования')
    plt.xlabel('Индекс поднесущей')
    plt.ylabel('Амплитуда')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()


def plot_constellations(tx_symbols, rx_symbols):
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.scatter([s.real for s in tx_symbols], [s.imag for s in tx_symbols])
    plt.title('Сигнальное созвездие QPSK в передатчике')
    plt.xlabel('I')
    plt.ylabel('Q')
    plt.grid(True)
    plt.axis('equal')
    
    plt.subplot(1, 2, 2)
    plt.scatter([s.real for s in rx_symbols], [s.imag for s in rx_symbols])
    plt.title('Сигнальное созвездие QPSK в приемнике')
    plt.xlabel('I')
    plt.ylabel('Q')
    plt.grid(True)
    plt.axis('equal')
    
    plt.tight_layout()
    plt.show()


def main():
    msg = "Hello World. This is test message and no more..."
    print(f"Исходное сообщение: {msg}\n")
    print(f"Длина сообщения: {len(msg)} символов")

    user_input = input("Введите количество информационных бит для кода Хэмминга (например 11): ")
    k_bits = int(user_input) if user_input else 11

    encoded = SignCoder.sign_encoder(msg)
    if not encoded:
        print("Ошибка кодирования")
        return
    print(f"Символьное кодирование: {len(encoded)} бит")

    hamming_coder = HammingCoder(k_bits)
    hamming_encoded = hamming_coder.encode(encoded)
    print(f"Кодирование Хэмминга: {len(hamming_encoded)} бит")

    interleaver = Interleaver(seed=42)
    interleaved = interleaver.interleave(hamming_encoded)
    print(f"Перемежение: {len(interleaved)} бит")

    qpsk_symbols = Modulator.modulate(interleaved)
    print(f"QPSK модуляция: {len(qpsk_symbols)} символов")

    delta_rs = int(input("Введите шаг опорных поднесущих delta_RS (например 6): ") or 6)
    cp_len = int(input("Введите длину циклического префикса TCP (например 16): ") or 16)
    c_param = float(input("Введите параметр C для нулевых поднесущих (например 0.25): ") or 0.25)
    
    ofdm_mod = OfdmModulator(delta_rs=delta_rs, cp_len=cp_len, c_param=c_param)
    ofdm_signal = ofdm_mod.modulate(qpsk_symbols)
    print(f"OFDM модуляция: {len(ofdm_signal)} отсчетов")

    num_paths = int(input("Введите количество лучей (например 3): ") or 3)
    n0_db = float(input("Введите мощность АБГШ N0 в дБ (например -100): ") or -100)

    channel = MultipathChannel(fc=2.4e9, bandwidth=10e6, num_paths=num_paths, n0_db=n0_db)
    received_signal = channel.propagate(ofdm_signal)
    print(f"Многолучевой канал: {num_paths} лучей, N0 = {n0_db} дБ")

    ofdm_demod = OfdmDemodulator(ofdm_mod)
    recovered_qpsk = ofdm_demod.demodulate(received_signal)
    print(f"OFDM демодуляция: {len(recovered_qpsk)} символов")

    demodulated_bits = Demodulator.demodulate(recovered_qpsk)
    print(f"QPSK демодуляция: {len(demodulated_bits)} бит")

    deinterleaver = Deinterleaver(interleaver)
    deinterleaved = deinterleaver.deinterleave(demodulated_bits)
    print(f"Обратное перемежение: {len(deinterleaved)} бит")

    hamming_decoded = hamming_coder.decode(deinterleaved)
    if not hamming_decoded:
        print("Ошибка декодирования Хэмминга")
        return
    print(f"Декодирование Хэмминга: {len(hamming_decoded)} бит")

    decoded = SignCoder.sign_decoder(hamming_decoded[:len(encoded)])
    print(f"\nПолученное сообщение: {decoded}")

    ber, errors = calculate_ber(encoded, hamming_decoded[:len(encoded)])
    print(f"\nBER (вероятность битовых ошибок): {ber:.6f}")
    print(f"Ошибочных бит: {errors} из {len(encoded)}")

    temp_mod = OfdmModulator(delta_rs=delta_rs, cp_len=cp_len, c_param=c_param)
    temp_mod.n_qpsk = len(qpsk_symbols)
    temp_mod.n_pilots = int(np.floor(len(qpsk_symbols) / delta_rs))
    if temp_mod.n_pilots == 0:
        temp_mod.n_pilots = 1
    temp_mod.n_zeros = int(c_param * (temp_mod.n_pilots + len(qpsk_symbols)))
    temp_mod.total_carriers = temp_mod.n_pilots + len(qpsk_symbols) + 2 * temp_mod.n_zeros
    spectrum_tx = np.zeros(temp_mod.total_carriers, dtype=complex)
    pilot_pos = temp_mod.n_zeros
    for i in range(temp_mod.n_pilots):
        idx = pilot_pos + i * delta_rs
        if idx < temp_mod.total_carriers - temp_mod.n_zeros:
            spectrum_tx[int(idx)] = complex(0.707, 0.707)
    data_idx = 0
    for i in range(temp_mod.total_carriers):
        if i >= temp_mod.n_zeros and i < temp_mod.total_carriers - temp_mod.n_zeros:
            if i not in [pilot_pos + j * delta_rs for j in range(temp_mod.n_pilots) if pilot_pos + j * delta_rs < temp_mod.total_carriers - temp_mod.n_zeros]:
                if data_idx < len(qpsk_symbols):
                    spectrum_tx[i] = qpsk_symbols[data_idx]
                    data_idx += 1
    
    time_signal_rx = received_signal[cp_len:cp_len + temp_mod.total_carriers] if len(received_signal) >= cp_len + temp_mod.total_carriers else np.zeros(temp_mod.total_carriers, dtype=complex)
    spectrum_rx_before = np.fft.fft(time_signal_rx) if len(time_signal_rx) == temp_mod.total_carriers else np.zeros(temp_mod.total_carriers, dtype=complex)
    
    recovered_qpsk_full = ofdm_demod.demodulate(received_signal)
    spectrum_rx_after = np.zeros(temp_mod.total_carriers, dtype=complex)
    data_recovered_idx = 0
    for idx in ofdm_mod.data_indices:
        if idx < len(spectrum_rx_after) and data_recovered_idx < len(recovered_qpsk_full):
            spectrum_rx_after[idx] = recovered_qpsk_full[data_recovered_idx]
            data_recovered_idx += 1

    plot_spectrums(spectrum_tx, spectrum_rx_before, spectrum_rx_after)
    plot_constellations(qpsk_symbols, recovered_qpsk)


if __name__ == "__main__":
    main()
