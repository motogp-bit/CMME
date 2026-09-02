from qiskit.circuit.library import SXdgGate
from qiskit import QuantumCircuit
import numpy as np 

def get_scratch_size(n_a: int, n_b: int, cutoff: int) -> int:
    if n_a < cutoff or n_b < cutoff or n_a <= 1 or n_b <= 1:
        return 1  
    
    i = n_b // 3
    j = n_a // 2
    
    len_sum_a = (n_a - j) + 1
    len_sum_b = max(i, n_b - (2 * i)) + 2
    current_level_scratch = 2 * (len_sum_a + len_sum_b)
    branch_a0_b0 = get_scratch_size(j, i, cutoff)
    branch_a1_b2 = get_scratch_size(n_a - j, n_b - (2 * i), cutoff)
    branch_sum = get_scratch_size(len_sum_a, len_sum_b, cutoff)
    return current_level_scratch + max(branch_a0_b0, branch_a1_b2, branch_sum)  

def copy(n: int, n1):
    qc = QuantumCircuit(n + n1)
    a = qc.qubits[:n]
    b = qc.qubits[n:n + n1]
    for i in range(n):
        qc.cx(a[i],b[i])
    return qc.to_gate()

def IP_adder(n_a: int, n_b: int):
    #a is always the smaller register
    qc = QuantumCircuit(n_a + n_b + 1)
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a:n_a + n_b]
    c = qc.qubits[-1]

    for i in range(n_a):
        qc.cx(c, a[i])
        qc.cx(c, b[i])
        qc.ccx(a[i], b[i], c)
        
    extension_size = n_b - n_a
    if extension_size > 0:
        for i in reversed(range(1, extension_size)):
            target = b[n_a + i]
            controls = [c] + b[n_a : n_a + i]
            qc.mcx(controls, target)
        qc.cx(c, b[n_a])
    for i in reversed(range(n_a)):
        qc.ccx(a[i], b[i], c)
        qc.cx(c, a[i])
        qc.cx(a[i], b[i])
        
    return qc.to_gate()

def OOP_adder(n_a : int, n_b: int):
    #b is the larger register
    qc = QuantumCircuit(n_a + 2 * n_b + 1)
    
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a : n_a + n_b]
    s = qc.qubits[n_a + n_b : n_a + 2 * n_b + 1]
    csxdg = SXdgGate().control(1)
    
    for i in range(n_b):
        b_qubit = b[i]
        c_in = s[i]
        c_out = s[i+1]
        
        if i < n_a:
            a_qubit = a[i]
            
            qc.csx(a_qubit, c_out)
            qc.csx(b_qubit, c_out)
            qc.cx(a_qubit, b_qubit)
            qc.csx(c_in, c_out)
            qc.cx(b_qubit, c_in)
            qc.append(csxdg, [c_in, c_out])
            
            qc.cx(a_qubit, b_qubit)
        else:
            qc.csx(b_qubit, c_out)
            qc.csx(c_in, c_out)
            qc.cx(b_qubit, c_in)
            qc.append(csxdg, [c_in, c_out])
            
    return qc.to_gate()

def gen_splits(max_bits: int, cutoff=11):
    dp = {}
    best_split = {}
    
    for n in range(1, cutoff + 1):
        dp[n] = 4 * (n ** 2) - 3 * n
        
    for n in range(cutoff + 1, max_bits + 1):
        min_cost = float('inf')
        optimal_k = n // 2 
        
        for k in range(1, n):
            size_x0 = k
            size_x1 = n - k
            size_mid = max(size_x0, size_x1) 
            cost_mults = dp[size_x1] + dp[size_x0] + dp[size_mid]
            cost_adders = 4 * (2 * n) + 4 * (2 * size_mid)
            total_cost = cost_mults + cost_adders
            
            if total_cost < min_cost:
                min_cost = total_cost
                optimal_k = k
        
        naive_cost = 4 * (n ** 2) - 3 * n
        if naive_cost < min_cost:
            dp[n] = naive_cost
            best_split[n] = None
        else:
            dp[n] = min_cost
            best_split[n] = optimal_k
            
    return best_split, dp

optimal_splits, min_gate_costs = gen_splits(32, cutoff=11)

