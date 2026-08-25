#probably deprecated,saving the logic just in case
from qiskit import QuantumCircuit
from qiskit.circuit.libraries import DraperQFTAdder



def AND():
    qc = QuantumCircuit(3)
    x = qc.qubits[0]
    y = qc.qubits[1]
    ta = qc.qubits[2]
    qc.h(ta)
    qc.t(ta)
    qc.cx(x,ta)
    qc.cx(y,ta)
    qc.cx(ta,x)
    qc.cx(ta,y)
    qc.t(ta)
    qc.tdg(y)
    qc.tdg(x)
    qc.cx(ta,x)
    qc.cx(ta,y)
    qc.h(ta)
    qc.s(ta)
    return qc.to_gate()

def AND_adjoint():
    qc = QuantumCircuit(3, 1)
    x = qc.qubits[0]
    y = qc.qubits[1]
    ta = qc.qubits[2]
    
    qc.h(ta)
    qc.measure(ta, 0)
    
    qc.cz(x, y).c_if(0, 1)
    qc.reset(ta)
    return qc.to_instruction()
    
def MajAnd(a_i: int):
    qc = QuantumCircuit(3)
    x = qc.qubits[0]
    y = qc.qubits[1]
    ta = qc.qubits[2]
    if a_i:
        qc.x(x)
        qc.x(y)
        
    qc.append(AND(), [x, y, ta])
    
    if a_i:
        qc.x(x)
        qc.x(y)
    return qc.to_gate()

def UMajAnd(a_i: int):
    qc = QuantumCircuit(3,1)
    x = qc.qubits[0]
    y = qc.qubits[1]
    ta = qc.qubits[2]
    c = qc.clbits[0]
    if a_i:
        qc.x(x)
        qc.x(y)
        
    qc.append(AND_adjoint(), [x, y, ta],[c])
    
    if a_i:
        qc.x(x)
        qc.x(y)
    return qc.to_gate()

def ACMOD(a: int, n: int):
    qc = QuantumCircuit(2*n + 3,1)
    b = qc.qubits[:n]
    ancillas = qc.qubits[n: 2*n + 3]
    c = qc.clbits[0]
    a = a % (2**n)
    if not a:
        return 
        
    z = 0
    while not a % 2:
        a = a // 2
        z += 1
        
    n_prime = n - z
    b_active = b[z : n]
    a_bits = [(a >> i) & 1 for i in range(n_prime)] 
    if n_prime < 4:
        qc.append(fallback_small_adder(a_bits, n_prime), [*b_active])
        return
    anc = ancillas[0 : n_prime - 3]
    if a_bits[1]:
        qc.x(b_active[0])
        qc.x(b_active[1])
    qc.ccx(b_active[0], b_active[1], anc[0])
    
    if a_bits[1] ^ a_bits[2]:
        qc.x(anc[0])
    for i in range(2, n_prime - 2):
        if a_bits[i]:
            qc.x(b_active[i])
        qc.ccx(b_active[i], anc[i-2], anc[i-1])
        if a_bits[i] ^ a_bits[i+1]:
            qc.x(anc[i-1])

    if a_bits[n_prime-2]:
        qc.x(b_active[n_prime-2])
        qc.x(anc[n_prime-4])
    qc.ccx(b_active[n_prime-2], anc[n_prime-4], b_active[n_prime-1])
    if a_bits[n_prime-2]:
        qc.x(b_active[n_prime-2])
        qc.x(anc[n_prime-4])
    if a_bits[n_prime-2] ^ a_bits[n_prime-1]:
        qc.x(b_active[n_prime-1])

    for i in range(n_prime - 2, 1, -1):
        qc.cx(anc[i-2], b_active[i])
        if a_bits[i]:
            qc.x(b_active[i])
            
        if i > 2:
            qc.append(UMajAnd(a_bits[i-1]), [b_active[i-1], anc[i-3], anc[i-2]], [c])
        else: 
            qc.append(UMajAnd(a_bits[1]), [b_active[1], b_active[0], anc[0]],[c])
    qc.cx(b_active[0], b_active[1])
    if a_bits[1]:
        qc.x(b_active[1])
    qc.x(b_active[0])
    qc.cx(*[b_active[0], b_active[1]])
    if a_bits[1]:
        qc.x(*[b_active[1]])
        
    qc.x(*[b_active[0]])
    return qc.to_gate()



