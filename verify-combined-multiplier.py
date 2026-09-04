import numpy as np

def fft_qft(state):
    """Performs a 1D QFT on a statevector using FFT."""
    return np.fft.fft(state) / np.sqrt(len(state))

def fft_iqft(state):
    """Performs a 1D IQFT on a statevector using IFFT."""
    return np.fft.ifft(state) * np.sqrt(len(state))

def simulate_modular_multiplier(n: int, N_mod: int, m: int, x_val: int, y_val: int):
    """
    Simulates the exact behavior of the combined Quantum-Quantum Modular Multiplier (QQMM).
    This includes:
      1. QQM phase multiplier evaluation into register w
      2. Modular Reconstruction into product register P using controlled Draper additions
      3. Complete uncomputation of register w
    """
    size_P = 2**(n + 1)
    size_w = 2**m
    
    # =========================================================================
    # STEP 1: QQM Phase Multiplier Evaluation into Register 'w'
    # =========================================================================
    w_qft = np.zeros(size_w, dtype=complex)
    product_val = x_val * y_val
    for w_val in range(size_w):
        phase = -2 * np.pi * (product_val / N_mod) * w_val
        w_qft[w_val] = np.exp(1j * phase) / np.sqrt(size_w)
    
    # Apply IQFT to bring w to the computational basis
    w_state = fft_iqft(w_qft)
    
    # =========================================================================
    # STEP 2: Modular Reconstruction into Product Register 'P'
    # =========================================================================
    # Product register is initialized to |0>. QFT of |0> is the uniform superposition.
    P_qft = np.ones(size_P, dtype=complex) / np.sqrt(size_P)
    
    # Build joint state of P (Fourier basis) and w (computational basis)
    joint_state = np.outer(P_qft, w_state)
    
    # Apply controlled-phase: phase = -2 * pi * N_mod * w * P / (2^m * 2^(n+1))
    for P_val in range(size_P):
        for w_val in range(size_w):
            phase = -2 * np.pi * (N_mod * w_val * P_val) / (size_w * size_P)
            joint_state[P_val, w_val] *= np.exp(1j * phase)
            
    # Apply IQFT to P (axis 0) to bring the product back to the computational basis
    for w_val in range(size_w):
        joint_state[:, w_val] = fft_iqft(joint_state[:, w_val])
        
    # =========================================================================
    # STEP 3: Reversible Uncomputation of 'w'
    # =========================================================================
    # Apply forward QFT to w (axis 1) to prepare for phase-subtraction
    for P_val in range(size_P):
        joint_state[P_val, :] = fft_qft(joint_state[P_val, :])
        
    # Subtract P/N_mod from w_qft: phase = +2 * pi * P_val * w_val / N_mod
    for P_val in range(size_P):
        for w_val in range(size_w):
            phase = 2 * np.pi * (P_val * w_val) / N_mod
            joint_state[P_val, w_val] *= np.exp(1j * phase)
            
    # Apply IQFT to w (axis 1) to restore it back to the computational basis
    for P_val in range(size_P):
        joint_state[P_val, :] = fft_iqft(joint_state[P_val, :])
        
    # Find the peak probability
    probabilities = np.abs(joint_state)**2
    max_idx = np.unravel_index(np.argmax(probabilities), probabilities.shape)
    peak_P, peak_w = max_idx
    peak_prob = probabilities[peak_P, peak_w]
    
    return peak_P, peak_w, peak_prob

if __name__ == "__main__":
    print("=================================================================")
    print("RUNNING MODULAR MULTIPLIER VALIDATION ON NUMPY EMULATOR")
    print("=================================================================\n")
    
    test_cases = [
        {"n": 6, "N_mod": 13, "m": 10, "x": 6, "y": 7, "expected": 3},
        {"n": 6, "N_mod": 11, "m": 10, "x": 5, "y": 4, "expected": 9}
    ]

    for tc in test_cases:
        peak_P, peak_w, prob = simulate_modular_multiplier(tc["n"], tc["N_mod"], tc["m"], tc["x"], tc["y"])
        print(f"TEST CASE: {tc['x']} * {tc['y']} (mod {tc['N_mod']}) | Qubits: {tc['n']}")
        print(f"  Measured Product Register P: {peak_P} (Expected: {tc['expected']})")
        print(f"  Measured Carry Register w  : {peak_w} (Expected: 0)")
        print(f"  Success Probability        : {prob * 100:.2f}%")
        if peak_P == tc["expected"] and peak_w == 0:
            print("  STATUS: SUCCESS / PASSED!\n")
        else:
            print("  STATUS: FAILED!\n")
    print("=================================================================")
