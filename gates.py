from qiskit.circuit.library import DraperQFTAdder
from qiskit.circuit.library import VBERippleCarryAdder
from qiskit import QuantumCircuit

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

def IP_adder(n_a, n_b):
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

def OOP_adder(n_a, n_b):
    #a is always the smaller register
    
    qc = QuantumCircuit(n_a + 2*n_b + 2)
    
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a : n_a + n_b]
    s = qc.qubits[n_a + n_b : n_a + 2* n_b + 1]
    anc = qc.qubits[-1]
    
        
    for i in range(n_b):
        qc.cx(b[i], s[i])
        
    qc.append(IP_adder(n_a, n_b + 1), [*a, *s, anc])
    return qc.to_gate()

def gen_splits(max_bits, cutoff=11):
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

def add_constant(N, n):
    z = 0
    while N % 2 == 0:
        N = N // 2
        z+=1
    qc = QuantumCircuit(2*n - 3)
    x = qc.qubits[z:n]
    anc = qc.qubits[n:2*n - 3]
    #bit_array = N as an array of bits
    for i in range(bit_array):
        compute_MAJ(x, y, target, bit_array[i])
    #CONTINUE FROM HERE 
        


def shift_and_reduce(N, n):
    qc = QuantumCircuit(n + 1)
    
    x = qc.qubits[:n]
    anc = qc.qubits[n:2*n - 3]
    ctrl = qc.qubits[-1]
    
    shifted_x = [*anc, *x]
    
    qc.append(add_constant(N, n + 1).inverse(), [*x, *anc])
    
    c = shifted_x[n:n+1]
    
    qc.append(add_constant(N, n).control(1), [*c, *shifted_x[0:n]])
    
    qc.x(shifted_x[n])
    qc.cx(shifted_x[0], shifted_x[n])
    
    return qc.to_gate()

def QMA(n, N):
    qc = QuantumCircuit()
    x = qc.qubits[:n]
    y = qc.qubits[n:2*n]
    acc = qc.qubits[2*n:3*n]
    anc = qc.qubits[-1]
    for i in range(n):
        qc.append(DraperQFTAdder(n).control(1), [*y[i],*x,*acc])
        qc.append(shift_and_reduce(N, n), [*x, *anc])
    return qc.to_gate()