def CACMOD(a: int, n: int):
    qc = QuantumCircuit(2*n + 3,1)
    ctrl = qc.qubits[0]
    b = qc.qubits[1:n+1]
    ancillas = qc.qubits[n+1: 2*n + 3]
    c = qc.clbits[0]
    
    a = a % (2**n)
    if not a: 
        return
    z = 0
    while not a % 2:
        a = a // 2
        z += 1
    n_prime = n - z
    b_active = b[z : n]
    a_bits = [(a >> i) & 1 for i in range(n_prime)]
    anc = ancillas[0 : n_prime - 2] 
    qc.append(MajAnd(a_bits[1]), [b_active[1], b_active[0], anc[0]])
    if a_bits[1] ^ a_bits[2]:
        qc.x(anc[0])
    for i in range(2, n_prime - 1):
        qc.append(MajAnd(a_bits[i]), [b_active[i], anc[i-2], anc[i-1]])
        if a_bits[i] ^ a_bits[i+1]:
            qc.x(anc[i-1])
    qc.ccx(ctrl, anc[n_prime-3], b_active[n_prime-1])
    
    if a_bits[n_prime-1]:
        qc.cx(ctrl, b_active[n_prime-1])

    for i in range(n_prime - 2, 0, -1):
        qc.ccx(ctrl, anc[i-1], b_active[i])
        
        if a_bits[i]:
            qc.cx(ctrl, b_active[i])

    qc.cx(ctrl, b_active[0])

    for i in range(n_prime - 1, 1, -1):
        if i > 2:
            qc.append(UMajAnd(a_bits[i-1]), [b_active[i-1], anc[i-3], anc[i-2]],[c])
        else:
            qc.append(UMajAnd(a_bits[1]), [b_active[1], b_active[0], anc[0]],[c])
    return qc.to_gate()

def shift_and_reduce(N: int, n: int):
    qc = QuantumCircuit(2 * n + 5, 1)
    q = qc.qubits[:n+1]
    anc = qc.qubits[n+1:]
    c = qc.clbits[0]
    
    for i in range(n, 0, -1):
        qc.swap(q[i], q[i-1])
        
    acmod_inst = ACMOD(2**(n + 1) - N, n + 1)
    qc.append(acmod_inst, qc.qubits[:2 * n + 5], [c])

    cacmod_inst = CACMOD(N, n)
    cacmod_qubits = [q[n]] + q[:n] + anc[:n+2]
    qc.append(cacmod_inst, cacmod_qubits, [c])
    
    qc.x(q[n])
    qc.cx(q[0], q[n])
    
    return qc.to_instruction()

def QMA(n: int, N: int):
    qc = QuantumCircuit(3*n + 1)
    x = qc.qubits[:n]
    y = qc.qubits[n:2*n]
    acc = qc.qubits[2*n:3*n]
    anc = qc.qubits[-1]
    for i in range(n):
        qc.append(DraperQFTAdder(n).control(1), [*y[i],*x,*acc])
        qc.append(shift_and_reduce(N, n), [*x, anc])
    return qc.to_gate()

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

