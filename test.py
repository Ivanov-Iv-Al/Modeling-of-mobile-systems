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
        if not bits:
            return bits
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
        if not bits:
            return None
        working_bits = bits
        remainder = len(working_bits) % self.N
        if remainder:
            working_bits = working_bits + '0' * (self.N - remainder)

        decoded = []
        for i in range(0, len(working_bits), self.N):
            r = [int(b) for b in working_bits[i:i + self.N]]
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
    @staticmethod
    def modulate(bits):
        if bits is None or len(bits) == 0:
            return []

        working_bits = bits
        if len(working_bits) % 2 != 0:
            working_bits = working_bits + '0'

        symbols = []
        for i in range(0, len(working_bits), 2):
            bit_pair = working_bits[i:i + 2]

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
        if symbols is None or len(symbols) == 0:
            return ""

        bits = []
        for symbol in symbols:

            real_part = symbol.real
            imag_part = symbol.imag

            norm = np.sqrt(real_part ** 2 + imag_part ** 2)
            if norm > 0:
                real_part = real_part / norm
                imag_part = imag_part / norm

            if real_part > 0 and imag_part > 0:
                bits.append('00')
            elif real_part > 0 and imag_part < 0:
                bits.append('01')
            elif real_part < 0 and imag_part > 0:
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


class OFDMTransmitter:
    def __init__(self, n_subcarriers=64, cp_len=16, pilot_spacing=8, pilot_value=complex(0.707, 0.707)):
        self.n_subcarriers = n_subcarriers
        self.cp_len = cp_len
        self.pilot_spacing = pilot_spacing
        self.pilot_value = pilot_value
        self.pilot_indices = list(range(0, n_subcarriers, pilot_spacing))
        self.data_indices = [i for i in range(n_subcarriers) if i not in self.pilot_indices]

    def transmit(self, symbols):
        n_data_per_symbol = len(self.data_indices)
        n_symbols = len(symbols) // n_data_per_symbol
        if len(symbols) % n_data_per_symbol != 0:
            n_symbols += 1

        grid = np.zeros((self.n_subcarriers, n_symbols), dtype=complex)

        for i in range(n_symbols):
            for p_idx in self.pilot_indices:
                grid[p_idx, i] = self.pilot_value

        symbol_idx = 0
        for i in range(n_symbols):
            for d_idx in self.data_indices:
                if symbol_idx < len(symbols):
                    grid[d_idx, i] = symbols[symbol_idx]
                    symbol_idx += 1

        ofdm_time = np.fft.ifft(np.fft.ifftshift(grid, axes=0), axis=0) * np.sqrt(self.n_subcarriers)

        cp = ofdm_time[-self.cp_len:, :]
        ofdm_with_cp = np.vstack([cp, ofdm_time])

        return ofdm_with_cp.reshape(-1, order='F'), grid


