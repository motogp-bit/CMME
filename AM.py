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

def ToomCook25(qc, a, b, res, scratch, dcheck, cutoff = 11, d = 0):
    n_a = len(a)
    n_b = len(b)
    n_res = len(res)
    if n_a > n_b:
        ToomCook25(qc, b, a, res, scratch, dcheck, cutoff, d)
    elif n_a < cutoff or n_b < cutoff:
        qc.append(RPM(n_a,n_b), [*a,*b,*res[:n_a + n_b]])
    elif n_b > 1.5 * n_a:
        i = n_b // 3
        j = n_a // 2        
        b0, b1, b2 = b[:i], b[i:2*i], b[2*i:]
        a0, a1 = a[:j], a[j:]
        temp_xq = scratch[:i + 1]
        temp_yq = scratch[i+1 : 2*i + 3]
        temp_xr = scratch[2*i + 3 : 3*i + 4]
        temp_yr = scratch[3*i + 4 : 4*i + 6]
        anc = scratch[4*i + 6]
        rest = scratch[4*i + 7:]
        qc.append(evaluations(n_a, n_b),[*b0, *b1, *b2, *a0, *a1, *temp_xq, *temp_yq, *temp_xr, *temp_yr, anc])
        if d != dcheck:
            P = rest[:2*i]
            Q = rest[2*i: 4*i + 3]
            R = rest[4*i + 3: 6*i + 6]
            S = rest[6*i + 6: 8*i + 6]
            c_scratch = rest[8*i + 6:]
            ToomCook25(qc, a0, b0, P, c_scratch, dcheck, cutoff, d + 1)
            ToomCook25(qc, temp_xq, temp_yq, Q, c_scratch, dcheck, cutoff, d + 1)
            ToomCook25(qc, temp_xr, temp_yr, R, c_scratch, dcheck, cutoff, d + 1)
            ToomCook25(qc, a1, b2, S, c_scratch, dcheck, cutoff, d + 1)
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
            master_scratch = rest[:2*i + 3]
            c_scratch = rest[2*i + 3:]
            p_sub_qubits = [*a0, *b0, *master_scratch[:2*i], *c_scratch]
            p_sub_qc = QuantumCircuit(len(p_sub_qubits))
            ToomCook25(
                p_sub_qc, 
                p_sub_qc.qubits[:len(a0)], 
                p_sub_qc.qubits[len(a0):len(a0)+len(b0)], 
                p_sub_qc.qubits[len(a0)+len(b0):len(a0)+len(b0)+2*i], 
                p_sub_qc.qubits[len(a0)+len(b0)+2*i:], 
                dcheck, cutoff, d + 1
            )
            p_gate = p_sub_qc.to_gate(label=f"Toom_P_d{d}")
            
            qc.append(p_gate, p_sub_qubits) 
            for idx in range(2*i): qc.cx(master_scratch[idx], res[idx]) 
            qc.append(p_gate.inverse(), p_sub_qubits) 
            q_sub_qubits = [*temp_xq, *temp_yq, *master_scratch, *c_scratch]
            q_sub_qc = QuantumCircuit(len(q_sub_qubits))
            ToomCook25(
                q_sub_qc, 
                q_sub_qc.qubits[:len(temp_xq)], 
                q_sub_qc.qubits[len(temp_xq):len(temp_xq)+len(temp_yq)], 
                q_sub_qc.qubits[len(temp_xq)+len(temp_yq):len(temp_xq)+len(temp_yq)+2*i+3], 
                q_sub_qc.qubits[len(temp_xq)+len(temp_yq)+2*i+3:], 
                dcheck, cutoff, d + 1
            )
            q_gate = q_sub_qc.to_gate(label=f"Toom_Q_d{d}")
            
            qc.append(q_gate, q_sub_qubits) 
            qc.append(IP_adder(2*i + 2, n_res - i), [*master_scratch[1:], *res[i:], anc])
            qc.append(IP_adder(2*i + 2, n_res - 2*i), [*master_scratch[1:], *res[2*i:], anc])
            qc.append(q_gate.inverse(), q_sub_qubits) 
            
            r_sub_qubits = [*temp_xr, *temp_yr, *master_scratch, *c_scratch]
            r_sub_qc = QuantumCircuit(len(r_sub_qubits))
            ToomCook25(
                r_sub_qc, 
                r_sub_qc.qubits[:len(temp_xr)], 
                r_sub_qc.qubits[len(temp_xr):len(temp_xr)+len(temp_yr)], 
                r_sub_qc.qubits[len(temp_xr)+len(temp_yr):len(temp_xr)+len(temp_yr)+2*i+3], 
                r_sub_qc.qubits[len(temp_xr)+len(temp_yr)+2*i+3:], 
                dcheck, cutoff, d + 1
            )
            r_gate = r_sub_qc.to_gate(label=f"Toom_R_d{d}")
            
            qc.append(r_gate, r_sub_qubits) 
            qc.append(IP_adder(2*i + 2, n_res - i).inverse(), [*master_scratch[1:], *res[i:], anc])
            qc.append(IP_adder(2*i + 2, n_res - 2*i), [*master_scratch[1:], *res[2*i:], anc])
            qc.append(r_gate.inverse(), r_sub_qubits)
            s_sub_qubits = [*a1, *b2, *master_scratch[:2*i], *c_scratch]
            s_sub_qc = QuantumCircuit(len(s_sub_qubits))
            ToomCook25(
                s_sub_qc, 
                s_sub_qc.qubits[:len(a1)], 
                s_sub_qc.qubits[len(a1):len(a1)+len(b2)], 
                s_sub_qc.qubits[len(a1)+len(b2):len(a1)+len(b2)+2*i], 
                s_sub_qc.qubits[len(a1)+len(b2)+2*i:], 
                dcheck, cutoff, d + 1
            )
            s_gate = s_sub_qc.to_gate(label=f"Toom_S_d{d}")
            qc.append(s_gate, s_sub_qubits) 
            qc.append(IP_adder(2*i, n_res - 3*i), [*master_scratch[:2*i], *res[3*i:], anc])
            qc.append(IP_adder(2*i, n_res - i).inverse(), [*master_scratch[:2*i], *res[i:], anc])
            qc.append(s_gate.inverse(), s_sub_qubits)
            qc.append(evaluations(n_a, n_b).inverse(), [*b0, *b1, *b2, *a0, *a1, *temp_xq, *temp_yq, *temp_xr, *temp_yr, anc])

def ToomCook8Way():
    #WIP
def ToomCookMultiply(n_a, n_b, cutoff):
    nplog = np.frompyfunc(log, 2, 1)
    N = nplog(max(n_a,n_b) / cutoff,6)
    k = np.floor(0.738 * N)
    dcheck = N - k
    qc = QuantumCircuit()
    qc.append(ToomCookMultiply(n_a, n_b, n_a + n_b, dcheck, cutoff)[])
    
    
    


    
    
    
    
    
    
    

