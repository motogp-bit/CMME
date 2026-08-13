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