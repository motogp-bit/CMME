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