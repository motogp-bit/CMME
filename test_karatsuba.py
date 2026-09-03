import sys
import os
import numpy as np

# =============================================================================
# FLEXIBLE IMPORT ROUTING
# =============================================================================
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_dir)

try:
    from quantum_multipliers import inline_karatsuba
    print("Successfully imported inline_karatsuba from package 'quantum_multipliers'!")
except ImportError:
    try:
        from AM import inline_karatsuba
        print("Successfully imported inline_karatsuba from local flat file 'AM.py'!")
    except ImportError as e:
        print("\n" + "="*80)
        print("IMPORT ERROR: Please ensure that 'quantum_multipliers.py' or 'AM.py'")
        print("is located in the same directory as this test script.")
        print("="*80 + "\n")
        raise e

from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit_aer import AerSimulator

def run_karatsuba_test(val_u: int, val_v: int, m: int = 2):
    """
    Dynamically configures and runs a Qiskit test for Gidney's Inline Karatsuba multiplier
    using your codebase, allowing you to test any arbitrary positive integers.
    """
    print("\n" + "-"*60)
    print(f"TEST CASE: {val_u} x {val_v} (m = {m} pieces)")
    print("-"*60)
    
    # 1. Determine minimum base word size w based on input values
    max_val = max(val_u, val_v, 1)
    n_bits = int(np.ceil(np.log2(max_val + 1)))
    w = int(np.ceil(n_bits / m))
    if w == 0:
        w = 1
        
    # 2. Apply Craig Gidney's padding theorem
    lg_m = int(np.ceil(np.log2(m)))
    w_in = w + lg_m if m > 1 else w
    w_out = 2 * w + 3 * lg_m if m > 1 else 2 * w
    
    print(f"Base Word Size (w): {w} bits")
    print(f"Padded Input Word Size (w_in): {w_in} qubits")
    print(f"Padded Output Word Size (w_out): {w_out} qubits")
    
    # 3. Allocate quantum registers
    u_reg = QuantumRegister(m * w_in, 'u')
    v_reg = QuantumRegister(m * w_in, 'v')
    t_reg = QuantumRegister((2 * m - 1) * w_out, 't')
    anc_reg = QuantumRegister(1, 'anc')
    
    qc = QuantumCircuit(u_reg, v_reg, t_reg, anc_reg)
    
    # 4. Encode inputs dynamically with X-gates
    for i in range(m):
        u_val = (val_u >> (i * w)) & ((1 << w) - 1)
        v_val = (val_v >> (i * w)) & ((1 << w) - 1)
        # Write to the first w bits of each word; the remaining are carry padding
        for bit_idx in range(w):
            if (u_val >> bit_idx) & 1:
                qc.x(u_reg[i * w_in + bit_idx])
            if (v_val >> bit_idx) & 1:
                qc.x(v_reg[i * w_in + bit_idx])
                
    # 5. Slice registers into List[List[Qubit]] Gidney-pieces
    u_pieces = [list(u_reg[i * w_in : (i + 1) * w_in]) for i in range(m)]
    v_pieces = [list(v_reg[i * w_in : (i + 1) * w_in]) for i in range(m)]
    t_pieces = [list(t_reg[i * w_out : (i + 1) * w_out]) for i in range(2 * m - 1)]
    anc = anc_reg[0]
    
    print(f"Total Circuit Qubits: {qc.num_qubits}")
    
    # Run forward multiplication (sign = 1)
    inline_karatsuba(qc, u_pieces, v_pieces, t_pieces, anc, sign=1)
    
    qc.measure_all()
    
    # 6. Simulate cleanly using MPS and unconstrained transpilation
    simulator = AerSimulator(method='matrix_product_state')
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
    
    # 7. Parsing of Gidney's padded output slices
    measured_state = list(counts.keys())[0]
    reversed_state = measured_state[::-1]
    
    # T register starts after u and v registers:
    t_start_idx = 2 * (m * w_in)
    
    extracted_slices = []
    reconstructed_product = 0
    
    for i in range(2 * m - 1):
        slice_start = t_start_idx + i * w_out
        slice_end = slice_start + w_out
        slice_bits = reversed_state[slice_start:slice_end]
        
        # Parse slice as LSB-first binary string, reversing to MSB-first for casting
        slice_val = int(slice_bits[::-1], 2)
        # Sign extension logic: If MSB is 1, it's negative
        if slice_bits[-1] == '1':
            slice_val -= (1 << w_out)
            
        extracted_slices.append(slice_val)
        reconstructed_product += slice_val * (2 ** (i * w))
        
    expected_product = val_u * val_v
    print(f"Extracted T Register Slices: {extracted_slices}")
    print(f"Reconstructed Product: {reconstructed_product} (Expected: {expected_product})")
    
    if reconstructed_product == expected_product:
        print("STATUS: SUCCESS for Gidney Inline Karatsuba!")
        return True
    else:
        print("STATUS: FAILED (Incorrect product reconstruction).")
        return False

if __name__ == "__main__":
    suite = [
        (1, 3, 2),
        (3, 3, 2),
        (11, 15, 2),
        (13, 19, 2),
        (23, 17, 2),
        (101, 89, 2),
    ]
    
    all_success = True
    for u, v, m in suite:
        success = run_karatsuba_test(u, v, m)
        if not success:
            all_success = False
            
    if all_success:
        print("\n" + "="*60)
        print("ALL INTERACTIVE KARATSUBA TESTS PASSED SUCCESSFULLY!")
        print("="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("SOME KARATSUBA TESTS FAILED. Please review calculations.")
        print("="*60 + "\n")