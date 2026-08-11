from collections import defaultdict
from qiskit import QuantumCircuit
import numpy as np


def karatsuba(a, b, n_a, n_b, optimal_splits): 
    if n_a == 1 and n_b == 1:
        qc = QuantumCircuit(3)
        qc.ccx(0, 1, 2)
        return qc.to_gate()
    k = optimal_splits.get(n_a, n_a // 2)
    odd = (n_a - k) != k 
    qc = QuantumCircuit(4*(n_a + n_b - k) + 3 + 2 *(k**2) + n_a*n_b - n_a*k - n_b*k)
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a: n_a + n_b]
    sum_a = qc.qubits[n_a + n_b: 2*n_a + n_b - k + 1]
    sum_b = qc.qubits[2*n_a + n_b - k + 1: 2*n_a + 2*n_b - 2*k + 2]
    p0 = qc.qubits[2*n_a + 2*n_b - 2*k + 2: 2*n_a + 2*n_b - 2*k + 2 + k**2]
    p2 = qc.qubits[2*n_a + 2*n_b - 2*k + 2 + k**2: 2*n_a + 2*n_b - 2*k + 2 + 2 *(k**2) + n_a*n_b - n_a*k - n_b*k]
    M = qc.qubits[2*n_a + 2*n_b - 2*k + 2 + 2 *(k**2) + n_a*n_b - n_a*k - n_b*k:3*n_a + 3*n_b - 4*k + 3 + 2 *(k**2) + n_a*n_b - n_a*k - n_b*k]
    R = qc.qubits[3*n_a + 3*n_b - 4*k + 3 + 2 *(k**2) + n_a*n_b - n_a*k - n_b*k: 4*n_a + 4*n_b - 4*k + 3 + 2 *(k**2) + n_a*n_b - n_a*k - n_b*k]
    anc = qc.qubits[-1]
    
    a1 = a[:k]
    a0 = a[k:n_a]
    b1 = b[:k]
    b0 = b[k:n_b]
    if odd:
        for i in range(len(a0)):
            qc.cx(a0[i],sum_a[i])
        for i in range(len(b0)):
            qc.cx(b0[i],sum_b[i])
        qc.append(IP_adder(k,len(a0)),[*a1,*sum_a,*anc])
        qc.append(IP_adder(k,len(b0)),[*b1,*sum_b,*anc])
    else:
        qc.append(OOP_adder(k),[*a1,*a0,*sum_a])
        qc.append(OOP_adder(k),[*b1,*b0,*sum_b])
    qc.append(karatsuba(len(a0),len(b0),[*a0,*b0,*p0]))
    qc.append(karatsuba(len(a1),len(b1),[*a1,*b1,*p2]))
    qc.append(karatsuba(len(sum_a), len(sum_b)), [*sum_a,*sum_b,*M])
    R0 = R[:len(p0)]
    R1 = R[k : k + len(M)]
    R2 = R[2*k : 2*k + len(p2)]
    
    for i in range(len(p0)):
        qc.cx(p0[i], R0[i])
        
    for i in range(len(p2)):
        qc.cx(p2[i], R2[i])
        
    qc.append(IP_adder(len(p0), len(M)).inverse(), [*p0, *M, anc])
    qc.append(IP_adder(len(p2), len(M)).inverse(), [*p2, *M, anc])
    
    qc.append(IP_adder(len(M), len(R1)), [*M, *R1, anc])
    
    qc.append(IP_adder(len(p2), len(M)), [*p2, *M, anc])
    qc.append(IP_adder(len(p0), len(M)), [*p0, *M, anc])
    
    qc.append(karatsuba(len(sum_a), len(sum_b)).inverse(), [*sum_a, *sum_b, *M])
    qc.append(karatsuba(len(a1), len(b1)).inverse(), [*a1, *b1, *p2])
    qc.append(karatsuba(len(a0), len(b0)).inverse(), [*a0, *b0, *p0])
    
    if odd:
        qc.append(IP_adder(k, len(b0)).inverse(), [*b1, *sum_b, anc])
        qc.append(IP_adder(k, len(a0)).inverse(), [*a1, *sum_a, anc])
        for i in reversed(range(len(b0))):
            qc.cx(b0[i], sum_b[i])
        for i in reversed(range(len(a0))):
            qc.cx(a0[i], sum_a[i])
    else:
        qc.append(OOP_adder(k).inverse(), [*b1, *b0, *sum_b])
        qc.append(OOP_adder(k).inverse(), [*a1, *a0, *sum_a])
    return qc.to_gate()
    
    
    
def RP(n_a, n_b):
    total_qubits = 2 * (n_a + n_b)
    qc = QuantumCircuit(total_qubits)
    
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a : n_a + n_b]
    R = qc.qubits[n_a + n_b : 2 * (n_a + n_b)]
    
    c_adder = OOP_adder(n_b, n_b + 1).to_gate().control(1)
    
    for i in range(n_a):
        acc_slice = R[i : i + n_b + 1]
        
        qc.append(c_adder, [a[i]] + b[:] + acc_slice)
        
    return qc.to_gate()

def ToomCookMN(n_a,n_b):
    ratio = n_b - n_a
    #CONTINUE
    
"""
def booth(a, b, n_a, n_b):
    #only viable for even bits
    qc = QuantumCircuit(2* n_a + 2* n_b + 5)
    
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a: n_a + n_b]
    R = qc.qubits[n_a + n_b: 2*n_a + 2*n_b]
    flags = qc.qubits[2*n_a + 2* n_b: 2* n_a + 2* n_b + 4]
    anc = qc.qubits[-1]
    
    if n_a <= n_b:
        mult, add = a, b
    else:
        mult, add = b, a
        
    for j in range(1, len(mult), 2):
        
        if j == 1:
            qc.append(booth_multiplexer_simple(), [mult[j], mult[j-1], *flags])
        else: 
            qc.append(booth_multiplexer(), [mult[j], mult[j-1], mult[j-2], *flags, anc])
        t0 = R[j-1 :]
        qc.append(IP_adder(len(add), len(t0)).to_gate().control(1), [flags[0], anc, *add, *t0])
        t1 = R[j :]
        qc.append(IP_adder(len(add), len(t1)).to_gate().control(1), [flags[1], anc, *add, *t1])
        qc.append(IP_adder(len(add), len(t0)).to_gate().inverse().control(1), [flags[2], anc, *add, *t0])
        qc.append(IP_adder(len(add), len(t1)).to_gate().inverse().control(1), [flags[3], anc, *add, *t1])
        if j == 1:
            qc.append(booth_multiplexer_simple().inverse(), [mult[j], mult[j-1], *flags])
        else: 
            qc.append(booth_multiplexer().inverse(), [mult[j], mult[j-1], mult[j-2], *flags, anc])
    #fix missing msb
"""

    
    
    
    
    
    
    