class OFDMReceiver:
    def __init__(self, transmitter):
        self.n_subcarriers = transmitter.n_subcarriers
        self.cp_len = transmitter.cp_len
        self.pilot_spacing = transmitter.pilot_spacing
        self.pilot_value = transmitter.pilot_value
        self.pilot_indices = transmitter.pilot_indices
        self.data_indices = transmitter.data_indices

    def receive(self, signal):
        sym_len = self.n_subcarriers + self.cp_len
        n_symbols = len(signal) // sym_len

        rx_mat = signal[:n_symbols * sym_len].reshape(sym_len, n_symbols, order='F')
        rx_no_cp = rx_mat[self.cp_len:, :]

        grid_rx = np.fft.fftshift(np.fft.fft(rx_no_cp, axis=0) / np.sqrt(self.n_subcarriers), axes=0)

        rx_pilots = np.array([grid_rx[idx, :] for idx in self.pilot_indices])
        tx_pilots = np.array([self.pilot_value] * len(self.pilot_indices))

        h_est = rx_pilots / tx_pilots[:, np.newaxis]
        h_est_mean = np.mean(h_est, axis=1)

        grid_eq = np.zeros_like(grid_rx)

        for i in range(self.n_subcarriers):
            if i in self.pilot_indices:
                pilot_idx = self.pilot_indices.index(i)
                grid_eq[i, :] = grid_rx[i, :] / h_est_mean[pilot_idx]
            else:
                left_pilots = [p for p in self.pilot_indices if p < i]
                right_pilots = [p for p in self.pilot_indices if p > i]

                if left_pilots and right_pilots:
                    left_pilot = left_pilots[-1]
                    right_pilot = right_pilots[0]
                    left_idx = self.pilot_indices.index(left_pilot)
                    right_idx = self.pilot_indices.index(right_pilot)

                    weight = (i - left_pilot) / (right_pilot - left_pilot)
                    h_interp = h_est_mean[left_idx] * (1 - weight) + h_est_mean[right_idx] * weight
                    grid_eq[i, :] = grid_rx[i, :] / h_interp
                elif left_pilots:
                    left_pilot = left_pilots[-1]
                    left_idx = self.pilot_indices.index(left_pilot)
                    grid_eq[i, :] = grid_rx[i, :] / h_est_mean[left_idx]
                elif right_pilots:
                    right_pilot = right_pilots[0]
                    right_idx = self.pilot_indices.index(right_pilot)
                    grid_eq[i, :] = grid_rx[i, :] / h_est_mean[right_idx]
                else:
                    grid_eq[i, :] = grid_rx[i, :]

        symbols = []
        for i in range(grid_eq.shape[1]):
            for d_idx in self.data_indices:
                if d_idx < len(grid_eq):
                    symbols.append(grid_eq[d_idx, i])

        return np.array(symbols), grid_rx, grid_eq


class MultipathChannel:
    def __init__(self, fc=2.4e9, bandwidth=10e6, num_paths=3, snr_db=20):
        self.fc = fc
        self.bandwidth = bandwidth
        self.num_paths = num_paths
        self.snr_db = snr_db
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

        gains = [self.c / (4 * np.pi * d * self.fc) for d in distances]

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

        signal_power = np.mean(np.abs(rx_signal) ** 2)
        snr_linear = 10 ** (self.snr_db / 10)
        noise_power = signal_power / snr_linear
        noise_std = np.sqrt(noise_power / 2)
        noise = noise_std * (np.random.randn(L) + 1j * np.random.randn(L))

        return rx_signal + noise


def calculate_ber(tx_bits, rx_bits):
    if len(tx_bits) != len(rx_bits):
        min_len = min(len(tx_bits), len(rx_bits))
        tx_bits = tx_bits[:min_len]
        rx_bits = rx_bits[:min_len]

    errors = sum(1 for i in range(len(tx_bits)) if tx_bits[i] != rx_bits[i])
    return errors / len(tx_bits) if len(tx_bits) > 0 else 0, errors


def plot_spectrums(tx_grid, rx_grid_before, rx_grid_after):
    plt.figure(figsize=(12, 8))
    plt.subplot(3, 1, 1)
    plt.plot(np.mean(np.abs(tx_grid), axis=1))
    plt.title('Спектр переданного OFDM символа')
    plt.xlabel('Индекс поднесущей')
    plt.ylabel('Амплитуда')
    plt.grid(True)
    plt.subplot(3, 1, 2)
    plt.plot(np.mean(np.abs(rx_grid_before), axis=1))
    plt.title('Спектр принятого OFDM символа до эквалайзинга')
    plt.xlabel('Индекс поднесущей')
    plt.ylabel('Амплитуда')
    plt.grid(True)
    plt.subplot(3, 1, 3)
    plt.plot(np.mean(np.abs(rx_grid_after), axis=1))
    plt.title('Спектр принятого OFDM символа после эквалайзинга')
    plt.xlabel('Индекс поднесущей')
    plt.ylabel('Амплитуда')
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_constellations(tx_symbols, rx_symbols):
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.scatter([s.real for s in tx_symbols], [s.imag for s in tx_symbols], s=10, alpha=0.7)
    plt.title('Сигнальное созвездие QPSK в передатчике')
    plt.xlabel('I')
    plt.ylabel('Q')
    plt.grid(True)
    plt.axis('equal')
    plt.subplot(1, 2, 2)
    plt.scatter([s.real for s in rx_symbols], [s.imag for s in rx_symbols], s=10, alpha=0.7)
    plt.title('Сигнальное созвездие QPSK в приёмнике')
    plt.xlabel('I')
    plt.ylabel('Q')
    plt.grid(True)
    plt.axis('equal')
    plt.tight_layout()
    plt.show()

