import numpy as np
import matplotlib.pyplot as plt
from src.efc_light import c_of_S

S = np.linspace(-0.2, 1.2, 400)
c = c_of_S(S)

plt.plot(S, c)
plt.xlabel("Entropy S")
plt.ylabel("c(S) [m/s]")
plt.title("EFC: Effective c(S) across entropy field")
plt.grid(True)

# Save instead of show
plt.savefig("output/c_of_S_plot.png", dpi=200)
print("Saved plot to output/c_of_S_plot.png")

