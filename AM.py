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
    
def DW(a, b, n_a, n_b, N):
    
def Booth(a, b, n_a, n_b, N):
    
