import sys
import os
from typing import List

# =============================================================================
# FLEXIBLE IMPORT ROUTING
# Automatically detects if the test script is run from outside or inside the
# codebase directory, allowing clean imports.
# =============================================================================
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_dir)

try:
    from AM import inline_karatsuba, RPM
    print("Successfully imported multipliers from local directory 'AM.py'!")
except ImportError:
    try:
        from AM import inline_karatsuba, RPM
        print("Successfully imported multipliers from 'quantum_multipliers'!")
    except ImportError as e:
        print("\n" + "="*80)
        print("IMPORT ERROR: Please place this script next to 'AM.py' or 'quantum_multipliers.py'.")
        print("="*80 + "\n")
        raise e

from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit_aer import AerSimulator

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
