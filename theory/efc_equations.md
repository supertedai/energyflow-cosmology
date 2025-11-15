# Energy-Flow Cosmology — Core Equations

Denne fila samler de sentrale ligningene i EFC i kompakt form.  
Den er ment som et raskt oppslagsverk, ikke som full teori.

---

## 1. Entropifelt og endepunkter

- Entropifelt:
  \[
  S(\mathbf{x})
  \]

- Endepunkter:
  \[
  S_0 \quad (\text{s}_0: \text{lav entropi, høy struktur}), \qquad
  S_1 \quad (\text{s}_1: \text{høy entropi, strukturell løsere}).
  \]

- Midtpunkt og spenn:
  \[
  S_{\text{mid}} = \frac{1}{2}(S_0 + S_1),
  \qquad
  \Delta S = S_1 - S_0.
  \]

- Normalisert koordinat:
  \[
  x(S) = \frac{S - S_{\text{mid}}}{\Delta S / 2}.
  \]

---

## 2. Effektiv lysfart c(S)

\[
c(S) = c_0 \left( 1 + a_{\text{edge}}\, x(S)^2 \right),
\]

med:

- \(c_0\): baseline lysfart ved midt-entropi  
- \(a_{\text{edge}} > 0\): styrer økning mot s₀ og s₁.

Egenskaper:

- Minimum ved \(S = S_{\text{mid}}\).  
- Øker når \(S \to S_0\) (fokuserende regime).  
- Øker når \(S \to S_1\) (defokuserende regime).

---

## 3. Energiflyt og potensial Φ(Ef, S)

- Energiflytfelt:
  \[
  E_f(\mathbf{x}) : \mathbb{R}^3 \to \mathbb{R},
  \qquad
  E_f \propto -\nabla S.
  \]

- Effektivt potensial:
  \[
  \Phi(E_f,S) = A_\Phi E_f (1 + S),
  \]
  (baseline-modell, lineær i S).

Utvidet form (ikke implementert i baseline):

\[
\Phi(E_f,S) = A_\Phi E_f (1 + S^\beta).
\]

---

## 4. Ekspansjonsrate H(Ef, S)

\[
H(E_f,S) = \sqrt{|E_f|}\, (1 + S).
\]

Tolkning:

- \(\sqrt{|E_f|}\): styrke i energiflyt.  
- \((1+S)\): termodynamisk modulasjon.  
- Senere akselerasjon kan komme fra endring i \((E_f, S)\), ikke fra egen mørk-energi.

---

## 5. Rotasjonskurver

\[
v(r) = \sqrt{\, r \, \frac{\partial \Phi}{\partial r} \, }.
\]

- Φ avhenger av \(E_f\) og S.  
- c(S) påvirker hvordan v(r) måles observasjonelt.  
- Flate rotasjonskurver kan oppstå fra stabilitetsbånd rundt \(S_{\text{mid}}\).

---

## 6. Lysgang og tidsforsinkelser

- Lysgangstid langs bane \(\gamma\):
  \[
  t_{\text{obs}} = \int_{\gamma} \frac{dl}{c(S(l))}.
  \]

- Tidsforskjell mellom to bilder i lensing:
  \[
  \Delta t_{ij}
    = \int_{\gamma_i} \frac{dl}{c(S(l))}
    - \int_{\gamma_j} \frac{dl}{c(S(l))}.
  \]

---

## 7. Lensing og signaturer

- Lensing-signaler (magnifikasjon, shear, tidsforsinkelser) avhenger av:
  \[
  \text{massestruktur} + S(\mathbf{x}) + c(S).
  \]

Samme massefordeling kan gi ulike lensing-mønstre hvis S-feltet er forskjellig.

---

## 8. Triade: S → Ef → Φ → c(S) → Observables

Kjernestrukturen i EFC kan skrives som:

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

Alt (dynamikk, struktur og observasjoner) har dermed samme termodynamiske kilde.
