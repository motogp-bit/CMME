import sys
import os
from typing import List


current_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(current_dir)
sys.path.append(parent_dir)

try:
    # 1. Try importing assuming test script is next to the 'motogp-bit-cmme' package folder
    from .AM import ToomCookMultiply, inline_karatsuba, RPM
    from .gates import get_scratch_size
    print("Successfully imported multipliers from package 'motogp_bit_cmme'!")
except ImportError:
    try:
        # 2. Try importing assuming test script is inside the 'motogp-bit-cmme' folder alongside AM.py
        import AM,gates
        print("Successfully imported multipliers from local directory flat files!")
    except ImportError as e:
        print("\n" + "="*80)
        print("IMPORT ERROR: Could not locate your codebase files ('AM.py' or 'gates.py').")
        print("To fix this, please ensure that:")
        print("  1. You have split the uploaded .txt file into its respective python files:")
        print("     AM.py, gates.py, SMM.py, and VS-CMME.py.")
        print("  2. This test script is placed EITHER inside the same directory as those files,")
        print("     OR right next to the 'motogp-bit-cmme' package directory.")
        print("="*80 + "\n")
        raise e

from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit_aer import AerSimulator

def test_russian_peasant():
    """
    Tests your RPM (Russian Peasant Multiplier) gate with small values.
    """
    print("\n" + "-"*50)
    print("TESTING: Russian Peasant Multiplier (RPM)")
    print("-"*50)
    
    n_a, n_b = 3, 3
    # RPM qubits = 2 * (n_a + n_b) + 1
    total_qubits = 2 * (n_a + n_b) + 1
    qc = QuantumCircuit(total_qubits)
    
    # Let's set a = 3 (binary 011) and b = 5 (binary 101)
    # Target R should register 3 * 5 = 15 (binary 001111)
    
    # a is qubits [0:3] -> LSB is 0, set to 1, 1, 0
    qc.x(0)
    qc.x(1)
    
    # b is qubits [3:6] -> set to 1, 0, 1
    qc.x(3)
    qc.x(5)
    
    # Append your RPM gate
    rpm_gate = RPM(n_a, n_b)
    qc.append(rpm_gate, qc.qubits)
    qc.measure_all()
    
    simulator = AerSimulator()
    compiled_circuit = transpile(qc, simulator)
    job = simulator.run(compiled_circuit, shots=1)
    result = job.result()
    counts = result.get_counts()
    
    # Find the measured state
    measured_state = list(counts.keys())[0]
    print(f"Classical Inputs: a = 3, b = 5")
    print(f"Quantum Measurement (Full State): {measured_state}")
    
    # Extract R bits (indices n_a + n_b to 2*(n_a + n_b))
    # Reverse string to match Qiskit's big-endian output order
    reversed_state = measured_state[::-1]
    r_start = n_a + n_b
    r_end = 2 * (n_a + n_b)
    r_bits = reversed_state[r_start:r_end]
    product = int(r_bits, 2)
    
    print(f"Extracted Product Register (R): {r_bits} -> Decimal: {product}")
    if product == 15:
        print("STATUS: SUCCESS for Russian Peasant Multiplier!")
    else:
        print("STATUS: FAILED (Check carry propagation logic).")


def test_toom_cook():
    """
    Tests your ToomCookMultiply gate with asymmetric inputs.
    """
    print("\n" + "-"*50)
    print("TESTING: Pebbled Toom-Cook 2.5 Multiplier")
    print("-"*50)
    
    n_a, n_b = 4, 6
    n_res = n_a + n_b
    cutoff = 4
    
    # Call your get_scratch_size function to allocate space safely
    n_scratch = get_scratch_size(n_a, n_b, cutoff)
    print(f"Calculated required scratch space: {n_scratch} qubits.")
    
    a_reg = QuantumRegister(n_a, 'a')
    b_reg = QuantumRegister(n_b, 'b')
    res_reg = QuantumRegister(n_res, 'res')
    scratch_reg = QuantumRegister(n_scratch, 'scratch')
    qc = QuantumCircuit(a_reg, b_reg, res_reg, scratch_reg)
    
    # Set a = 3 (binary 0011) and b = 5 (binary 000101)
    # Expected product = 15 (binary 0000001111)
    qc.x(a_reg[0])
    qc.x(a_reg[1])
    
    qc.x(b_reg[0])
    qc.x(b_reg[2])
    
    # Instantiate your ToomCookMultiply gate
    tc_gate = ToomCookMultiply(n_a, n_b, n_res, n_scratch, cutoff)
    qc.append(tc_gate, list(a_reg) + list(b_reg) + list(res_reg) + list(scratch_reg))
    
    # Measure only the output register to verify cleanliness
    qc.measure_all()
    
    simulator = AerSimulator()
    compiled_circuit = transpile(qc, simulator)
    job = simulator.run(compiled_circuit, shots=1)
    result = job.result()
    counts = result.get_counts()
    
    measured_state = list(counts.keys())[0]
    reversed_state = measured_state[::-1]
    
    # Extract res register (indices n_a + n_b to n_a + n_b + n_res)
    res_start = n_a + n_b
    res_end = n_a + n_b + n_res
    res_bits = reversed_state[res_start:res_end]
    product = int(res_bits, 2)
    
    # Extract scratchpad to verify it returned cleanly to |0> (essential for no decoherence!)
    scratch_bits = reversed_state[res_end : res_end + n_scratch]
    scratch_clean = all(bit == '0' for bit in scratch_bits)
    
    print(f"Classical Inputs: a = 3, b = 5")
    print(f"Extracted Product Register (res): {res_bits} -> Decimal: {product}")
    print(f"Extracted Scratchpad State: {scratch_bits}")
    
    if product == 15:
        print("STATUS: SUCCESS for Toom-Cook 2.5 Multiplier!")
        if scratch_clean:
            print("DECOHERENCE CHECK: PASSED! Scratchpad register was completely uncomputed to |0>.")
        else:
            print("DECOHERENCE CHECK: WARNING! Scratchpad contains garbage bits (entanglement hazard).")
    else:
        print("STATUS: FAILED (Check carry/headroom boundaries).")


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


if __name__ == "__main__":
    print("="*80)
    print("QUANTUM MULTIPLIERS TESTING SUITE FOR YOUR LOCAL CODEBASE")
    print("="*80)
    
    try:
        test_russian_peasant()
        test_toom_cook()
        test_inline_karatsuba()
    except Exception as e:
        print(f"\nTest execution stopped due to an error: {e}")
    
    print("\n" + "="*80)
    print("Testing complete. Place this script alongside your AM.py and gates.py files to run.")
    print("="*80)