"""
def booth_multiplexer():
    qc = QuantumCircuit()
    z,y,x = qc.qubits[0],qc.qubits[1], qc.qubits[2]
    flag = qc.qubits[3:7]
    T = qc.qubits[7]
    qc.cx(y,T)
    qc.cx(z,T)
    qc.cx(T,flag[1])
    qc.ccx(x,T,flag[1])
    qc.ccx(x,T,flag[2])
    qc.x(x)
    qc.mcx([x,y,z],flag[0])
    qc.x(x)
    qc.x(y)
    qc.x(z)
    qc.mcx([x,y,z],flag[3])
    qc.x(y)
    qc.x(z)
    return qc.to_gate()

def booth_multiplexer_simple():
    qc = QuantumCircuit()
    y,x = qc.qubits[0],qc.qubits[1]
    flag = qc.qubits[2:6]
    qc.cx(y, flag[1])
    qc.ccx(x,y,flag[1])
    qc.ccx(x,y,flag[2])
    qc.x(y)
    qc.ccx(x,y,flag[3])
    qc.x(y)
    return qc.to_gate()
"""

def karatsuba(a: int, b: int, n_a: int, n_b: int, optimal_splits: int): 
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

def gen_splits(max_bits: int, cutoff=11):
    dp = {}
    best_split = {}
    
    for n in range(1, cutoff + 1):
        dp[n] = 4 * (n ** 2) - 3 * n
        
    for n in range(cutoff + 1, max_bits + 1):
        min_cost = float('inf')
        optimal_k = n // 2 
        
        for k in range(1, n):
            size_x0 = k
            size_x1 = n - k
            size_mid = max(size_x0, size_x1) 
            cost_mults = dp[size_x1] + dp[size_x0] + dp[size_mid]
            cost_adders = 4 * (2 * n) + 4 * (2 * size_mid)
            total_cost = cost_mults + cost_adders
            
            if total_cost < min_cost:
                min_cost = total_cost
                optimal_k = k
        
        naive_cost = 4 * (n ** 2) - 3 * n
        if naive_cost < min_cost:
            dp[n] = naive_cost
            best_split[n] = None
        else:
            dp[n] = min_cost
            best_split[n] = optimal_k
            
    return best_split, dp

optimal_splits, min_gate_costs = gen_splits(32, cutoff=11)

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
        
