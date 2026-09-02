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

def test_toom_cook(n_a: int, n_b: int, val_a: int, val_b: int):
    print("\n" + "-"*50)
    print(f"TESTING: Grouped Pebbled Toom-Cook 2.5 Multiplier ({n_a}x{n_b})")
    print("-" * 50)
    
    n_res = n_a + n_b
    cutoff = 11
    
    n_scratch = get_scratch_size(n_a, n_b, cutoff)
    print(f"Running full {n_a + n_b + n_res + n_scratch}-qubit test (recursive Toom-Cook 2.5)...")
    print(f"Calculated required scratch space: {n_scratch} qubits.")
    
    a_reg = QuantumRegister(n_a, 'a')
    b_reg = QuantumRegister(n_b, 'b')
    res_reg = QuantumRegister(n_res, 'res')
    scratch_reg = QuantumRegister(n_scratch, 'scratch')
    qc = QuantumCircuit(a_reg, b_reg, res_reg, scratch_reg)
    
    # Dynamic binary encoding of inputs (LSB-first)
    for bit_idx in range(n_a):
        if (val_a >> bit_idx) & 1:
            qc.x(a_reg[bit_idx])
            
    for bit_idx in range(n_b):
        if (val_b >> bit_idx) & 1:
            qc.x(b_reg[bit_idx])
            
    tc_gate = ToomCookMultiply(n_a, n_b, n_res, n_scratch, cutoff)
    qc.append(tc_gate, list(a_reg) + list(b_reg) + list(res_reg) + list(scratch_reg))
    
    qc.measure_all()
    run_simulation(qc, n_scratch, n_res, n_a, n_b, val_a, val_b)

if __name__ == "__main__":
    # Test 1: Basic Russian Peasant Multiplier (RPM)
    test_russian_peasant()
    test_toom_cook(n_a=4, n_b=6, val_a=3, val_b=5)
    test_toom_cook(n_a=8, n_b=12, val_a=181, val_b=2743)
    test_inline_karatsuba()


def test_inline_karatsuba():
    """
    Tests your Gidney-style inline_karatsuba with padded input blocks.
    """
    print("\n" + "-"*50)
    print("TESTING: Craig Gidney's Inline Karatsuba")
    print("-"*50)
    
    # Slices represent: m = 2 words, word size w = 1
    # Inputs will be structured as individual lists of qubit slices
    qc = QuantumCircuit(15) # Allocates enough space for test
    
    # Set up mock padded pieces
    u_pieces = [[qc.qubits[0]], [qc.qubits[1]]]
    v_pieces = [[qc.qubits[2]], [qc.qubits[3]]]
    t_pieces = [[qc.qubits[4], qc.qubits[5]], [qc.qubits[6], qc.qubits[7]], [qc.qubits[8], qc.qubits[9]]]
    anc = qc.qubits[-1]
    
    # Flip some bits to set inputs
    qc.x(0) # u0 = 1
    qc.x(2) # v0 = 1
    
    print("Invoking inline_karatsuba function...")
    try:
        inline_karatsuba(qc, u_pieces, v_pieces, t_pieces, anc, sign=1)
        print("inline_karatsuba call succeeded compilation!")
        print("STATUS: SUCCESS for Karatsuba structure compilation!")
    except Exception as e:
        print("Compilation Failed!")
        raise e

