import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister, transpile

# Import your core SMM module
try:
    from SMM import QQ_Modular_Multiplier
except ImportError:
    try:
        from SMM_v5 import QQ_Modular_Multiplier
    except ImportError:
        raise ImportError(
            "Could not import QQ_Modular_Multiplier from SMM. "
            "Please make sure your modular multiplier file is named 'SMM.py'."
        )

# Configure the Matrix Product State (MPS) simulator
try:
    from qiskit_aer import AerSimulator
    simulator = AerSimulator(method='matrix_product_state')
except ImportError:
    try:
        from qiskit.providers.aer import AerSimulator
        simulator = AerSimulator(method='matrix_product_state')
    except ImportError:
        raise ImportError(
            "Matrix Product State simulation requires 'qiskit-aer'. "
            "Please install it using: pip install qiskit-aer"
        )

def run_simulation_case_mps(x_val: int, y_val: int, N: int, n: int = 6, m: int = 10):
    print(f"Running MPS simulation for: {x_val} * {y_val} (mod {N}) | n = {n} qubits, m = {m}")
    print("-" * 75)
    
    # 1. Instantiate the combined circuit
    qc_gate = QQ_Modular_Multiplier(n=n, N=N, m=m)
    qc = QuantumCircuit(qc_gate.num_qubits)
    
    # 2. State Preparation (LSB-First)
    for i in range(n):
        if (x_val >> i) & 1:
            qc.x(i)         
        if (y_val >> i) & 1:
            qc.x(n + i)     

    # 3. Append modular multiplier
    qc.append(qc_gate, range(qc_gate.num_qubits))
    
    # 4. Map Classical Registers and Measure Qubits
    cr_x = ClassicalRegister(n, 'x_meas')
    cr_y = ClassicalRegister(n, 'y_meas')
    cr_P = ClassicalRegister(n + 1, 'P_meas')
    cr_w = ClassicalRegister(m, 'w_meas')
    qc.add_register(cr_x, cr_y, cr_P, cr_w)
    
    # Qubit layout: x [0:n], y [n:2n], P [2n:3n+1], w [3n+1:3n+1+m]
    qc.measure(range(0, n), cr_x)
    qc.measure(range(n, 2 * n), cr_y)
    qc.measure(range(2 * n, 3 * n + 1), cr_P)
    qc.measure(range(3 * n + 1, 3 * n + 1 + m), cr_w)
    
    # 5. Transpile and Execute on the MPS Simulator
    tqc = transpile(qc, simulator)
    result = simulator.run(tqc, shots=1000).result()
    counts = result.get_counts()
    
    # Retrieve the state with the peak shot count
    peak_string = max(counts, key=counts.get)
    peak_count = counts[peak_string]
    prob = peak_count / 1000.0
    
    # Parse space-separated registers (Qiskit returns MSB-first: "w P y x")
    parts = peak_string.split(" ")
    w_bin, P_bin, y_bin, x_bin = parts[0], parts[1], parts[2], parts[3]
    
    measured_x = int(x_bin, 2)
    measured_y = int(y_bin, 2)
    measured_P = int(P_bin, 2)
    measured_w = int(w_bin, 2)
    
    expected_P = (x_val * y_val) % N
    
    print(f"Measured Input x: {measured_x} (Expected: {x_val})")
    print(f"Measured Input y: {measured_y} (Expected: {y_val})")
    print(f"Measured Modular Product P: {measured_P} (Expected: {expected_P})")
    print(f"Measured Fractional Carry w: {measured_w} (Expected: 0)")
    print(f"Simulation Success Probability: {prob * 100:.2f}% ({peak_count}/1000 shots)")
    
    if measured_P == expected_P and measured_w == 0:
        print("STATUS: PASSED!")
    else:
        print("STATUS: FAILED!")
    print("-" * 75 + "\n")

if __name__ == "__main__":
    try:
        run_simulation_case_mps(x_val=6, y_val=7, N=13, n=6, m=10)
        run_simulation_case_mps(x_val=5, y_val=4, N=11, n=6, m=10)
    except Exception as e:
        print("An error occurred during testing execution:", str(e))