from collections import defaultdict
from qiskit import QuantumCircuit


def karatsuba(a, b, n_a, n_b, N):
    qc = QuantumCircuit(4*(n_a + n_b - k) + 3 2 *(k**2) + n_a*n_b - n_a*k - n_b*k)
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a: n_a + n_b]
    sum_a = qc.qubits[n_a + n_b: 2*n_a + n_b - k + 1]
    sum_b = qc.qubits[2*n_a + n_b - k + 1: 2*n_a + 2*n_b - 2*k + 2]
    p0 = qc.qubits[2*n_a + 2*n_b - 2*k + 2: 2*n_a + 2*n_b - 2*k + 2 + k**2]
    p2 = qc.qubits[2*n_a + 2*n_b - 2*k + 2 + k**2: 2*n_a + 2*n_b - 2*k + 2 + 2 *(k**2) + n_a*n_b - n_a*k - n_b*k]
    M = qc.qubits[2*n_a + 2*n_b - 2*k + 2 + 2 *(k**2) + n_a*n_b - n_a*k - n_b*k:3*n_a + 3*n_b - 4*k + 3 + 2 *(k**2) + n_a*n_b - n_a*k - n_b*k]
    R = qc.qubits[3*n_a + 3*n_b - 4*k + 3 + 2 *(k**2) + n_a*n_b - n_a*k - n_b*k: 4*n_a + 4*n_b - 4*k + 3 + 2 *(k**2) + n_a*n_b - n_a*k - n_b*k]
    k = n_a // 2
    a1 = a[:k]
    a0 = a[k:n_a]
    b1 = b[:k]
    b0 = b[k:n_b]
    #adder sum_a = a0 + a1 
    #adder sum_b = b0 + b1
    #multiplier p0 = a0 * b0
    #multiplier p2 = a1 * b1
    #multiplier M = (a0 + a1) * (b0 + b1)
    R0 = R[:k]
    R1 = R[k:2*k]
    R2 = R[2*k:n_a + n_b]
    #adder R0 = P0
    #adder R1 = R1 + M
    #adder R1 = R1 - P0
    #adder R1 = R1 - P2
    #adder R2 = R2 + P2
    #reverse adder p0
    #reverse adder p2
    #reverse adder M
    #reverse adder sum_a
    #reverse adder sum_b
    return qc.to_gate()
    
    
    
def RP(a, b, n_a, n_b, N):
    qc = QuantumCircuit(2*(n_a + n_b))
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a: n_a + n_b]
    R = qc.qubits[n_a + n_b: 2*(n_a + n_b)]
    c_adder = adder.control(1)
    for i in range(n_a):
        acc_slice = R[i : i + n_b]
        qc.append(c_adder, [a[i]] + b[:] + acc_slice)
    return qc.to_gate()

"""
def Dadda(a, b, n_a, n_b, N):
    qc = QuantumCircuit()
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a: n_a + n_b]
    p = qc.qubits[n_a + n_b: n_a + n_b + n_a * n_b]
    columns = defaultdict(list)
    for i in range(n_a):
        for j in range(n_b):
            p_i = i * n_b + j
            qc.ccx(a[i],b[j],p[p_i])
            weight = i + j
            columns[weight].append(p[p_i])
    D = []
    Dj = 2
    hmax = max(n_a,n_b)
    for j in range(hmax):
        D[j] = Dj
        Dj = 3 * Dj // 2        
"""
    
def booth(a, b, n_a, n_b, N):
    qc = QuantumCircuit()
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a: n_a + n_b]
    R = qc.qubits[n_a + n_b: 2*n_a + 2*n_b]
    flags = qc.qubits[2*n_a + 2* n_b: 2* n_a + 2* n_b + 4]
    anc = qc.qubits[-1]
    mult,add = a,b if n_a <= n_b else b,a
    for j in range(1, len(mult), 2):
        if j == 1:
            qc.append(booth_multiplexer_simple(),[a[j],a[j-1],flags])
        else: 
            qc.append(booth_multiplexer(), [a[j],a[j-1],a[j-2],flags,anc])
        t0 = R[j-1: j - 1 + n_b]
        qc.append(c_adder(),[flags[0], *add, *t0])
        t1 = R[j : j + n_b]
        qc.append(c_adder(),[flags[1], *add, *t1])
        qc.append(c_subtractor(),[flags[2], *add, *t0])
        qc.append(c_subtractor(),[flags[3], *add, *t1])
        if j == 1:
            qc.append(booth_multiplexer_simple().inverse(),[a[j],a[j-1],flags])
        else: 
            qc.append(booth_multiplexer().inverse(), [a[j],a[j-1],a[j-2],flags,anc])
        return qc.to_gate()
    
    
    
    
    
    
    
        qc.append(c_adder())