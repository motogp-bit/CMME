import sys
import os
from typing import List

current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_dir)


from AM import ToomCookMultiply, RPM, get_scratch_size



from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit_aer import AerSimulator



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

def test_toom_cook_grouped(n_a: int, n_b: int, val_a: int, val_b: int):
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
    
    # Test 3: Large 180-qubit Recursive Toom-Cook 2.5 (Fully bypasses the 30-qubit limit using MPS!)
    test_toom_cook_grouped(n_a=13, n_b=19, val_a=5023, val_b=524211)


