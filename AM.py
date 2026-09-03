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
    """
    Recursively implements Craig Gidney's O(n) Space Quantum Karatsuba Multiplier
    using inline additions/subtractions directly into output pieces.
    
    This implementation resolves all slice truncation issues by preserving full-size 
    unitary additions and utilizes the exact 2-input signature of RPM(w_in, w_in).
    """
    m = len(u_pieces)
    if m == 1:
        # Base case: RPM multiplier with exactly two input parameters.
        # Spans exactly 4*w_in + 1 qubits.
        # We append RPM or its inverse directly inside qc.append without intermediate variables.
        w_in = len(u_pieces[0])
        if sign == 1:
            qc.append(RPM(w_in, w_in), [*u_pieces[0], *v_pieces[0], *t_pieces[0][:2 * w_in], anc])
        else:
            qc.append(RPM(w_in, w_in).inverse(), [*u_pieces[0], *v_pieces[0], *t_pieces[0][:2 * w_in], anc])
        return

    h = m // 2
    
    # 1. Scaling additions: t[h:] += t
    for i in range(h, len(t_pieces)):
        w_out = len(t_pieces[0])
        qc.append(IP_adder(w_out, w_out) if sign == 1 else IP_adder(w_out, w_out).inverse(), [*t_pieces[i - h], *t_pieces[i], anc])

    # 2. Recursive multiply-add for low halves
    inline_karatsuba(qc, u_pieces[:h], v_pieces[:h], t_pieces[:2*h], anc, sign)
    
    # 3. Recursive multiply-subtract for high halves
    inline_karatsuba(qc, u_pieces[h:], v_pieces[h:], t_pieces[h:3*h], anc, -sign)

    # 4. Scaling subtractions: t[h:] -= t
    for i in reversed(range(h, len(t_pieces))):
        w_out = len(t_pieces[0])
        qc.append(IP_adder(w_out, w_out).inverse() if sign == 1 else IP_adder(w_out, w_out), [*t_pieces[i - h], *t_pieces[i], anc])

    # 5. Symmetrical additions of operands: u_pieces[i] += u_pieces[i + h]
    w_in = len(u_pieces[0])
    for i in range(h):
        qc.append(cuccaro_1(w_in), [*u_pieces[i + h], *u_pieces[i], anc])
        qc.append(cuccaro_2(w_in), [*u_pieces[i + h], *u_pieces[i], anc])
        
        qc.append(cuccaro_1(w_in), [*v_pieces[i + h], *v_pieces[i], anc])
        qc.append(cuccaro_2(w_in), [*v_pieces[i + h], *v_pieces[i], anc])

    # 6. Sum multiplication: (u_low + u_high) * (v_low + v_high)
    inline_karatsuba(qc, u_pieces[:h], v_pieces[:h], t_pieces[h:3*h], anc, sign)

    # 7. Symmetrical uncomputation of input additions: u_pieces[i] -= u_pieces[i + h]
    for i in range(h):
        qc.append(cuccaro_inv(w_in), [*u_pieces[i + h], *u_pieces[i], anc])
        qc.append(cuccaro_inv(w_in), [*v_pieces[i + h], *v_pieces[i], anc])