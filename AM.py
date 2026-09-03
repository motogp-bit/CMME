from qiskit import QuantumCircuit
import numpy as np
from gates import IP_adder,cuccaro_1,cuccaro_2,cuccaro_inv
from typing import List

def schoolbook_multiplier(n_a: int, n_b: int, n_out: int):
    qc = QuantumCircuit(n_a + n_b + n_out)
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a : n_a + n_b]
    R = qc.qubits[n_a + n_b :]
    
    for i in range(n_a):
        for j in range(n_b):
            k = i + j
            controls = [a[i], b[j]]
            for idx in range(n_out - 1, k, -1):
                qc.mcx(controls + R[k:idx], R[idx])
            qc.mcx(controls, R[k])
            
    return qc.to_gate()

def inline_karatsuba(
    qc: QuantumCircuit,
    u_pieces: list,
    v_pieces: list,
    t_pieces: list,
    anc: any,
    sign: int = 1
):

    m = len(u_pieces)
    if m == 1:
        w_in = len(u_pieces[0])
        w_out = len(t_pieces[0])
        if sign == 1:
            qc.append(schoolbook_multiplier(w_in, w_in, w_out), [*u_pieces[0], *v_pieces[0], *t_pieces[0]])
        else:
            qc.append(schoolbook_multiplier(w_in, w_in, w_out).inverse(), [*u_pieces[0], *v_pieces[0], *t_pieces[0]])
        return
    if sign == -1:
        flat_u = [q for piece in u_pieces for q in piece]
        flat_v = [q for piece in v_pieces for q in piece]
        flat_t = [q for piece in t_pieces for q in piece]
        total_qubits = len(flat_u) + len(flat_v) + len(flat_t) + 1
        sub_qc = QuantumCircuit(total_qubits)
        w_in = len(u_pieces[0])
        w_out = len(t_pieces[0])
        sub_u = [list(sub_qc.qubits[i * w_in : (i + 1) * w_in]) for i in range(m)]
        sub_v = [list(sub_qc.qubits[m * w_in + i * w_in : m * w_in + (i + 1) * w_in]) for i in range(m)]
        sub_t = [list(sub_qc.qubits[2 * m * w_in + i * w_out : 2 * m * w_in + (i + 1) * w_out]) for i in range(2 * m - 1)]
        sub_anc = sub_qc.qubits[-1]
        inline_karatsuba(sub_qc, sub_u, sub_v, sub_t, sub_anc, sign=1)
        qc.append(sub_qc.to_gate(label=f"inline_karatsuba_{m}_inv").inverse(), [*flat_u, *flat_v, *flat_t, anc])
        return

    h = m // 2
    for i in range(h, len(t_pieces)):
        w_out = len(t_pieces[0])
        qc.append(IP_adder(w_out, w_out), [*t_pieces[i - h], *t_pieces[i], anc])
    # Recursive on low halves
    inline_karatsuba(qc, u_pieces[:h], v_pieces[:h], t_pieces[:2 * h - 1], anc, sign=1)
    # Recursive on high halves
    inline_karatsuba(qc, u_pieces[h:], v_pieces[h:], t_pieces[h : h + 2 * (m - h) - 1], anc, sign=-1)
    for i in reversed(range(h, len(t_pieces))):
        w_out = len(t_pieces[0])
        qc.append(IP_adder(w_out, w_out).inverse(), [*t_pieces[i - h], *t_pieces[i], anc])

    w_in = len(u_pieces[0])
    for i in range(h):
        qc.append(cuccaro_1(w_in), [*u_pieces[i + h], *u_pieces[i], anc])
        qc.append(cuccaro_2(w_in), [*u_pieces[i + h], *u_pieces[i], anc])
        
        qc.append(cuccaro_1(w_in), [*v_pieces[i + h], *v_pieces[i], anc])
        qc.append(cuccaro_2(w_in), [*v_pieces[i + h], *v_pieces[i], anc])

    # Sum multiplication
    inline_karatsuba(qc, u_pieces[:h], v_pieces[:h], t_pieces[h : h + 2 * h - 1], anc, sign=1)
    for i in range(h):
        qc.append(cuccaro_inv(w_in), [*u_pieces[i + h], *u_pieces[i], anc])
        qc.append(cuccaro_inv(w_in), [*v_pieces[i + h], *v_pieces[i], anc])

