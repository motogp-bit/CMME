from qiskit import QuantumCircuit
from .SMM import QQM
from .gates import gen_splits,

def CMMC(n, constant):
    qc = QuantumCircuit(n+1)
    ctrl = qc.qubits[0]
    reg = qc.qubits[1:]
    bitmask = 1 ^ constant
    for j in range(n):
        if (bitmask >> j) & 1:
            qc.cx(ctrl, reg[j])
    return qc.to_gate()

def build_tree(qc, regs, n,  N, index, optimal_splits):
    layers = [regs]
    current_level = regs
    markers = []
    while len(current_level) > 1:
        next_level = []
        tier_size = len(current_level)
        midpoint = tier_size // 2
        
        for i in range(midpoint):
            ln = current_level[i]
            rn = current_level[tier_size - 1 - i]
            out_size = len(ln) + len(rn)
            newreg = qc.qubits[index: index + out_size]
            
            if out_size >= n:
                pass
                qc.append(QQM(n), [*ln, *rn, *newreg])
            else:
                pass
                #multiplication
                
            next_level.append(newreg)
            index = index + out_size
        if tier_size % 2 != 0:
            next_level.append(current_level[midpoint])
            
        layers.append(next_level)
        current_level = next_level
        markers.append(tier_size)
    return layers, markers 

def invert_tree(qc, layers, markers, n, N):
    depth = len(markers)
    
    for d in range(depth - 1, -1, -1):
        upper_tier = layers[d + 1]
        lower_tier = layers[d]
        
        tier_size = markers[d]
        midpoint = tier_size // 2
        
        for i in range(midpoint - 1, -1, -1):
            ln = lower_tier[i]
            rn = lower_tier[tier_size - 1 - i]
            
            newreg = upper_tier[i]
            out_size = len(ln) + len(rn)
            
            if out_size >= n:
                qc.append(QQM(n).inverse(), [*ln, *rn, *newreg])
            else:
            #something    
            
def main(sizes,total_size, n, N):
    optimal_splits, min_gate_costs = gen_splits(max_bits=32)
    qc = QuantumCircuit(total_size * n)
    constants = []
    mark = 0
    regs = []
    for size in sizes:
        regs.append(qc.qubits[mark: mark + size])
        mark = mark + size
    c = qc.qubits[mark: mark + 1]
    for i in range(len(regs)):
        qc.append(CMMC(sizes[i],constants[i]), [*c, regs[i]])
    tree, markers = build_tree(qc, regs, n, N, index, optimal_splits)
    #accumulator
    invert_tree(qc,tree,markers,n,N)
    