def PTP(qc: QuantumCircuit, phi: float, x, y, z, anc,  n: int, cutoff: int = 4):
    if n <= cutoff:        
        for i in range(n):
            for j in range(n):
                for k in range(len(z)):
                    qc.mcp(
                        phi * (2**(i+j+k)), 
                        control_qubits=[x[i], y[j]], 
                        target_qubit=z[k]
                    )
                    
        return

    k = 3
    q = 3 * k - 2
    m = n // 3
    xc = [x[i*m : (i+1)*m] for i in range(3)]
    yc = [y[i*m : (i+1)*m] for i in range(3)]
    zc = [z[i*m : (i+1)*m] for i in range(3)]
    points = [0, inf, 1, -1, 2, -2, -0.5]
    phases = interpol_phases(phi, points, m) 
    for l in range(q):
            pt = points[l]
            phi_l = phases[l]
            
            if pt == 0:
                PTP(qc, phi_l, xc[0], yc[0], zc[0], anc, m, cutoff)
                
            elif pt == float('inf'):
                PTP(qc, phi_l, xc[2], yc[2], zc[2], anc, m, cutoff)
                
            elif pt == 1:
                qc.append(q_add(), [*xc[1], *xc[0], anc])
                qc.append(q_add(), [*xc[1], *xc[2], anc])
                qc.append(q_add(), [*yc[1], *yc[0], anc]) 
                qc.append(q_add(), [*yc[1], *yc[2], anc])
                qc.append(q_add(), [*zc[1], *zc[0], anc]) 
                qc.append(q_add(), [*zc[1], *zc[2], anc])
                sub_ptpc = QuantumCircuit(6 * m + 1) 
                local_xc = [sub_ptpc.qubits[0 : m], sub_ptpc.qubits[m : 2*m]]
                local_yc = [sub_ptpc.qubits[2*m : 3*m], sub_ptpc.qubits[3*m : 4*m]]
                local_zc = [sub_ptpc.qubits[4*m : 5*m], sub_ptpc.qubits[5*m : 6*m]]
                local_anc = sub_ptpc.qubits[6 * m]
                PTPC(sub_ptpc, m, phi_l, local_anc, local_xc, local_yc, local_zc, cutoff)
                qc.append(sub_ptpc.to_gate(label="PTPC"), [
                *xc[0], *xc[1],
                *yc[0], *yc[1],
                *zc[0], *zc[1], anc
            ])
                qc.append(q_sub(), [*zc[1], *zc[2], anc])
                qc.append(q_sub(), [*zc[1], *zc[0], anc]) 
                qc.append(q_sub(), [*yc[1], *yc[2], anc])
                qc.append(q_sub(), [*yc[1], *yc[0], anc]) 
                qc.append(q_sub(), [*xc[1], *xc[2], anc])
                qc.append(q_sub(), [*xc[1], *xc[0], anc])
            elif pt == -1:
                qc.append(q_sub(), [*xc[1], *xc[1], anc])
                qc.append(q_sub(), [*xc[1], *xc[1], anc])
                qc.append(q_add(), [*xc[1], *xc[0], anc])
                qc.append(q_add(), [*xc[1], *xc[2], anc])
                qc.append(q_sub(), [*yc[1], *yc[1], anc])
                qc.append(q_sub(), [*yc[1], *yc[1], anc])
                qc.append(q_add(), [*yc[1], *yc[0], anc])
                qc.append(q_add(), [*yc[1], *yc[2], anc])
                qc.append(q_sub(), [*zc[1], *zc[1], anc])
                qc.append(q_sub(), [*zc[1], *zc[1], anc])
                qc.append(q_add(), [*zc[1], *zc[0], anc])
                qc.append(q_add(), [*zc[1], *zc[2], anc])
                sub_ptpc = QuantumCircuit(6 * m + 1)
                local_xc = [sub_ptpc.qubits[0 : m], sub_ptpc.qubits[m : 2*m]]
                local_yc = [sub_ptpc.qubits[2*m : 3*m], sub_ptpc.qubits[3*m : 4*m]]
                local_zc = [sub_ptpc.qubits[4*m : 5*m], sub_ptpc.qubits[5*m : 6*m]]
                local_anc = sub_ptpc.qubits[6 * m]
                PTPC(sub_ptpc, m, phi_l, local_anc, local_xc, local_yc, local_zc, cutoff)
                qc.append(sub_ptpc.to_gate(label="PTPC_neg1"), [
                    *xc[0], *xc[1],
                    *yc[0], *yc[1],
                    *zc[0], *zc[1],
                    anc
                ])
                qc.append(q_sub(), [*zc[1], *zc[2], anc])
                qc.append(q_sub(), [*zc[1], *zc[0], anc])
                qc.append(q_add(), [*zc[1], *zc[1], anc])
                qc.append(q_add(), [*zc[1], *zc[1], anc])            
                qc.append(q_sub(), [*yc[1], *yc[2], anc])
                qc.append(q_sub(), [*yc[1], *yc[0], anc])
                qc.append(q_add(), [*yc[1], *yc[1], anc])
                qc.append(q_add(), [*yc[1], *yc[1], anc])
                qc.append(q_sub(), [*xc[1], *xc[2], anc])
                qc.append(q_sub(), [*xc[1], *xc[0], anc])
                qc.append(q_add(), [*xc[1], *xc[1], anc])
                qc.append(q_add(), [*xc[1], *xc[1], anc])
            elif pt == -2:
                qc.append(q_sub(), [*xc[1][1:], *xc[0][:m-1], anc])
                qc.append(q_sub(), [*xc[1][2:], *xc[2][:m-2], anc])
                
                qc.append(q_sub(), [*yc[1][1:], *yc[0][:m-1], anc])
                qc.append(q_sub(), [*yc[1][2:], *yc[2][:m-2], anc])
                
                qc.append(q_sub(), [*zc[1][1:], *zc[0][:m-1], anc])
                qc.append(q_sub(), [*zc[1][2:], *zc[2][:m-2], anc])
                sub_ptpc = QuantumCircuit(6 * m + 1)
                local_xc = [sub_ptpc.qubits[0 : m], sub_ptpc.qubits[m : 2*m]]
                local_yc = [sub_ptpc.qubits[2*m : 3*m], sub_ptpc.qubits[3*m : 4*m]]
                local_zc = [sub_ptpc.qubits[4*m : 5*m], sub_ptpc.qubits[5*m : 6*m]]
                local_anc = sub_ptpc.qubits[6 * m]
                
                PTPC(sub_ptpc, m, -phi_l, local_anc, local_xc, local_yc, local_zc, cutoff)
                
                qc.append(sub_ptpc.to_gate(label="PTPC_neg2"), [
                    *xc[0], *xc[1],
                    *yc[0], *yc[1],
                    *zc[0], *zc[1],
                    anc
                ])
                qc.append(q_add(), [*zc[1][2:], *zc[2][:m-2], anc])
                qc.append(q_add(), [*zc[1][1:], *zc[0][:m-1], anc])
                qc.append(q_add(), [*yc[1][2:], *yc[2][:m-2], anc])
                qc.append(q_add(), [*yc[1][1:], *yc[0][:m-1], anc])
                qc.append(q_add(), [*xc[1][2:], *xc[2][:m-2], anc])
                qc.append(q_add(), [*xc[1][1:], *xc[0][:m-1], anc])
                
            elif pt == 2:
                qc.append(q_add(), [*xc[1][1:], *xc[0][:m-1], anc])
                qc.append(q_add(), [*xc[1][2:], *xc[2][:m-2], anc])
                qc.append(q_add(), [*yc[1][1:], *yc[0][:m-1], anc])
                qc.append(q_add(), [*yc[1][2:], *yc[2][:m-2], anc])
                qc.append(q_add(), [*zc[1][1:], *zc[0][:m-1], anc])
                qc.append(q_add(), [*zc[1][2:], *zc[2][:m-2], anc])
                sub_ptpc = QuantumCircuit(6 * m + 1)
                local_xc = [sub_ptpc.qubits[0 : m], sub_ptpc.qubits[m : 2*m]]
                local_yc = [sub_ptpc.qubits[2*m : 3*m], sub_ptpc.qubits[3*m : 4*m]]
                local_zc = [sub_ptpc.qubits[4*m : 5*m], sub_ptpc.qubits[5*m : 6*m]]
                local_anc = sub_ptpc.qubits[6 * m]
                
                PTPC(sub_ptpc, m, phi_l, local_anc, local_xc, local_yc, local_zc, cutoff)
                qc.append(sub_ptpc.to_gate(), [
                    *xc[0], *xc[1],
                    *yc[0], *yc[1],
                    *zc[0], *zc[1],
                    anc
                ])
                qc.append(q_sub(), [*zc[1][2:], *zc[2][:m-2], anc])
                qc.append(q_sub(), [*zc[1][1:], *zc[0][:m-1], anc])
                qc.append(q_sub(), [*yc[1][2:], *yc[2][:m-2], anc])
                qc.append(q_sub(), [*yc[1][1:], *yc[0][:m-1], anc])
                qc.append(q_sub(), [*xc[1][2:], *xc[2][:m-2], anc])
                qc.append(q_sub(), [*xc[1][1:], *xc[0][:m-1], anc])
            elif pt == 0.5:
                qc.append(q_sub(), [*xc[1][2:], *xc[0][:m-2], anc])
                qc.append(q_sub(), [*xc[1], *xc[2], anc])
                qc.append(q_sub(), [*yc[1][2:], *yc[0][:m-2], anc])
                qc.append(q_sub(), [*yc[1], *yc[2], anc])
                qc.append(q_sub(), [*zc[1][2:], *zc[0][:m-2], anc])
                qc.append(q_sub(), [*zc[1], *zc[2], anc])
                sub_ptpc = QuantumCircuit(6 * m + 1)
                local_xc = [sub_ptpc.qubits[0 : m], sub_ptpc.qubits[m : 2*m]]
                local_yc = [sub_ptpc.qubits[2*m : 3*m], sub_ptpc.qubits[3*m : 4*m]]
                local_zc = [sub_ptpc.qubits[4*m : 5*m], sub_ptpc.qubits[5*m : 6*m]]
                local_anc = sub_ptpc.qubits[6 * m]
                PTPC(sub_ptpc, m, -phi_l, local_anc, local_xc, local_yc, local_zc, cutoff)
                qc.append(sub_ptpc.to_gate(label="PTPC_neg2"), [
                    *xc[0], *xc[1],
                    *yc[0], *yc[1],
                    *zc[0], *zc[1],
                    anc
                ])
                qc.append(q_add(), [*zc[1], *zc[2], anc])
                qc.append(q_add(), [*zc[1][2:], *zc[0][:m-2], anc])
                qc.append(q_add(), [*yc[1], *yc[2], anc])
                qc.append(q_add(), [*yc[1][2:], *yc[0][:m-2], anc])
                qc.append(q_add(), [*xc[1], *xc[2], anc])
                qc.append(q_add(), [*xc[1][2:], *xc[0][:m-2], anc])


    return        

