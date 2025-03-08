import numpy as np
import pandas as pd
import re
import subprocess

class Energy:
    def __init__(self, int_=0, pot=0, vdw=0, ele=0, pol=0):
        self.int = int_
        self.pot = pot
        self.vdw = vdw
        self.ele = ele
        self.pol = pol
    
    def __sub__(self, other):
        int_diff = self.int - other.int
        pot_diff = self.pot - other.pot
        vdw_diff = self.vdw - other.vdw
        ele_diff = self.ele - other.ele
        pol_diff = self.pol - other.pol
        return Energy(int_diff,pot_diff,vdw_diff,ele_diff,pol_diff)
    
    def __isub__(self, other):
        self.int -= other.int
        self.pot -= other.pot
        self.vdw -= other.vdw
        self.ele -= other.ele
        self.pol -= other.pol
        return self
    
    def __add__(self, other):
        int_diff = self.int + other.int
        pot_diff = self.pot + other.pot
        vdw_diff = self.vdw + other.vdw
        ele_diff = self.ele + other.ele
        pol_diff = self.pol + other.pol
        return Energy(int_diff,pot_diff,vdw_diff,ele_diff,pol_diff)
    
    def __iadd__(self, other):
        self.int += other.int
        self.pot += other.pot
        self.vdw += other.vdw
        self.ele += other.ele
        self.pol += other.pol
        return self

def analyze(exe, key, xyz):
    # Command to run
    command = f"{exe} -k {key} {xyz} e"
    
    # Run the command
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Get the output and error
    output, error = process.communicate()
    
    # Split the output into a list of strings
    lines = output.decode().splitlines()

    energy_list = []
    
    # Read lines
    energy = Energy()
    for line in lines:
        if " Intermolecular Energy : " in line:
            energy.int = float(line.split()[-2])
        elif " Total Potential Energy : " in line:
            energy.pot = float(line.split()[-2])
        elif " Van der Waals " in line:
            energy.vdw = float(line.split()[-2])
        elif " Atomic Multipoles " in line:
            energy.ele = float(line.split()[-2])
        elif " Polarization " in line:
            energy.pol = float(line.split()[-2])
        elif " Analysis for Archive Structure :" in line:
            energy_list.append(energy)
            energy = Energy()
    energy_list.append(energy)

    return np.array(energy_list)

def compute(exe, key, xyz, xyzA, xyzB):
    # Compute energy
    energy = analyze(exe, key, xyz)
    energyA = analyze(exe, key, xyzA)
    energyB = analyze(exe, key, xyzB)
    
    return energy - energyA - energyB

def getQMMethods(QM):
    QM_methods = {}

    if "ALMO" in QM:
        ALMO = pd.read_csv('ALMO/ALMO.dat', sep='\s+')
        ALMO = ALMO.rename(columns={'ALMO/TZVPPD': 'Total'})
        ALMO['Induction'] = ALMO['Polarization'] + ALMO['ChargeTransfer']
        ALMO['VdW'] = ALMO['Exchange'] + ALMO['Dispersion']
        QM_methods["ALMO"] = ALMO

    if "SAPT" in QM:
        SAPT = pd.read_csv('SAPT/SAPT.dat', sep='\s+')
        SAPT = SAPT.rename(columns={'SAPT2+/aVTZ': 'Total'})
        SAPT['VdW'] = SAPT['Exchange'] + SAPT['Dispersion']
        QM_methods["SAPT"] = SAPT

    if "MP2" in QM:
        MP2 = pd.read_csv('MP2/MP2.dat', sep='\s+')
        MP2 = MP2.rename(columns={'MP2/aVTZ': 'Total'})
        QM_methods["MP2"] = MP2
    
    return QM_methods

def extract_multipole_moments(text):
    # Extract Dipole components
    dipole_pattern = r"Dipole X,Y,Z-Components\s*:\s*([\d\-.]+)\s+([\d\-.]+)\s+([\d\-.]+)"
    dipole_match = re.search(dipole_pattern, text)

    if dipole_match:
        dipole_moment = [float(dipole_match.group(i)) for i in range(1, 4)]
    else:
        dipole_moment = None

    # Extract Quadrupole tensor components
    quadrupole_pattern = r"Quadrupole Moment Tensor\s*:\s*([\d\-.]+)\s+([\d\-.]+)\s+([\d\-.]+)\s*\n\s*\(Buckinghams\)\s*([\d\-.]+)\s+([\d\-.]+)\s+([\d\-.]+)\s*\n\s*([\d\-.]+)\s+([\d\-.]+)\s+([\d\-.]+)"
    quadrupole_match = re.search(quadrupole_pattern, text)

    if quadrupole_match:
        quadrupole_moment = [[float(quadrupole_match.group(i)) for i in range(1, 4)],
                             [float(quadrupole_match.group(i)) for i in range(4, 7)],
                             [float(quadrupole_match.group(i)) for i in range(7, 10)]]
    else:
        quadrupole_moment = None

    return np.array(dipole_moment), np.array(quadrupole_moment)

def extract_polarizability(text):
    # Corrected regex patterns
    tensor_pattern = re.compile(
        r"Molecular Polarizability Tensor :\s*\n"
        r"\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\n"
        r"\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\n"
        r"\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)"
    )
    eigenvalues_pattern = re.compile(r"Polarizability Tensor Eigenvalues :\s+([-\d.\s]+)")
    interactive_pattern = re.compile(r"Interactive Molecular Polarizability :\s+([-\d.]+)")

    # Finding matches
    tensor_match = tensor_pattern.search(text)
    eigenvalues_match = eigenvalues_pattern.search(text)
    interactive_match = interactive_pattern.search(text)

    # Extract molecular polarizability tensor
    molecular_tensor = None
    if tensor_match:
        tensor_values = [float(x) for x in tensor_match.groups()]
        molecular_tensor = np.array(tensor_values).reshape(3, 3)  # Ensure correct matrix shape

    # Extract eigenvalues
    eigenvalues = None
    if eigenvalues_match:
        eigenvalues = np.array(list(map(float, eigenvalues_match.group(1).split())))

    # Extract interactive molecular polarizability
    interactive_polarizability = None
    if interactive_match:
        interactive_polarizability = float(interactive_match.group(1).strip())

    return molecular_tensor, eigenvalues, interactive_polarizability

def calculate_rmsd(array1, array2):
    if array1.shape != array2.shape:
        raise ValueError("Arrays must have the same shape.")
    
    rmsd = np.sqrt(np.mean((array1 - array2) ** 2))
    return rmsd
