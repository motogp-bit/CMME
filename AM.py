from qiskit import QuantumCircuit,QuantumRegister
from math import log
import numpy as np
from .gates import IP_adder,OOP_adder,evaluations
from typing import List
    
    
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

    
def ToomCook25(qc: QuantumCircuit, a, b, res, scratch, dcheck: int, cutoff = 11, d = 0):
    n_a = len(a)
    n_b = len(b)
    n_res = len(res)
    if n_a > n_b:
        ToomCook25(qc, b, a, res, scratch, dcheck, cutoff, d)
    elif n_a < cutoff or n_b < cutoff or n_b <= 1.5 * n_a:
        qc.append(RPM(n_a,n_b), [*a,*b,*res[:n_a + n_b]])
    else:
        i = n_b // 3
        j = n_a // 2        
        b0, b1, b2 = b[:i], b[i:2*i], b[2*i:]
        a0, a1 = a[:j], a[j:]
        anc = scratch
        sub_scratch = scratch[1:]
        if d != dcheck:
            qc.append(IP_adder(i, i), [*res[0:i], *res[2*i:3*i], anc])
            qc.append(IP_adder(i, i), [*res[i:2*i], *res[3*i:4*i], anc])
            qc.append(IP_adder(i, i), [*res[2*i:3*i], *res[4*i:5*i], anc])
            ToomCook25(qc, a0, b0, res[0:2*i], sub_scratch, dcheck, cutoff, d + 1)
            ToomCook25(qc, a1, b2, res[i:3*i], sub_scratch, dcheck, cutoff, d + 1, inverse=True)
            qc.append(IP_adder(i, i).inverse(), [*res[2*i:3*i], *res[4*i:5*i], anc])
            qc.append(IP_adder(i, i).inverse(), [*res[i:2*i], *res[3*i:4*i], anc])
            qc.append(IP_adder(i, i).inverse(), [*res[0:i], *res[2*i:3*i], anc])
            qc.append(IP_adder(i, i).inverse(), [*res[0:i], *res[i:2*i], anc])
            qc.append(IP_adder(i, i).inverse(), [*res[i:2*i], *res[2*i:3*i], anc])
            qc.append(IP_adder(i, i).inverse(), [*res[2*i:3*i], *res[3*i:4*i], anc])
            qc.append(IP_adder(i, i).inverse(), [*res[3*i:4*i], *res[4*i:5*i], anc])
            qc.append(IP_adder(j, j), [*a1, *a0, anc])
            qc.append(IP_adder(i, i), [*b1, *b0, anc])
            qc.append(IP_adder(i, i), [*b2, *b0, anc])
            ToomCook25(qc, a0, b0, res[i-1:3*i+2], sub_scratch, dcheck, cutoff, d + 1)
            qc.append(IP_adder(i, i).inverse(), [*b2, *b0, anc])
            qc.append(IP_adder(i, i).inverse(), [*b1, *b0, anc])
            qc.append(IP_adder(j, j).inverse(), [*a1, *a0, anc])
            qc.append(IP_adder(i, i), [*res[3*i:4*i], *res[4*i:5*i], anc])
            qc.append(IP_adder(i, i), [*res[2*i:3*i], *res[3*i:4*i], anc])
            qc.append(IP_adder(i, i), [*res[i:2*i], *res[2*i:3*i], anc])
            qc.append(IP_adder(i, i), [*res[0:i], *res[i:2*i], anc])
            qc.append(IP_adder(i, i), [*res[0:i], *res[i:2*i], anc])
            qc.append(IP_adder(i, i), [*res[i:2*i], *res[2*i:3*i], anc])
            qc.append(IP_adder(i, i), [*res[2*i:3*i], *res[3*i:4*i], anc])
            qc.append(IP_adder(i, i), [*res[3*i:4*i], *res[4*i:5*i], anc])
            qc.append(IP_adder(j, j).inverse(), [*a1, *a0, anc])
            qc.append(IP_adder(i, i).inverse(), [*b1, *b0, anc])
            qc.append(IP_adder(i, i), [*b2, *b0, anc])
            ToomCook25(qc, a0, b0, res[i-1:3*i+2], sub_scratch, dcheck, cutoff, d + 1, inverse=True)
            qc.append(IP_adder(i, i).inverse(), [*b2, *b0, anc])
            qc.append(IP_adder(i, i), [*b1, *b0, anc])
            qc.append(IP_adder(j, j), [*a1, *a0, anc])
            qc.append(IP_adder(i, i).inverse(), [*res[3*i:4*i], *res[4*i:5*i], anc])
            qc.append(IP_adder(i, i).inverse(), [*res[2*i:3*i], *res[3*i:4*i], anc])
            qc.append(IP_adder(i, i).inverse(), [*res[i:2*i], *res[2*i:3*i], anc])
            qc.append(IP_adder(i, i).inverse(), [*res[0:i], *res[i:2*i], anc])
        elif d == dcheck:
            p_sub_qubits = [*a0, *b0, *res[0:2*i], *sub_scratch]
            p_sub_qc = QuantumCircuit(len(p_sub_qubits))
            ToomCook25(p_sub_qc, p_sub_qc.qubits[:len(a0)], p_sub_qc.qubits[len(a0):len(a0)+len(b0)], p_sub_qc.qubits[len(a0)+len(b0):len(a0)+len(b0)+2*i], p_sub_qc.qubits[len(a0)+len(b0)+2*i:], dcheck, cutoff, d + 1)
            p_gate = p_sub_qc.to_gate(label=f"Toom_P_d{d}")
            qc.append(p_gate, [*a0, *b0, *res[0:2*i], *sub_scratch])

def ToomCookMultiply(n_a: int, n_b: int, n_res: int, n_scratch: int, cutoff: int):
    nplog = np.frompyfunc(log, 2, 1)
    N = nplog(max(n_a, n_b) / cutoff, 6)
    k = np.floor(0.738 * N)
    dcheck = int(N - k)
    a = QuantumRegister(n_a)
    b = QuantumRegister(n_b)
    res = QuantumRegister(n_res)
    scratch = QuantumRegister(n_scratch)
    qc = QuantumCircuit(a, b, res, scratch)
    ToomCook25(qc, a[:], b[:], res[:], scratch[:], dcheck, cutoff, 0)
    return qc.to_gate()




    
    
    
    
    
    
    

