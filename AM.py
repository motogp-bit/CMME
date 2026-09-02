from qiskit import QuantumCircuit,QuantumRegister
from math import log
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

def ToomCook25(
    qc: QuantumCircuit,
    a: List,
    b: List,
    res: List,
    scratch: List,
    dcheck: int,
    cutoff: int = 4,
    d: int = 0,
    inverse: bool = False
):

    n_a = len(a)
    n_b = len(b)
    
    if n_a < cutoff or n_b < cutoff or n_a <= 1 or n_b <= 1:
        base_gate = RPM(n_a, n_b)
        if inverse:
            base_gate = base_gate.inverse()
        qc.append(base_gate, [*a, *b, *res, scratch[-1]])
        return

    i = n_b // 3
    j = n_a // 2
    
    a0, a1 = a[:j], a[j:]
    b0, b1, b2 = b[:i], b[i:2*i], b[2*i:]
    len_sum_a = len(a1) + 1
    len_sum_b = max(len(b0), len(b1), len(b2)) + 2
    len_prod = len_sum_a + len_sum_b
    prod_p = scratch[:len(a0)+len(b0)]
    prod_s = scratch[len(a0)+len(b0) : len(a0)+len(b0) + len(a1)+len(b2)]
    sum_a = scratch[len(a0)+len(b0) + len(a1)+len(b2) : len(a0)+len(b0) + len(a1)+len(b2) + len_sum_a]
    sum_b = scratch[len(a0)+len(b0) + len(a1)+len(b2) + len_sum_a : len(a0)+len(b0) + len(a1)+len(b2) + len_sum_a + len_sum_b]
    diff_a = scratch[len(a0)+len(b0) + len(a1)+len(b2) + len_sum_a + len_sum_b : len(a0)+len(b0) + len(a1)+len(b2) + 2*len_sum_a + len_sum_b]
    diff_b = scratch[len(a0)+len(b0) + len(a1)+len(b2) + 2*len_sum_a + len_sum_b : len(a0)+len(b0) + len(a1)+len(b2) + 2*len_sum_a + 2*len_sum_b]
    prod_q = scratch[len(a0)+len(b0) + len(a1)+len(b2) + 2*len_sum_a + 2*len_sum_b : len(a0)+len(b0) + len(a1)+len(b2) + 2*len_sum_a + 2*len_sum_b + len_prod]
    prod_r = scratch[len(a0)+len(b0) + len(a1)+len(b2) + 2*len_sum_a + 2*len_sum_b + len_prod : len(a0)+len(b0) + len(a1)+len(b2) + 2*len_sum_a + 2*len_sum_b + 2*len_prod]
    sub_scratch = scratch[len(a0)+len(b0) + len(a1)+len(b2) + 2*len_sum_a + 2*len_sum_b + 2*len_prod : -1]
    anc = scratch[-1]
    pebble_uncompute = (d < dcheck) or (d == 0)

    if not inverse:
        ToomCook25(qc, a0, b0, prod_p, sub_scratch, dcheck, cutoff, d + 1, False)
        ToomCook25(qc, a1, b2, prod_s, sub_scratch, dcheck, cutoff, d + 1, False)
        qc.append(IP_adder(len(prod_p), len(res)), [*prod_p, *res, anc])
        qc.append(IP_adder(len(prod_p), len(res) - 2*i).inverse(), [*prod_p, *res[2*i:], anc])
        qc.append(IP_adder(len(prod_s), len(res) - 3*i), [*prod_s, *res[3*i:], anc])
        qc.append(IP_adder(len(prod_s), len(res) - i).inverse(), [*prod_s, *res[i:], anc])
        for idx in range(len(a0)):
            qc.cx(a0[idx], sum_a[idx])
        qc.append(IP_adder(len(a1), len_sum_a), [*a1, *sum_a, anc])
        for idx in range(len(b0)):
            qc.cx(b0[idx], sum_b[idx])
        qc.append(IP_adder(len(b1), len_sum_b - 1), [*b1, *sum_b[:-1], anc])
        qc.append(IP_adder(len(b2), len_sum_b), [*b2, *sum_b, anc])
        ToomCook25(qc, sum_a, sum_b, prod_q, sub_scratch, dcheck, cutoff, d + 1, False)
        qc.append(IP_adder(len(prod_q), len(res) - (2*i - 1)), [*prod_q, *res[2*i - 1:], anc])
        qc.append(IP_adder(len(prod_q), len(res) - (i - 1)), [*prod_q, *res[i - 1:], anc])
        if pebble_uncompute:
            ToomCook25(qc, sum_a, sum_b, prod_q, sub_scratch, dcheck, cutoff, d + 1, True)
            qc.append(IP_adder(len(b2), len_sum_b).inverse(), [*b2, *sum_b, anc])
            qc.append(IP_adder(len(b1), len_sum_b - 1).inverse(), [*b1, *sum_b[:-1], anc])
            for idx in range(len(b0)):
                qc.cx(b0[idx], sum_b[idx])
            qc.append(IP_adder(len(a1), len_sum_a).inverse(), [*a1, *sum_a, anc])
            for idx in range(len(a0)):
                qc.cx(a0[idx], sum_a[idx])
        for idx in range(len(a0)):
            qc.cx(a0[idx], diff_a[idx])
        qc.append(IP_adder(len(a1), len_sum_a).inverse(), [*a1, *diff_a, anc])
        for idx in range(len(b0)):
            qc.cx(b0[idx], diff_b[idx])
        qc.append(IP_adder(len(b1), len_sum_b - 1).inverse(), [*b1, *diff_b[:-1], anc])
        qc.append(IP_adder(len(b2), len_sum_b), [*b2, *diff_b, anc])
        ToomCook25(qc, diff_a, diff_b, prod_r, sub_scratch, dcheck, cutoff, d + 1, False)
        qc.append(IP_adder(len(prod_r), len(res) - (2*i - 1)), [*prod_r, *res[2*i - 1:], anc])
        qc.append(IP_adder(len(prod_r), len(res) - (i - 1)).inverse(), [*prod_r, *res[i - 1:], anc])
        if pebble_uncompute:
            ToomCook25(qc, diff_a, diff_b, prod_r, sub_scratch, dcheck, cutoff, d + 1, True)
            qc.append(IP_adder(len(b2), len_sum_b).inverse(), [*b2, *diff_b, anc])
            qc.append(IP_adder(len(b1), len_sum_b - 1), [*b1, *diff_b[:-1], anc])
            for idx in range(len(b0)):
                qc.cx(b0[idx], diff_b[idx])
            qc.append(IP_adder(len(a1), len_sum_a), [*a1, *diff_a, anc])
            for idx in range(len(a0)):
                qc.cx(a0[idx], diff_a[idx])
        ToomCook25(qc, a1, b2, prod_s, sub_scratch, dcheck, cutoff, d + 1, True)
        ToomCook25(qc, a0, b0, prod_p, sub_scratch, dcheck, cutoff, d + 1, True)
    else:
        ToomCook25(qc, a0, b0, prod_p, sub_scratch, dcheck, cutoff, d + 1, False)
        ToomCook25(qc, a1, b2, prod_s, sub_scratch, dcheck, cutoff, d + 1, False)
        if pebble_uncompute:
            for idx in range(len(a0)):
                qc.cx(a0[idx], diff_a[idx])
            qc.append(IP_adder(len(a1), len_sum_a).inverse(), [*a1, *diff_a, anc])
            for idx in range(len(b0)):
                qc.cx(b0[idx], diff_b[idx])
            qc.append(IP_adder(len(b1), len_sum_b - 1).inverse(), [*b1, *diff_b[:-1], anc])
            qc.append(IP_adder(len(b2), len_sum_b), [*b2, *diff_b, anc])
            ToomCook25(qc, diff_a, diff_b, prod_r, sub_scratch, dcheck, cutoff, d + 1, False)
        qc.append(IP_adder(len(prod_r), len(res) - (i - 1)), [*prod_r, *res[i - 1:], anc])
        qc.append(IP_adder(len(prod_r), len(res) - (2*i - 1)).inverse(), [*prod_r, *res[2*i - 1:], anc])
        ToomCook25(qc, diff_a, diff_b, prod_r, sub_scratch, dcheck, cutoff, d + 1, True)
        qc.append(IP_adder(len(b2), len_sum_b).inverse(), [*b2, *diff_b, anc])
        qc.append(IP_adder(len(b1), len_sum_b - 1), [*b1, *diff_b[:-1], anc])
        for idx in range(len(b0)):
            qc.cx(b0[idx], diff_b[idx])
        qc.append(IP_adder(len(a1), len_sum_a), [*a1, *diff_a, anc])
        for idx in range(len(a0)):
            qc.cx(a0[idx], diff_a[idx])
            
        if pebble_uncompute:
            for idx in range(len(a0)):
                qc.cx(a0[idx], sum_a[idx])
            qc.append(IP_adder(len(a1), len_sum_a), [*a1, *sum_a, anc])
            for idx in range(len(b0)):
                qc.cx(b0[idx], sum_b[idx])
            qc.append(IP_adder(len(b1), len_sum_b - 1), [*b1, *sum_b[:-1], anc])
            qc.append(IP_adder(len(b2), len_sum_b), [*b2, *sum_b, anc])
            ToomCook25(qc, sum_a, sum_b, prod_q, sub_scratch, dcheck, cutoff, d + 1, False)
        qc.append(IP_adder(len(prod_q), len(res) - (i - 1)).inverse(), [*prod_q, *res[i - 1:], anc])
        qc.append(IP_adder(len(prod_q), len(res) - (2*i - 1)).inverse(), [*prod_q, *res[2*i - 1:], anc])
        ToomCook25(qc, sum_a, sum_b, prod_q, sub_scratch, dcheck, cutoff, d + 1, True)
        qc.append(IP_adder(len(b2), len_sum_b).inverse(), [*b2, *sum_b, anc])
        qc.append(IP_adder(len(b1), len_sum_b - 1).inverse(), [*b1, *sum_b[:-1], anc])
        for idx in range(len(b0)):
            qc.cx(b0[idx], sum_b[idx])
        qc.append(IP_adder(len(a1), len_sum_a).inverse(), [*a1, *sum_a, anc])
        for idx in range(len(a0)):
            qc.cx(a0[idx], sum_a[idx])
        qc.append(IP_adder(len(prod_s), len(res) - i), [*prod_s, *res[i:], anc])
        qc.append(IP_adder(len(prod_s), len(res) - 3*i).inverse(), [*prod_s, *res[3*i:], anc])        
        qc.append(IP_adder(len(prod_p), len(res) - 2*i), [*prod_p, *res[2*i:], anc])
        qc.append(IP_adder(len(prod_p), len(res)).inverse(), [*prod_p, *res, anc])
        ToomCook25(qc, a1, b2, prod_s, sub_scratch, dcheck, cutoff, d + 1, True)
        ToomCook25(qc, a0, b0, prod_p, sub_scratch, dcheck, cutoff, d + 1, True)

def ToomCookMultiply(n_a: int, n_b: int, n_res: int, n_scratch: int, cutoff: int, inverse = False):
    nplog = np.frompyfunc(log, 2, 1)
    N = nplog(max(n_a, n_b) / cutoff, 6)
    k = np.floor(0.738 * N)
    dcheck = int(N - k)
    a = QuantumRegister(n_a)
    b = QuantumRegister(n_b)
    res = QuantumRegister(n_res)
    scratch = QuantumRegister(n_scratch)
    qc = QuantumCircuit(a, b, res, scratch)
    ToomCook25(qc, list(a), list(b), list(res), list(scratch), dcheck, cutoff, 0, inverse)
    return qc.to_gate()


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
        w = len(u_pieces[0])
        base_gate = RPM(w, w)
        if sign == -1:
            base_gate = base_gate.inverse()
        qc.append(base_gate, u_pieces[0] + v_pieces[0] + t_pieces[0] + [anc])
        return

    h = m // 2
    for i in range(h, len(t_pieces)):
        w_out = len(t_pieces)
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