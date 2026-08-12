from qiskit.circuit.library import DraperQFTAdder
from qiskit.circuit.library import SXdgGate
from qiskit.circuit.library import QFT
from qiskit import QuantumCircuit
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

def IP_adder(n_a: int, n_b: int):
    #a is always the smaller register
    qc = QuantumCircuit(n_a + n_b + 1)
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a:n_a + n_b]
    c = qc.qubits[-1]

    for i in range(n_a):
        qc.cx(c, a[i])
        qc.cx(c, b[i])
        qc.ccx(a[i], b[i], c)

    extension_size = n_b - n_a
    if extension_size > 0:
        for i in reversed(range(1, extension_size)):
            target = b[n_a + i]
            controls = [c] + b[n_a : n_a + i]
            qc.mcx(controls, target)
        qc.cx(c, b[n_a])
        
    for i in reversed(range(n_a)):
        qc.ccx(a[i], b[i], c)
        qc.cx(c, a[i])
        qc.cx(a[i], b[i])
        
    return qc.to_gate()

def OOP_adder(n_a : int, n_b: int):
    #b is the larger register
    qc = QuantumCircuit(n_a + 2 * n_b + 1)
    
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a : n_a + n_b]
    s = qc.qubits[n_a + n_b : n_a + 2 * n_b + 1]
    
    csxdg = SXdgGate().control(1)
    
    for i in range(n_b):
        b_qubit = b[i]
        c_in = s[i]
        c_out = s[i+1]
        
        if i < n_a:
            a_qubit = a[i]
            
            qc.csx(a_qubit, c_out)
            qc.csx(b_qubit, c_out)
            qc.cx(a_qubit, b_qubit)
            qc.csx(c_in, c_out)
            qc.cx(b_qubit, c_in)
            qc.append(csxdg, [c_in, c_out])
            
            qc.cx(a_qubit, b_qubit)
        else:
            qc.csx(b_qubit, c_out)
            qc.csx(c_in, c_out)
            qc.cx(b_qubit, c_in)
            qc.append(csxdg, [c_in, c_out])
            
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
def MAJ():
    qc = QuantumCircuit(3)
    a = qc.qubits[0]
    b = qc.qubits[1]
    c = qc.qubits[2]
    qc.cx(a,b)
    qc.cx(a,c)
    qc.ccx(c,b,a)
    return qc.to_gate()

def UMA():
    qc = QuantumCircuit(3)
    a = qc.qubits[0]
    b = qc.qubits[1]
    c = qc.qubits[2]   
    qc.ccx(c,b,a)
    qc.cx(a,c)
    qc.cx(c,b)
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
            

def cuccaro_1(m: int):
    qc = QuantumCircuit(2*m + 1)
    x = qc.qubits[:m]
    y = qc.qubits[m:2*m]
    c = qc.qubits[-1]
    qc.append(MAJ(),[x[0], y[0], c])
    for i in range(m - 1):
        qc.append(MAJ(),[x[i+1],y[i+1],x[i]])
    return qc.to_gate()

def cuccaro_2(m: int):
    qc = QuantumCircuit(2*m + 1)
    x = qc.qubits[:m]
    y = qc.qubits[m:2*m]
    c = qc.qubits[-1]
    for i in reversed(range(m - 1)):
        qc.append(UMA(), [x[i + 1], y[i + 1], x[i]])

    qc.append(UMA(), [x[0], y[0], c])
    
    
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

