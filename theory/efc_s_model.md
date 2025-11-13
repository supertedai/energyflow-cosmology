# EFC-S: Entropy Field & Gradient

EFC begins with a thermodynamic field S(x), representing the local
entropy state of matter–information configuration.

## 1. Entropy Field
The entropy field is modeled as:

\[
S(\mathbf{x}) \in [0,1]
\]

where:
- \( S = 0 \) → highly ordered regions  
- \( S = 1 \) → high entropy regions

## 2. Entropy Gradient
The gradient drives anisotropic flow:

\[
\nabla S(\mathbf{x}) = 
\left( 
\frac{\partial S}{\partial x},
\frac{\partial S}{\partial y},
\frac{\partial S}{\partial z}
\right)
\]

Magnitude:

\[
|\nabla S| = \sqrt{
\left( \frac{\partial S}{\partial x} \right)^2 +
\left( \frac{\partial S}{\partial y} \right)^2 +
\left( \frac{\partial S}{\partial z} \right)^2
}
\]

**Code reference:**  
`src/efc_entropy.py`
