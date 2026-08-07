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

"""
def Dadda(a, b, n_a, n_b, N):
    qc = QuantumCircuit()
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a: n_a + n_b]
    p = qc.qubits[n_a + n_b: n_a + n_b + n_a * n_b]
    columns = defaultdict(list)
    for i in range(n_a):
        for j in range(n_b):
            p_i = i * n_b + j
            qc.ccx(a[i],b[j],p[p_i])
            weight = i + j
            columns[weight].append(p[p_i])
    D = []
    Dj = 2
    hmax = max(n_a,n_b)
    for j in range(hmax):
        D[j] = Dj
        Dj = 3 * Dj // 2        
"""
def booth(a, b, n_a, n_b):
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
            qc.append(booth_multiplexer_simple(), [mult[j], mult[j-1], flags])
        else: 
            qc.append(booth_multiplexer(), [mult[j], mult[j-1], mult[j-2], flags, anc])
        t0 = R[j-1 :]
        qc.append(IP_adder(len(add), len(t0)).to_gate().control(1), [anc, flags[0], *add, *t0])
        t1 = R[j :]
        qc.append(IP_adder(len(add), len(t1)).to_gate().control(1), [anc, flags[1], *add, *t1])
        qc.append(IP_adder(len(add), len(t0)).to_gate().inverse().control(1), [anc, flags[2], *add, *t0])
        qc.append(IP_adder(len(add), len(t1)).to_gate().inverse().control(1), [anc, flags[3], *add, *t1])
        if j == 1:
            qc.append(booth_multiplexer_simple().inverse(), [mult[j], mult[j-1], flags])
        else: 
            qc.append(booth_multiplexer().inverse(), [ ult[j], mult[j-1], mult[j-2], flags])
    #fix missing msb
    
    
def VDH():
    #empty


def QQMM(reg_zero, reg_x, reg_y, N, n, m):
    
    # === STEP 1: Q-MAC (Quantum-Quantum Shift-and-Reduce Multiplier) ===
    # Multiplies reg_x and reg_y, accumulating into reg_zero.
    # reg_x is left in the state |2^n * x mod N>
    Q_MAC_quantum_quantum(control_y=reg_y, target_x=reg_x, accumulator=reg_zero, modulus=N)
    
    # Virtual slicing of the reg_zero register:
    # reg_carry is the single MSB carry/comparison qubit: reg_zero[n+m]
    # reg_t is the lower n+m qubits holding the unreduced product: reg_zero[0 : n+m]
    reg_carry = reg_zero.slice(start=n+m, end=n+m+1)
    reg_t = reg_zero.slice(start=0, end=n+m)
    
    # === STEP 2: Q-REDC (Montgomery Reduction) ===
    # 2a. Estimation Stage:
    # m sequential steps of controlled in-place subtractions of (N-1)//2
    for k in range(m):
        # The LSB of the remaining active part of reg_t controls subtraction
        # on the bits above it
        controlled_subtract(
            control=reg_t[k], 
            target=reg_t[k+1 : n+m], 
            value=(N - 1) // 2
        )
        
    # Virtual slicing of the reduced accumulator:
    # reg_estimate consists of reg_t[m : n+m] + reg_carry at the top (size n+1)
    # reg_u consists of the lower m bits: reg_t[0 : m]
    reg_estimate = reg_t.slice(start=m, end=n+m).concat(reg_carry)
    reg_u = reg_t.slice(start=0, end=m)
    
    # 2b. Correction Stage:
    # Conditionally add N based on the sign qubit (MSB of the estimate, which is reg_carry)
    sign_bit = reg_carry
    controlled_add(control=sign_bit, target=reg_estimate, value=N)
    
    # Exorcise phase/garbage: CNOT controlled by the LSB of the modular product 
    # to restore the sign bit
    CNOT(control=reg_estimate, target=sign_bit)
    
    # Virtual concatenation: sign_bit and reg_u form the (m+1)-bit garbage register reg_u_tilde
    reg_u_tilde = reg_u.concat(sign_bit)
    
    # At this point:
    # reg_estimate now holds the clean product: |xy * 2^-m mod N>
    # reg_u_tilde holds the garbage: |u_tilde>_{m+1}
    
    # === STEP 3: Q-MUL (In-Place Classical Multiplication) ===
    # Reversibly multiply the garbage register in-place by classical N modulo 2^(m+1)
    Q_MUL_inplace_classical(register=reg_u_tilde, multiplier=N, modulo=2**(m+1))
    
    # === STEP 4: Q-MAC Adjoint (Truncated Reverse Multiplier) ===
    # Run the reverse shift-and-reduce multiplier truncated to m+1 bits to clear reg_u_tilde
    Q_MAC_adjoint_truncated(
        control_y=reg_y, 
        target_x=reg_x, 
        accumulator=reg_u_tilde, 
        modulus=N, 
        limit_bits=m+1
    )
    
    # Garbage register is now restored to |0>_{m+1}
    # reg_estimate contains the finalized Montgomery modular product