def plot_all_in_one(tx_grid, rx_grid_before, rx_grid_after, tx_symbols, rx_symbols):

    tx_spectrum = np.mean(np.abs(tx_grid), axis=1)
    rx_spectrum_before = np.mean(np.abs(rx_grid_before), axis=1)
    rx_spectrum_after = np.mean(np.abs(rx_grid_after), axis=1)

    h_channel = rx_spectrum_before / (tx_spectrum + 1e-10)

    fig = plt.figure(figsize=(16, 12))

    ax1 = plt.subplot(2, 3, 1)
    ax1.plot(tx_spectrum, 'b-', linewidth=2)
    ax1.set_title('Спектр переданного OFDM символа')
    ax1.set_xlabel('Индекс поднесущей')
    ax1.set_ylabel('Амплитуда')
    ax1.grid(True)
    ax1.set_xlim(0, len(tx_spectrum) - 1)

    ax2 = plt.subplot(2, 3, 2)
    ax2.plot(rx_spectrum_before, 'r-', linewidth=2)
    ax2.set_title('Спектр принятого OFDM символа (до эквалайзинга)')
    ax2.set_xlabel('Индекс поднесущей')
    ax2.set_ylabel('Амплитуда')
    ax2.grid(True)
    ax2.set_xlim(0, len(rx_spectrum_before) - 1)

    ax3 = plt.subplot(2, 3, 3)
    ax3.plot(rx_spectrum_after, 'g-', linewidth=2)
    ax3.set_title('Спектр принятого OFDM символа (после эквалайзинга)')
    ax3.set_xlabel('Индекс поднесущей')
    ax3.set_ylabel('Амплитуда')
    ax3.grid(True)
    ax3.set_xlim(0, len(rx_spectrum_after) - 1)

    ax4 = plt.subplot(2, 3, 4)
    ax4.plot(h_channel, 'm-', linewidth=2)
    ax4.set_title('Оценка АЧХ канала передачи')
    ax4.set_xlabel('Индекс поднесущей')
    ax4.set_ylabel('|H|')
    ax4.grid(True)
    ax4.set_xlim(0, len(h_channel) - 1)

    ax5 = plt.subplot(2, 3, 5)
    ax5.scatter([s.real for s in tx_symbols[:500]], [s.imag for s in tx_symbols[:500]],
                s=15, alpha=0.6, c='blue', marker='o')
    ax5.set_title('Сигнальное созвездие QPSK в передатчике')
    ax5.set_xlabel('I')
    ax5.set_ylabel('Q')
    ax5.grid(True)
    ax5.axis('equal')
    ax5.set_xlim(-1.5, 1.5)
    ax5.set_ylim(-1.5, 1.5)
    ax5.axhline(y=0, color='k', linewidth=0.5)
    ax5.axvline(x=0, color='k', linewidth=0.5)

    ax6 = plt.subplot(2, 3, 6)
    ax6.scatter([s.real for s in rx_symbols[:500]], [s.imag for s in rx_symbols[:500]],
                s=15, alpha=0.6, c='red', marker='o')
    ax6.set_title('Сигнальное созвездие QPSK в приёмнике')
    ax6.set_xlabel('I')
    ax6.set_ylabel('Q')
    ax6.grid(True)
    ax6.axis('equal')
    ax6.set_xlim(-1.5, 1.5)
    ax6.set_ylim(-1.5, 1.5)
    ax6.axhline(y=0, color='k', linewidth=0.5)
    ax6.axvline(x=0, color='k', linewidth=0.5)

    plt.tight_layout()
    plt.show()

