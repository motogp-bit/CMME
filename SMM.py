import numpy as np
from math import inf
from qiskit import QuantumCircuit
from qiskit.circuit import Gate
from qiskit.circuit.library import QFT

def QQM(n: int) -> QuantumCircuit:
    qc = QuantumCircuit(4 * n)
    
    # Slice the circuit's qubits directly into lists of Qubit objects
    x = qc.qubits[0:n]
    y = qc.qubits[n:2 * n]
    w = qc.qubits[2 * n:4 * n]
    
    # Pass the unpacked list of qubits directly to the gate
    qc.append(QFT(num_qubits=2*n, do_swaps=True).to_gate(), [*w])
    PTP(qc, 2 * np.pi / (2 ** (2 * n)), x, y, w, n)
    qc.append(QFT(num_qubits=2*n, do_swaps=True).inverse().to_gate(), [*w])
    
    return qc

def PTP(qc: QuantumCircuit, phi: float, rx: list, ry: list, rz: list, n: int, cutoff: int = 4):
    if n <= cutoff:
        for i in range(n):
            for j in range(n):
                for k in range(len(rz)):
                    qc.mcphase(
                        phi * (2**(i+j+k)), 
                        control_qubits=[rx[i], ry[j]], 
                        target_qubit=rz[k]
                    )
        return

    m = n // 3
    
    xc = [rx[i*m : (i+1)*m] for i in range(3)]
    yc = [ry[i*m : (i+1)*m] for i in range(3)]
    zc = [rz[i*m : (i+1)*m] for i in range(3)]
    
    points = [0, inf, 1, -1, 2, -2, -0.5]
    phases = [phi * (i + 1) for i in range(7)] 
    
    add_g = qiskit_in_place_add(m)
    sub_g = qiskit_in_place_sub(m)

    for pt, phi_l in zip(points, phases):
        if pt == 0:
            PTP(qc, phi_l, xc[0], yc[0], zc[0], m, cutoff)
        elif pt == inf:
            PTP(qc, phi_l, xc[2], yc[2], zc[2], m, cutoff)
        elif pt == 1:
            for reg in (xc, yc, zc): 
                # Using list unpacking to feed dynamically sized target and source
                qc.append(add_g(m), [*reg[0], *reg[1]])
                qc.append(add_g(m), [*reg[2], *reg[1]])
            
            PTPC(qc, phi_l, xc[1], yc[1], zc[1], m, cutoff)
            
            for reg in (zc, yc, xc): 
                qc.append(sub_g(m), [*reg[2], *reg[1]])
                qc.append(sub_g(m), [*reg[0], *reg[1]])
        elif pt == -1:
            qc.append(sub_g(m), [*xc[0], *xc[1]])
            qc.append(add_g(m), [*xc[2], *xc[1]])
            PTPC(qc, phi_l, xc[1], yc[1], zc[1], m, cutoff)

def PTPC(qc: QuantumCircuit, phi: float, rx: list, ry: list, rz: list, m: int, cutoff: int):
    dcx, dcy, dcz = rx[m-1], ry[m-1], rz[m-1]
    
    qc.append(correction_g(m, phi), [*rx, *ry, *rz])
    
    qc.append(cuccaro_1(m), [*rx[:m-1], dcx])
    qc.append(cuccaro_1(m) [*ry[:m-1], dcy])
    qc.append(cuccaro_1(m), [*rz[:m-1], dcz])
    
    for i in range(m-1):
        for j in range(m-1):
            wt = phi * (2**(m-1 + i + j))
            qc.mcphase(wt, control_qubits=[dcx, rx[i]], target_qubit=rz[j])
            qc.mcphase(wt, control_qubits=[dcy, ry[i]], target_qubit=rz[j])
            
    for r, d in zip((rx, ry, rz), (dcx, dcy, dcz)): 
        qc.append(cuccaro_2(m), [*r[:m-1], d])
        
    PTP(qc, phi, rx[:m-1], ry[:m-1], rz[:m-1], m-1, cutoff)
    
    for r, d in zip((rz, ry, rx), (dcz, dcy, dcx)): 
        qc.append(cuccaro_inv(m), [*r[:m-1], d])




def add_g(m: int) -> Gate:
    return Gate('add', num_qubits=2*m, params=[])

def sub_g(m: int) -> Gate:
    return Gate('sub', num_qubits=2*m, params=[])

def cuccaro_1(m: int) -> Gate:
    return Gate('cuccaro_first_half', num_qubits=m, params=[])

def cuccaro_2(m: int) -> Gate:
    return Gate('cuccaro_second_half', num_qubits=m, params=[])

def cuccaro_inv(m: int) -> Gate:
    return Gate('cuccaro_inverse', num_qubits=m, params=[])

def correction_g(m: int, phi: float) -> Gate:
    return Gate('dirty_carry_correction', num_qubits=3*m, params=[phi])