def MAJ():
    qc = QuantumCircuit(3)
    a = qc.qubits[0]
    b = qc.qubits[1]
    c = qc.qubits[2]
    qc.cx(a,b)
    qc.cx(a,c)
    qc.ccx(c,b,a)
    return qc.to_gate()

def UMA():
    qc = QuantumCircuit(3)
    a = qc.qubits[0]
    b = qc.qubits[1]
    c = qc.qubits[2]   
    qc.ccx(c,b,a)
    qc.cx(a,c)
    qc.cx(c,b)
    return qc.to_gate()

def cuccaro_1(m: int):
    qc = QuantumCircuit(2*m + 1)
    x = qc.qubits[:m]
    y = qc.qubits[m:2*m]
    c = qc.qubits[-1]
    qc.append(MAJ(),[x[0], y[0], c])
    for i in range(m - 1):
        qc.append(MAJ(),[x[i+1],y[i+1],x[i]])
    return qc.to_gate()

def cuccaro_2(m: int):
    qc = QuantumCircuit(2*m + 1)
    x = qc.qubits[:m]
    y = qc.qubits[m:2*m]
    c = qc.qubits[-1]
    for i in reversed(range(m - 1)):
        qc.append(UMA(), [x[i + 1], y[i + 1], x[i]])
    qc.append(UMA(), [x[0], y[0], c])
    return qc.to_gate()
    
def cuccaro_inv(m: int):
    qc = QuantumCircuit(2 * m + 1)
    qc.append(cuccaro_1(m), qc.qubits)
    qc.append(cuccaro_2(m), qc.qubits)
    return qc.inverse().to_gate(label="cuccaro_inv")

def correction_g(m: int, phi: float):
    qc = QuantumCircuit(6 * m, name="correction_g")
    rx0 = qc.qubits[0 : m]
    rx1 = qc.qubits[m : 2 * m]
    ry0 = qc.qubits[2 * m : 3 * m]
    ry1 = qc.qubits[3 * m : 4 * m]
    rz0 = qc.qubits[4 * m : 5 * m]
    rz1 = qc.qubits[5 * m : 6 * m]
    dcx, dcy, dcz = rx0[m-1], ry0[m-1], rz0[m-1]

    for i in range(m - 1):
        for j in range(m - 1):
            wt = -phi * (2**(m-1 + i + j))
            
            qc.mcphase(wt, control_qubits=[dcx, ry1[i]], target_qubit=rz1[j])
            qc.mcphase(wt, control_qubits=[dcy, rx1[i]], target_qubit=rz1[j])
            qc.mcphase(wt, control_qubits=[rx1[i], ry1[j]], target_qubit=dcz)
            
    return qc.to_gate()
    
def add_at_offset(n, m, offset):
    qc = QuantumCircuit(n + m + 1)
    a = qc.qubits[0 : n]
    b = qc.qubits[n : n + m]
    ancilla = qc.qubits[-1]
    qc.append(IP_adder(n, m - offset), [*a, *b[offset:], ancilla])
    
    return qc.to_gate()

def interpol_phases(phi, points, m):
    q = 7
    M = np.zeros((q, q))
    for i, w in enumerate(points):
        for d in range(q):
            if w == float('inf'):
                M[i, d] = 1.0 if d == q - 1 else 0.0
            else:
                M[i, d] = w ** d
    M_inv = np.linalg.inv(M)
        
    phases = []
    for l in range(q):
        coeff_sum = sum(M_inv[d, l] * (2 ** (m * d)) for d in range(q))
        phases.append(phi * coeff_sum)
    return phases

def q_add(x_reg, y_reg, ancilla):
    m = len(x_reg)
    qc = QuantumCircuit(m + len(y_reg) + 1)
    qc.append(cuccaro_1(m), [*x_reg, *y_reg, ancilla])
    qc.append(cuccaro_2(m), [*x_reg, *y_reg, ancilla])
    return qc.to_gate()

def q_sub(x_reg, y_reg, ancilla):
    m = len(x_reg)
    qc = QuantumCircuit(m + len(y_reg) + 1)
    qc.append(cuccaro_2(m).inverse(), [*x_reg, *y_reg, ancilla])
    qc.append(cuccaro_1(m).inverse(), [*x_reg, *y_reg, ancilla])
    return qc.to_gate()