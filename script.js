async function loadDashboard() {
  const metaURL = "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/metadata.json";
  const termsURL = "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/terms.json";

  try {
    const [meta, terms] = await Promise.all([
      fetch(metaURL).then((r) => r.json()),
      fetch(termsURL).then((r) => r.json())
    ]);

    // --- METADATA ---
    const metaDiv = document.getElementById("meta-content");
    metaDiv.innerHTML = `
      <p><b>Name:</b> ${meta.name}</p>
      <p><b>Description:</b> ${meta.description}</p>
      <p><b>Last Updated:</b> ${meta.dateModified}</p>
      <p><b>License:</b> <a href="${meta.license}" target="_blank">${meta.license}</a></p>
      <p><b>Accessible:</b> ${meta.isAccessibleForFree ? "✅ Free" : "⚠️ Restricted"}</p>
    `;

    // --- CONCEPTS ---
    const tableBody = document.querySelector("#concept-table tbody");
    tableBody.innerHTML = "";
    terms.forEach((t) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${t.name}</td>
        <td><a href="${t.url}" target="_blank">${t.url}</a></td>
      `;
      tableBody.appendChild(row);
    });
  } catch (err) {
    document.getElementById("meta-content").innerHTML = `<p style="color:red;">Error loading data: ${err}</p>`;
  }
}

loadDashboard();
