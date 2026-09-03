from qiskit import QuantumCircuit
import numpy as np
from gates import IP_adder,cuccaro_1,cuccaro_2,cuccaro_inv
from typing import List

def RPM(n_a: int, n_b: int):
    total_qubits = 2 * (n_a + n_b) + 1
    qc = QuantumCircuit(total_qubits)
    
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a : n_a + n_b]
    R = qc.qubits[n_a + n_b : 2 * (n_a + n_b)]
    anc = qc.qubits[-1]
    
    for i in range(n_a):
        acc_slice = R[i : i + n_b + 1]  
        c_adder = IP_adder(n_b, n_b + 1).control(1)  
        qc.append(c_adder, [a[i]] + b[:] + acc_slice + [anc])
    return qc.to_gate(label="RPM")

def inline_karatsuba(
    qc: QuantumCircuit, 
    u_pieces: List[List], 
    v_pieces: List[List], 
    t_pieces: List[List], 
    anc: any, 
    sign: int = 1
):
    m = len(u_pieces)
    if m == 1:
        base_qc = QuantumCircuit(len(u_pieces[0]) + len(v_pieces[0]) + len(t_pieces[0]))
        for idx_u in range(len(u_pieces[0])):
            for idx_v in range(len(v_pieces[0])):
                out_idx = idx_u + idx_v
                if out_idx < len(t_pieces[0]):
                    base_qc.ccx(
                        base_qc.qubits[idx_u], 
                        base_qc.qubits[len(u_pieces[0]) + idx_v], 
                        base_qc.qubits[len(u_pieces[0]) + len(v_pieces[0]) + out_idx]
                    )
                    
        base_gate = base_qc.to_gate(label=f"BaseCase_x{sign}")
        if sign == 1:
            qc.append(base_gate, [*u_pieces[0], *v_pieces[0], *t_pieces[0]])
        else:
            qc.append(base_gate.inverse(), [*u_pieces[0], *v_pieces[0], *t_pieces[0]])
        return

    h = m // 2
    
    for i in range(h, len(t_pieces)):
        w_out = len(t_pieces[0])
        adder = IP_adder(w_out, w_out)
        if sign == -1:
            adder = adder.inverse()
        qc.append(adder, t_pieces[i - h] + t_pieces[i] + [anc])
    inline_karatsuba(qc, u_pieces[:h], v_pieces[:h], t_pieces[:2*h], anc, sign)
    inline_karatsuba(qc, u_pieces[h:], v_pieces[h:], t_pieces[h:3*h], anc, -sign)

    for i in reversed(range(h, len(t_pieces))):
        w_out = len(t_pieces[0])
        adder = IP_adder(w_out, w_out)
        if sign == 1:
            adder = adder.inverse()
        qc.append(adder, t_pieces[i - h] + t_pieces[i] + [anc])
    w_in = len(u_pieces[0])
    for i in range(h):
        qc.append(cuccaro_1(w_in), u_pieces[i + h] + u_pieces[i] + [anc])
        qc.append(cuccaro_2(w_in), u_pieces[i + h] + u_pieces[i] + [anc])
        
        qc.append(cuccaro_1(w_in), v_pieces[i + h] + v_pieces[i] + [anc])
        qc.append(cuccaro_2(w_in), v_pieces[i + h] + v_pieces[i] + [anc])
    inline_karatsuba(qc, u_pieces[:h], v_pieces[:h], t_pieces[h:3*h], anc, sign)
    for i in range(h):
        qc.append(cuccaro_inv(w_in), u_pieces[i + h] + u_pieces[i] + [anc])
        qc.append(cuccaro_inv(w_in), v_pieces[i + h] + v_pieces[i] + [anc])