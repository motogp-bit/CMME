from collections import defaultdict
from qiskit import QuantumCircuit
from math import log
import numpy as np
from .gates import IP_adder,OOP_adder,evaluations

def karatsuba(a: int, b: int, n_a: int, n_b: int, optimal_splits: int): 
    #implement craig gidney optimization
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
    
    
    
def RPM(n_a: int, n_b: int):
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

def ToomCook25(n_a, n_b, n_res, dcheck, cutoff = 11, d = 0):
    
    qc = QuantumCircuit()
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a:n_a + n_b]
    res = qc.qubits[n_a + n_b: n_a + n_b + n_res]
    if n_a < cutoff or n_b < cutoff:
        #qc.append(RPM(n_a,n_b),[*a,*b,*R])
    elif n_a > n_b:
        qc.append(ToomCook25(n_b, n_a, n_res, dcheck, cutoff, d), [*b, *a, *res])
    elif n_b > 1.5 * n_a:
        i = n_b // 3
        rest = qc.qubits[n_a + n_b + n_res: n_a + n_b + n_res + 12*i + 12]
        b0 = b[:i]
        b1 = b[i:2*i]
        b2 = b[2*i:]
        j = n_a // 2
        a0 = a[:j]
        a1 = a[j:2*j]
        temp_xq = rest[:i + 1]
        temp_yq = rest[i+1: 2*i + 3]
        temp_xr = rest[2*i + 3: 3*i + 4]
        temp_yr = rest[3*i + 4: 4*i + 6]
        rest = rest[4*i + 6:]
        anc = qc.qubits[-1]
        qc.append(evaluations(n_a, n_b),[*b0, *b1, *b2, *a0, *a1, *temp_xq, *temp_yq, *temp_xr, *temp_yr, anc])
        if d < dcheck:
            P = rest[:2*i]
            Q = rest[2*i: 4*i + 3]
            R = rest[4*i + 3: 6*i + 6]
            S = rest[6*i + 6: 8*i + 6]
            qc.append(ToomCook25(i, j), [*a0, *b0, *P])
            qc.append(ToomCook25(i+1, i+2),[*temp_xq, *temp_yq, *Q])
            qc.append(ToomCook25(i+1, i + 2),[*temp_xr, *temp_yr, *R])
            qc.append(ToomCook25(len(a1),len(b2)),[*a1,*b2,*S])
            qc.append(evaluations(n_a, n_b).inverse(), [*b0, *b1, *b2, *a0, *a1, *temp_xq, *temp_yq, *temp_xr, *temp_yr, anc])
            qc.append(IP_adder(2*i, n_res),[*P, *res[0:], anc])
            qc.append(IP_adder(2*i, n_res - 2*i).inverse(),[*P, *res[2*i:], anc])
            qc.append(IP_adder(2*i, n_res - 3*i),[*S, *res[3*i:], anc])
            qc.append(IP_adder(2*i, n_res - i).inverse(),[*S, *res[i:], anc])
            qc.append(IP_adder(2*i + 2, n_res - i),[*Q[1:], *res[i:], anc])
            qc.append(IP_adder(2*i + 2, n_res - 2*i),[*Q[1:], *res[2*i:], anc])
            qc.append(IP_adder(2*i + 2, n_res - i).inverse(),[*R[1:], *res[i:], anc])
            qc.append(IP_adder(2*i + 2, n_res - 2*i),[*R[1:], *res[2*i:], anc])
        elif d == dcheck:
    
        
    return qc.to_gate()

def ToomCook8Way():
    #WIP
def ToomCookMultiply(n_a, n_b, cutoff):
    nplog = np.frompyfunc(log, 2, 1)
    N = nplog(max(n_a,n_b) / cutoff,6)
    k = np.floor(0.738 * N)
    dcheck = N - k
    qc = QuantumCircuit()
    qc.append(ToomCookMultiply(n_a, n_b, dcheck, cutoff)[])
    
    
    


    
    
    
    
    
    
    

