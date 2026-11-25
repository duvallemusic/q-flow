"""QUBO → Ising conversion using SparsePauliOp."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from qiskit.quantum_info import SparsePauliOp

from .qubo import QuboModel


@dataclass
class IsingHamiltonian:
    """Ising representation of a QUBO.

    Mapping: x_i = (I - Z_i) / 2
    Qiskit qubit ordering: Pauli string little-endian (rightmost char = qubit 0).
    """

    operator: SparsePauliOp
    offset: float
    n_qubits: int
    linear_z: dict[int, float]
    quadratic_zz: dict[tuple[int, int], float]
    metadata: dict[str, Any]

    def energy_from_bits(self, bits: list[int] | tuple[int, ...]) -> float:
        """Evaluate ⟨H⟩ for a computational-basis bitstring (x values)."""
        if len(bits) != self.n_qubits:
            raise ValueError(f"expected {self.n_qubits} bits")
        zs = [1 - 2 * int(b) for b in bits]
        energy = float(self.offset)
        for i, coeff in self.linear_z.items():
            energy += float(coeff) * zs[i]
        for (i, j), coeff in self.quadratic_zz.items():
            energy += float(coeff) * zs[i] * zs[j]
        return energy

    def energy_from_pauli_expectation(self, expectation: float) -> float:
        """SparsePauliOp already includes the constant I term when present."""
        return float(expectation)


def qubo_to_ising(model: QuboModel) -> IsingHamiltonian:
    """Convert QUBO to Ising via x_i = (1 - Z_i)/2.

    Expansion:
      c_i x_i = c_i/2 - (c_i/2) Z_i
      q_ij x_i x_j = q_ij/4 - (q_ij/4) Z_i - (q_ij/4) Z_j + (q_ij/4) Z_i Z_j
    """
    n = model.n_vars
    const = float(model.offset)
    linear_z: dict[int, float] = {i: 0.0 for i in range(n)}
    quadratic_zz: dict[tuple[int, int], float] = {}

    for i, c in model.linear.items():
        const += float(c) / 2.0
        linear_z[i] = linear_z.get(i, 0.0) - float(c) / 2.0

    for (i, j), q in model.quadratic.items():
        q = float(q)
        if i == j:
            # x_i^2 = x_i for binary variables
            const += q / 2.0
            linear_z[i] = linear_z.get(i, 0.0) - q / 2.0
            continue
        const += q / 4.0
        linear_z[i] = linear_z.get(i, 0.0) - q / 4.0
        linear_z[j] = linear_z.get(j, 0.0) - q / 4.0
        a, b = (i, j) if i < j else (j, i)
        quadratic_zz[(a, b)] = quadratic_zz.get((a, b), 0.0) + q / 4.0

    pauli_labels: list[str] = []
    coeffs: list[complex] = []

    # Identity (constant) term stored in the operator for ⟨H⟩ consistency.
    if not np.isclose(const, 0.0):
        pauli_labels.append("I" * n)
        coeffs.append(complex(const))

    for i, coeff in linear_z.items():
        if np.isclose(coeff, 0.0):
            continue
        label = ["I"] * n
        label[n - 1 - i] = "Z"  # qubit i is at position from the right
        pauli_labels.append("".join(label))
        coeffs.append(complex(coeff))

    for (i, j), coeff in quadratic_zz.items():
        if np.isclose(coeff, 0.0):
            continue
        label = ["I"] * n
        label[n - 1 - i] = "Z"
        label[n - 1 - j] = "Z"
        pauli_labels.append("".join(label))
        coeffs.append(complex(coeff))

    if not pauli_labels:
        operator = SparsePauliOp("I" * n, coeffs=[0.0])
    else:
        operator = SparsePauliOp(pauli_labels, coeffs=coeffs).simplify()

    return IsingHamiltonian(
        operator=operator,
        offset=const,
        n_qubits=n,
        linear_z={i: v for i, v in linear_z.items() if not np.isclose(v, 0.0)},
        quadratic_zz={k: v for k, v in quadratic_zz.items() if not np.isclose(v, 0.0)},
        metadata={
            "mapping": "x=(I-Z)/2",
            "endianness": "qiskit_little_endian_pauli_string",
            "qubo_scale": model.scale,
            "source": model.metadata.get("instance_id"),
        },
    )


def cost_operator_without_identity(ising: IsingHamiltonian) -> SparsePauliOp:
    """Drop constant I terms for QAOA ansatz construction (offset tracked separately)."""
    labels = ising.operator.paulis.to_labels()
    coeffs = ising.operator.coeffs
    kept_labels: list[str] = []
    kept_coeffs: list[complex] = []
    for label, coeff in zip(labels, coeffs, strict=True):
        if set(label) <= {"I"}:
            continue
        kept_labels.append(label)
        kept_coeffs.append(coeff)
    if not kept_labels:
        return SparsePauliOp("I" * ising.n_qubits, coeffs=[0.0])
    return SparsePauliOp(kept_labels, coeffs=kept_coeffs).simplify()
