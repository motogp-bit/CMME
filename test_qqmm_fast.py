import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector

try:
    from SMM import QQ_Modular_Multiplier
except ImportError:
    try:
        from SMM_v6 import QQ_Modular_Multiplier
    except ImportError:
        raise ImportError(
            "Could not import QQ_Modular_Multiplier from SMM. "
            "Please ensure SMM.py is in the current directory."
        )

def run_simulation_case_fast(x_val: int, y_val: int, N: int, n: int = 6, m: int = 6):
    total_qubits = 3 * n + 2 + m
    print(f"Running fast Statevector simulation for: {x_val} * {y_val} (mod {N})")
    print(f"Configuration: n = {n} (cutoff=4), m = {m} | Total Qubits: {total_qubits}")
    print("-" * 75)
    qc_gate = QQ_Modular_Multiplier(n=n, N=N, m=m)
    qc = QuantumCircuit(qc_gate.num_qubits)
    
    for i in range(n):
        if (x_val >> i) & 1:
            qc.x(i)         
        if (y_val >> i) & 1:
            qc.x(n + i)     

    qc.append(qc_gate, range(qc_gate.num_qubits))    
    print("Simulating statevector...")
    state = Statevector(qc)
    state_dict = state.to_dict()
    
    highest_prob = 0.0
    best_state_str = ""
    for state_str, amplitude in state_dict.items():
        prob = np.abs(amplitude)**2
        if prob > highest_prob:
            highest_prob = prob
            best_state_str = state_str
    x_bits = best_state_str[-n:]
    y_bits = best_state_str[-(2*n):-n]
    P_bits = best_state_str[-(3*n + 1):-(2*n)]
    w_bits = best_state_str[-(3*n + 1 + m):-(3*n + 1)]
    
    measured_x = int(x_bits[::-1], 2)
    measured_y = int(y_bits[::-1], 2)
    measured_P = int(P_bits[::-1], 2)
    measured_w = int(w_bits[::-1], 2)
    
    expected_P = (x_val * y_val) % N
    
    print(f"Measured Input x: {measured_x} (Expected: {x_val})")
    print(f"Measured Input y: {measured_y} (Expected: {y_val})")
    print(f"Measured Modular Product P: {measured_P} (Expected: {expected_P})")
    print(f"Measured Fractional Carry w: {measured_w} (Expected: 0)")
    print(f"Simulation Success Probability: {highest_prob * 100:.2f}%")
    
    if measured_P == expected_P and measured_w == 0:
        print("STATUS: PASSED!")
    else:
        print("STATUS: FAILED!")
    print("-" * 75 + "\n")

if __name__ == "__main__":
    print("=================================================================")
    print("QISKIT STATEVECTOR MULTIPLIER TESTER (MEMORY AND CPU OPTIMIZED)")
    print("=================================================================\n")
    
    # Option A: Fast 26-qubit simulation (takes ~1-3 seconds on average CPU)
    """    try:
        run_simulation_case_fast(x_val=6, y_val=7, N=13, n=6, m=6)
    except Exception as e:
        print("Execution failed for n=6 configuration:", str(e))"""
        
    print("\nExecuting ultra-light 14-qubit test:")
    try:
        run_simulation_case_fast(x_val=3, y_val=2, N=7, n=3, m=5)
    except Exception as e:
        print("Execution failed for n=3 configuration:", str(e))
