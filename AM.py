from collections import defaultdict
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


def inline_karatsuba(qc: QuantumCircuit, 
                    input1: List[QuantumRegister], 
                    input2: List[QuantumRegister], 
                    output: List[QuantumRegister], 
                    anc: QuantumRegister,
                    sign: int = 1):

    n1 = len(input1)
    if n1 == 1:
        flat_in1 = [q for reg in input1 for q in reg]
        flat_in2 = [q for reg in input2 for q in reg]
        flat_out = [q for reg in output for q in reg]
        
        if sign == 1:
            qc.append(RPM(len(input1[0]), len(input2[0])), flat_in1 + flat_in2 + flat_out)
        else:
            qc.append(RPM(len(input1[0]), len(input2[0])).inverse(), flat_in1 + flat_in2 + flat_out)
        return

    h = n1 // 2
    
    a = input1[:h]
    b = input1[h:]
    x = input2[:h]
    y = input2[h:]

    for i in range(h, len(output)):
        qc.append(IP_adder(len(output[i - h]), len(output[i])), [*output[i - h], *output[i], *anc])

    inline_karatsuba(qc, a, x, output[:2*h], anc, sign)
    inline_karatsuba(qc, b, y, output[h:3*h], anc, -sign)
    for i in reversed(range(h, len(output))):
        qc.append(IP_adder(len(output[i - h]), len(output[i])).inverse(), [*output[i - h], *output[i], *anc])
    for i in range(h):
        qc.append(IP_adder(len(b[i]), len(a[i])), [*b[i], *a[i], *anc])
        qc.append(IP_adder(len(y[i]), len(x[i])), [*y[i], *x[i], *anc])

    inline_karatsuba(qc, a, x, output[h:3*h], anc, sign)

    for i in range(h):
        qc.append(IP_adder(len(b[i]), len(a[i])).inverse(), [*b[i], *a[i], *anc])
        qc.append(IP_adder(len(y[i]), len(x[i])).inverse(), [*y[i], *x[i], *anc])
    
def ToomCook25(qc: QuantumCircuit, a, b, res, scratch, dcheck: int, cutoff = 11, d = 0):
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

def ToomCook8Way():
    #WIP    
    


    
    
    
    
    
    
    

