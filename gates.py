from qiskit.circuit.library import SXdgGate
from qiskit import QuantumCircuit
import numpy as np 

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

def evaluations(n_a: int, n_b: int):
        qc = QuantumCircuit(4*i + 7)
        i = n_b // 3
        b0 = qc.qubits[:i]
        b1 = qc.qubits[i:2*i]
        b2 = qc.qubits[2*i:]
        j = n_a // 2 
        temp = len(b2) + 2*i
        a0 = qc.qubits[temp: temp +j]
        a1 = qc.qubits[temp +j:temp + 2*j]
        temp = temp + len(a1) + 2*j
        temp_xq = qc.qubits[temp: temp + i + 1]
        temp_yq = qc.qubits[temp + i+1: temp + 2*i + 3]
        temp_xr = qc.qubits[temp + 2*i + 3: temp + 3*i + 4]
        temp_yr = qc.qubits[temp + 3*i + 4: temp + 4*i + 6]
        anc = qc.qubits[-1]
        qc.append(copy(len(a0),len(temp_xq)), [*a0,*temp_xq])
        qc.append(copy(len(b0), len(temp_yq)), [*b0,*temp_yq])
        qc.append(copy(len(a0), len(temp_xr)), [*a0,*temp_xr])
        qc.append(copy(len(b0), len(temp_yr)), [*b0,*temp_yr])
        qc.append(IP_adder(len(a1), len(temp_xq)),[*a1, *temp_xq, anc])
        qc.append(IP_adder(len(b1), len(temp_yq)),[*b1,*temp_yq, anc])
        qc.append(IP_adder(len(b2), len(temp_yq))[*b2, *temp_yq,  anc])
        qc.append(IP_adder(len(a1).inverse(), len(temp_xr))[*a1, *temp_xr,  anc])
        qc.append(IP_adder(len(b1).inverse(), len(temp_yr))[*b2, *temp_yr,  anc])
        qc.append(IP_adder(len(b2), len(temp_yr))[*b2, *temp_yr,  anc])
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

def q_add(qc, x_reg, y_reg, ancilla):
    m = len(x_reg)
    qc.append(cuccaro_1(m), [*x_reg, *y_reg, ancilla])
    qc.append(cuccaro_2(m), [*x_reg, *y_reg, ancilla])
    return qc.to_gate()

def q_sub(qc, x_reg, y_reg, ancilla):
    m = len(x_reg)
    qc.append(cuccaro_2(m).inverse(), [*x_reg, *y_reg, ancilla])
    qc.append(cuccaro_1(m).inverse(), [*x_reg, *y_reg, ancilla])
    return qc.to_gate()