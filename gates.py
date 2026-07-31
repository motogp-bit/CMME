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

def AS_adder(n_a, n_b):

    qc = QuantumCircuit()
    a = qc.qubits[:n_a]
    b = qc.qubits[n_a:n_a + n_b]
    c = qc.qubits[-1]

    for i in range(n):
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

def OOP_adder(n):
    
    qc = QuantumCircuit(a, b, s)
    a = qc.qubits[:n]
    b = qc.qubits[n:2*n]
    s = qc.qubits[2*n:3*n + 1]
    vbe_gate = VBERippleCarryAdder(num_state_qubits=n).to_gate()
    qc.append(vbe_gate, [*a, *b, *s[:n], s[n]])
    
    return qc.to_gate()