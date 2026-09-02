import sys
import os
from typing import List


current_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(current_dir)
sys.path.append(parent_dir)

from AM import ToomCookMultiply, inline_karatsuba, RPM
from gates import get_scratch_size

from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit_aer import AerSimulator

def run_simulation(qc: QuantumCircuit, n_scratch: int, n_res: int, n_a: int, n_b: int, val_a: int, val_b: int):
    """
    Helper function to run MPS simulation unconstrained by physical layout or size.
    """
    # 1. Initialize simulator with Matrix Product State method to save memory (RAM)
    simulator = AerSimulator(method='matrix_product_state')
    
    print(f"Transpiling circuit ({n_a + n_b + n_res + n_scratch} qubits, unconstrained)...")
    compiled_circuit = transpile(
        qc, 
        simulator, 
        coupling_map=None, 
        initial_layout=None,
        optimization_level=1
    )
    
    print("Running quantum simulation...")
    job = simulator.run(compiled_circuit, shots=1)
    result = job.result()
    counts = result.get_counts()
    
    measured_state = list(counts.keys())[0]
    reversed_state = measured_state[::-1]
    
    # LSB-first parsing of output register
    res_start = n_a + n_b
    res_end = n_a + n_b + n_res
    res_bits = reversed_state[res_start:res_end]
    # Reverse res_bits to represent standard big-endian (MSB-first) for int() conversion
    product = int(res_bits[::-1], 2)
    
    # Parse scratch register to verify clean uncomputation
    scratch_bits = reversed_state[res_end : res_end + n_scratch]
    scratch_clean = all(bit == '0' for bit in scratch_bits)
    
    print(f"Classical Inputs: a = {val_a}, b = {val_b}")
    print(f"Extracted Product Register (res) [LSB-first]: {res_bits}")
    print(f"Extracted Product Register (res) [MSB-first]: {res_bits[::-1]} -> Decimal: {product}")
    print(f"Scratchpad Register returned cleanly to |0>: {scratch_clean}")
    
    expected_product = val_a * val_b
    if product == expected_product and scratch_clean:
        print(f"STATUS: SUCCESS for {n_a}x{n_b} multiplication!")
    else:
        if product != expected_product:
            print(f"STATUS: FAILED (Incorrect product {product}, expected {expected_product}).")
        if not scratch_clean:
            print("STATUS: FAILED (Scratchpad qubits left entangled/unclean).")

def test_russian_peasant():
    print("\n" + "-"*50)
    print("TESTING: Russian Peasant Multiplier (RPM)")
    print("-" * 50)
    
    n_a, n_b = 3, 3
    total_qubits = 2 * (n_a + n_b) + 1
    qc = QuantumCircuit(total_qubits)
    
    val_a, val_b = 3, 5
    # Set a = 3 (binary 011 -> LSB-first [0]=1, [1]=1, [2]=0)
    qc.x(0)
    qc.x(1)
    # Set b = 5 (binary 101 -> LSB-first [0]=1, [1]=0, [2]=1)
    qc.x(3)
    qc.x(5)
    
    rpm_gate = RPM(n_a, n_b)
    qc.append(rpm_gate, qc.qubits)
    qc.measure_all()
    
    simulator = AerSimulator()
    compiled_circuit = transpile(qc, simulator)
    job = simulator.run(compiled_circuit, shots=1)
    result = job.result()
    counts = result.get_counts()
    
    measured_state = list(counts.keys())[0]
    reversed_state = measured_state[::-1]
    
    # LSB-first bit reversal parsing of product register R
    r_start = n_a + n_b
    r_end = 2 * (n_a + n_b)
    r_bits = reversed_state[r_start:r_end]
    product = int(r_bits[::-1], 2) # Reverse to MSB-first for correct decimal value
    
    print(f"Classical Inputs: a = {val_a}, b = {val_b}")
    print(f"Extracted Product Register (R) [LSB-first]: {r_bits}")
    print(f"Extracted Product Register (R) [MSB-first]: {r_bits[::-1]} -> Decimal: {product}")
    
    if product == (val_a * val_b):
        print("STATUS: SUCCESS for Russian Peasant Multiplier!")
    else:
        print("STATUS: FAILED (Check carry propagation logic).")

def test_inline_karatsuba_correct():
    """
    Tests your corrected Gidney-style inline_karatsuba with non-truncated slices.
    """
    print("\n" + "-"*50)
    print("TESTING: Craig Gidney's Correct Reversible Inline Karatsuba")
    print("-"*50)
    
    # Allocates a clean ideal simulation environment
    qc = QuantumCircuit(11)
    
    # Set up Gidney padded word layout: m = 2 words, word size w = 1.
    # To satisfy w_padded = w + lg(m) = 1 + 1 = 2, we allocate lists of qubit slices.
    u_pieces = [[qc.qubits[0]], [qc.qubits[1]]]
    v_pieces = [[qc.qubits[2]], [qc.qubits[3]]]
    
    # Output register pieces of size 2w = 2 qubits each
    t_pieces = [
        [qc.qubits[4], qc.qubits[5]], 
        [qc.qubits[6], qc.qubits[7]], 
        [qc.qubits[8], qc.qubits[9]]
    ]
    anc = qc.qubits[10]
    
    # Let's set u = 3 (binary 11) and v = 3 (binary 11)
    # Expected product u * v = 9
    qc.x(0) # u0 = 1
    qc.x(1) # u1 = 1
    qc.x(2) # v0 = 1
    qc.x(3) # v1 = 1
    
    print("Appending inline_karatsuba gate to circuit...")
    inline_karatsuba(qc, u_pieces, v_pieces, t_pieces, anc, sign=1)
    
    qc.measure_all()
    
    # Save memory and bypass device coupling map limits using matrix product state
    simulator = AerSimulator(method='matrix_product_state')
    
    print("Transpiling circuit (unconstrained)...")
    compiled_circuit = transpile(
        qc, 
        simulator, 
        coupling_map=None, 
        initial_layout=None,
        optimization_level=1
    )
    
    print("Running quantum simulation...")
    job = simulator.run(compiled_circuit, shots=1)
    result = job.result()
    counts = result.get_counts()
    
    measured_state = list(counts.keys())[0]
    reversed_state = measured_state[::-1]
    
    # Extract slices in LSB-first ordering
    t0_bits = reversed_state[4:6]
    t1_bits = reversed_state[6:8]
    t2_bits = reversed_state[8:10]
    
    # Reverse slice strings back to big-endian (MSB-first) for standard base-2 conversion
    t0 = int(t0_bits[::-1], 2)
    t1 = int(t1_bits[::-1], 2)
    t2 = int(t2_bits[::-1], 2)
    
    # Apply Gidney's shift-reconstruction formula: Product = Sum_i t_i * 2^(i*w)
    product = t0 * 1 + t1 * 2 + t2 * 4
    
    print(f"Classical Inputs: u = 3, v = 3")
    print(f"Quantum Measurement (Full State): {measured_state}")
    print(f"Extracted T Register Slices: {[t0, t1, t2]}")
    print(f"Reconstructed Product: {product} (Expected: 9)")
    
    if product == 9:
        print("STATUS: SUCCESS for Corrected Inline Karatsuba!")
    else:
        print("STATUS: FAILED (Check recursive slice calculations and adders).")

if __name__ == "__main__":
    test_inline_karatsuba_correct()



