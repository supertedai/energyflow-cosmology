# Energy-Flow Cosmology — Core Equations

This document collects the central equations of EFC in compact form.  
It is intended as a quick reference, not a full theoretical exposition.

---

## 1. Entropy Field and Endpoint Structure

- Entropy field:
  \[
  S(\mathbf{x})
  \]

- Endpoint values:
  \[
  S_0 \quad (\text{s}_0: \text{low entropy, high structural order}), \qquad
  S_1 \quad (\text{s}_1: \text{high entropy, structurally diffuse}).
  \]

- Midpoint and span:
  \[
  S_{\text{mid}} = \frac{1}{2}(S_0 + S_1),
  \qquad
  \Delta S = S_1 - S_0.
  \]

- Normalized entropy coordinate:
  \[
  x(S) = \frac{S - S_{\text{mid}}}{\Delta S / 2}.
  \]

---

## 2. Effective Light Speed \(c(S)\)

\[
c(S) = c_0 \left( 1 + a_{\text{edge}}\, x(S)^2 \right),
\]

with:

- \(c_0\): baseline light speed at the mid-entropy point  
- \(a_{\text{edge}} > 0\): controls enhancement toward the s₀ and s₁ endpoints.

Characteristics:

- Minimum at \(S = S_{\text{mid}}\).  
- Increases as \(S \to S_0\) (focusing regime).  
- Increases as \(S \to S_1\) (defocusing regime).

---

## 3. Energy Flow and Potential \(\Phi(E_f, S)\)

- Energy-flow field:
  \[
  E_f(\mathbf{x}) : \mathbb{R}^3 \to \mathbb{R},
  \qquad
  E_f \propto -\nabla S.
  \]

- Effective potential:
  \[
  \Phi(E_f,S) = A_\Phi E_f (1 + S),
  \]
  (baseline model, linear in \(S\)).

Extended (not used in baseline):

\[
\Phi(E_f,S) = A_\Phi E_f (1 + S^\beta).
\]

---

## 4. Expansion Rate \(H(E_f, S)\)

\[
H(E_f,S) = \sqrt{|E_f|}\, (1 + S).
\]

Interpretation:

- \(\sqrt{|E_f|}\): strength of energy flow  
- \((1 + S)\): thermodynamic modulation  
- Late-time acceleration can arise from changes in \((E_f, S)\), not from a separate dark-energy field.

---

## 5. Rotation Curves

\[
v(r) = \sqrt{\, r \, \frac{\partial \Phi}{\partial r} \, }.
\]

- The potential \(\Phi\) depends on \(E_f\) and \(S\).  
- The effective light speed \(c(S)\) affects how velocities are inferred from observations.  
- Flat rotation curves can emerge from stability bands around \(S_{\text{mid}}\).

---

## 6. Light Travel and Time Delays

- Light-travel time along a path \(\gamma\):
  \[
  t_{\text{obs}} = \int_{\gamma} \frac{dl}{c(S(l))}.
  \]

- Time-delay difference between two lensing images:
  \[
  \Delta t_{ij}
    = \int_{\gamma_i} \frac{dl}{c(S(l))}
    - \int_{\gamma_j} \frac{dl}{c(S(l))}.
  \]

---

## 7. Lensing and Observable Signatures

Lensing signals (magnification, shear, time delays) depend on:
\[
\text{mass distribution} + S(\mathbf{x}) + c(S).
\]

A fixed mass distribution can generate different lensing patterns if the entropy field differs.

---

## 8. Triad: \(S \rightarrow E_f \rightarrow \Phi \rightarrow c(S) \rightarrow \) Observables

The core structure of EFC can be written as:

\[
S(\mathbf{x})
  \;\Rightarrow\;
  E_f(\mathbf{x})
  \;\Rightarrow\;
  \Phi(E_f,S)
  \;\Rightarrow\;
  c(S)
  \;\Rightarrow\;
  \text{Observables}.
\]

Thus, dynamics, structure formation, and observational signatures all share the same thermodynamic origin.