def quantum_quantum_modular_multiply_division(reg_x, reg_y, reg_zero, N, n, m):
    """
    Inputs:
      reg_x:    QuantumRegister of size n (holds |x>)
      reg_y:    QuantumRegister of size n (holds |y>)
      reg_zero: QuantumRegister of size n + m (initially |0>)
      N:        Classical modulus
      n:        Bit-width of N
      m:        Width of quotient register, ceil(log2(n))
    """
    # === STEP 1: Quantum-Quantum Q-MAC ===
    # Accumulate shifted, modularly reduced partial products of x and y.
    # reg_x is left in the state |2^n * x mod N>
    Q_MAC_quantum_quantum(control_y=reg_y, target_x=reg_x, accumulator=reg_zero, modulus=N)
    
    # === STEP 2: Q-DIV (Division Stage) ===
    # Identical to the quantum-classical case
    for k in range(m - 1, -1, -1):
        select_undo_subtract(target=reg_zero[k : n + m], value=2**k * N)
        NOT(reg_zero[n + k]) # Retrieve quotient bit q_k by inverting sign
        
    # Virtual slicing
    reg_q = reg_zero.slice(start=n, end=n+m)           # Upper m bits holding |q>
    reg_remainder = reg_zero.slice(start=0, end=n)     # Lower n bits holding |t mod N>

    # === STEP 3: Q-MUL ===
    # Multiply the quotient register in-place by classical N modulo 2^m
    Q_MUL_inplace_classical(register=reg_q, multiplier=N, modulo=2**m)

    # === STEP 4: LSB Addition ===
    # Add remainder LSBs to reconstruct the truncated product in reg_q (which becomes |t>_m)
    add_registers(source=reg_remainder[0 : m], target=reg_q)

    # === STEP 5: Truncated Quantum-Quantum Q-MAC Adjoint ===
    # Run the reverse shift-and-reduce multiplier truncated to m bits.
    # This clears reg_q back to |0> and restores reg_x to |x>
    Q_MAC_adjoint_truncated(
        control_y=reg_y, 
        target_x=reg_x, 
        accumulator=reg_q, 
        modulus=N, 
        limit_bits=m
    )
    
def quantum_quantum_modular_multiply_barrett(reg_x, reg_y, reg_S, reg_X_tilde_y, reg_q_tilde, reg_adj, N, n, m, nu_tilde):
    """
    Inputs:
      reg_x:          QuantumRegister of size n (holds |x>)
      reg_y:          QuantumRegister of size n (holds |y>)
      reg_S:          QuantumRegister of size n + m (accumulates full product)
      reg_X_tilde_y:  QuantumRegister of size 2m (first work register)
      reg_q_tilde:    QuantumRegister of size 2m (second work register)
      reg_adj:        QuantumRegister of size 1 (adjustment flag qubit)
      N:              Classical modulus
      n:              Bit-width of N
      m:              log2(n) + 1
      nu_tilde:       Classical precomputed Barrett value floor(2^(2n)/N)
    """
    # === STEP 1: Compute Full Product (Quantum-Quantum) ===
    # reg_x is shifted dynamically by reg_y to compute the full product xy into reg_S
    Q_MAC_quantum_quantum_unreduced(control_y=reg_y, target_x=reg_x, accumulator=reg_S)

    # === STEP 2: Compute Approximate Product (Quantum-Quantum) ===
    # Accumulate truncated shifted terms of reg_x controlled by reg_y into reg_X_tilde_y
    Q_MAC_quantum_quantum_approximate(control_y=reg_y, target_x=reg_x, accumulator=reg_X_tilde_y)

    # === STEP 3: Compute Approximate Reduction Factor ===
    # Multiply reg_X_tilde_y by classical nu_tilde in-place modulo 2^(2m) into reg_q_tilde
    Q_MUL_inplace_classical(register=reg_X_tilde_y, target=reg_q_tilde, multiplier=nu_tilde, modulo=2**(2*m))

    # === STEP 4: Primary Reduction ===
    # Subtract the quantum register product: reg_S = reg_S - reg_q_tilde * N
    controlled_subtract_quantum_quantum(control=reg_q_tilde, target=reg_S, multiplier=N)

    # === STEP 5: Conditional Adjustment (Steps 5-8) ===
    # Subtract N if reg_S >= N, setting the adjustment flag to 1
    compare_and_subtract_adjust(target_S=reg_S, modulus=N, flag=reg_adj)

    # === STEP 6: Prepare to Clear Flag (Step 9) ===
    # Add back the quantum register product: reg_S = reg_S + reg_q_tilde * N
    controlled_add_quantum_quantum(control=reg_q_tilde, target=reg_S, multiplier=N)

    # === STEP 7: Clear the Adjustment Flag (Steps 10-12) ===
    # Compare high-order bits of S with the approximate product register reg_X_tilde_y.
    # If S[high] - X_tilde_y < 0, CNOT flips reg_adj back to 0
    compare_high_and_flip_flag(target_S=reg_S, compare_reg=reg_X_tilde_y, flag=reg_adj)

    # === STEP 8: Restore Final Modular Product (Step 13) ===
    # Subtract reg_q_tilde * N from reg_S
    controlled_subtract_quantum_quantum(control=reg_q_tilde, target=reg_S, multiplier=N)

    # === STEP 9: Uncompute Garbage Work Registers (Steps 14-15) ===
    # Reverse Step 3
    Q_MUL_inplace_classical_adjoint(register=reg_X_tilde_y, target=reg_q_tilde, multiplier=nu_tilde, modulo=2**(2*m))
    
    # Reverse Step 2 (Truncated Quantum-Quantum MAC Adjoint)
    # This clears reg_X_tilde_y and completely restores reg_x to its original state |x>
    Q_MAC_quantum_quantum_approximate_adjoint(control_y=reg_y, target_x=reg_x, accumulator=reg_X_tilde_y)