def main():
    msg = "Hello World. This is test message and no more..."
    print(f"Исходное сообщение: {msg}\n")
    print(f"Длина сообщения: {len(msg)} символов")

    encoded = SignCoder.sign_encoder(msg)
    if not encoded:
        print("Ошибка кодирования")
        return
    print(f"Символьное кодирование: {len(encoded)} бит")

    k_bits = 11
    hamming_coder = HammingCoder(k_bits)
    hamming_encoded = hamming_coder.encode(encoded)
    print(f"Кодирование Хэмминга: {len(hamming_encoded)} бит")

    interleaver = Interleaver(seed=42)
    interleaved = interleaver.interleave(hamming_encoded)
    print(f"Перемежение: {len(interleaved)} бит")

    qpsk_symbols = Modulator.modulate(interleaved)
    print(f"QPSK модуляция: {len(qpsk_symbols)} символов")

    n_subcarriers = 64
    cp_len = 16
    pilot_spacing = 8

    ofdm_tx = OFDMTransmitter(
        n_subcarriers=n_subcarriers,
        cp_len=cp_len,
        pilot_spacing=pilot_spacing
    )
    ofdm_signal, tx_grid = ofdm_tx.transmit(qpsk_symbols)
    print(f"OFDM модуляция: {len(ofdm_signal)} отсчётов")
    print(f"Количество поднесущих: {n_subcarriers}")
    print(f"Пилот-тоны: {len(ofdm_tx.pilot_indices)} (каждые {pilot_spacing})")

    num_paths = 3
    snr_db = 20

    channel = MultipathChannel(fc=2.4e9, bandwidth=10e6, num_paths=num_paths, snr_db=snr_db)
    received_signal = channel.propagate(ofdm_signal)
    print(f"\nМноголучевой канал: {num_paths} лучей, SNR = {snr_db} дБ")

    ofdm_rx = OFDMReceiver(ofdm_tx)
    recovered_symbols, rx_grid_before, rx_grid_after = ofdm_rx.receive(received_signal)
    recovered_symbols = recovered_symbols[:len(qpsk_symbols)]
    print(f"OFDM демодуляция с эквалайзингом: {len(recovered_symbols)} символов")

    demodulated_bits = Demodulator.demodulate(recovered_symbols)
    print(f"QPSK демодуляция: {len(demodulated_bits)} бит")

    # Обрезаем до нужной длины
    if len(demodulated_bits) > len(interleaved):
        demodulated_bits = demodulated_bits[:len(interleaved)]
    elif len(demodulated_bits) < len(interleaved):
        demodulated_bits = demodulated_bits + '0' * (len(interleaved) - len(demodulated_bits))

    deinterleaver = Deinterleaver(interleaver)
    deinterleaved = deinterleaver.deinterleave(demodulated_bits)
    print(f"Обратное перемежение: {len(deinterleaved)} бит")

    hamming_decoded = hamming_coder.decode(deinterleaved)
    if not hamming_decoded:
        print("Ошибка декодирования Хэмминга")
        return
    print(f"Декодирование Хэмминга: {len(hamming_decoded)} бит")

    hamming_decoded = hamming_decoded[:len(encoded)]
    decoded = SignCoder.sign_decoder(hamming_decoded)

    if decoded is None:
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .'
        decoded_chars = []
        for i in range(0, len(hamming_decoded), 8):
            if i + 8 <= len(hamming_decoded):
                try:
                    code = int(hamming_decoded[i:i + 8], 2)
                    if code < 64:
                        decoded_chars.append(chars[code])
                    else:
                        decoded_chars.append('?')
                except:
                    decoded_chars.append('?')
        decoded = ''.join(decoded_chars)

    print(f"\nПолученное сообщение: {decoded}")

    ber, errors = calculate_ber(encoded, hamming_decoded)
    print(f"\nBER (вероятность битовых ошибок): {ber:.6f}")
    print(f"Ошибочных бит: {errors} из {len(encoded)}")

    if decoded == msg:
        print("\nСообщение декодировано успешно!")
    else:
        print("\nОшибка при декодировании сообщения")

    plot_spectrums(tx_grid, rx_grid_before, rx_grid_after)
    plot_constellations(qpsk_symbols, recovered_symbols)
    plot_all_in_one(tx_grid, rx_grid_before, rx_grid_after,qpsk_symbols, recovered_symbols)

main()