def PTPC(qc, m: int, phi: float, anc, xc, yc, zc, cutoff: int = 4):
    
    rx0 = xc[0]
    rx1 = xc[1]
    ry0 = yc[0]
    ry1 = yc[1]
    rz0 = zc[0]
    rz1 = zc[1]

    dcx_in, dcy_in, dcz_in = rx0[m-1], ry0[m-1], rz0[m-1]
    dcx_out, dcy_out, dcz_out = rx1[m-1], ry1[m-1], rz1[m-1] 
    qc.append(correction_g(m, phi), [*rx0, *rx1, *ry0, *ry1, *rz0, *rz1])
    

    qc.append(cuccaro_1(m-1), [*rx0[:m-1], *rx1[:m-1], dcx_in])
    qc.append(cuccaro_1(m-1), [*ry0[:m-1], *ry1[:m-1], dcy_in])
    qc.append(cuccaro_1(m-1), [*rz0[:m-1], *rz1[:m-1], dcz_in])
    carry_x = rx0[m-2]
    carry_y = ry0[m-2]
    carry_z = rz0[m-2] 


    for i in range(m-1):
        for j in range(m-1):
            wt = phi * (2**(m-1 + i + j))
            qc.mcp(wt, control_qubits=[carry_x, ry1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[carry_y, rx1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[rx1[i], ry1[j]], target_qubit=carry_z) 
            qc.mcp(wt, control_qubits=[dcx_out, ry1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[dcy_out, rx1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[rx1[i], ry1[j]], target_qubit=dcz_out) 

    qc.append(cuccaro_2(m-1), [*rx0[:m-1], *rx1[:m-1], dcx_in])
    qc.append(cuccaro_2(m-1), [*ry0[:m-1], *ry1[:m-1], dcy_in])
    qc.append(cuccaro_2(m-1), [*rz0[:m-1], *rz1[:m-1], dcz_in])
    PTP(qc, phi, rx1[:m-1], ry1[:m-1], rz1[:m-1], anc, m - 1, cutoff)
    qc.append(cuccaro_inv(m-1), [*rz0[:m-1], *rz1[:m-1], dcz_in])
    qc.append(cuccaro_inv(m-1), [*ry0[:m-1], *ry1[:m-1], dcy_in])
    qc.append(cuccaro_inv(m-1), [*rx0[:m-1], *rx1[:m-1], dcx_in])
    return 
