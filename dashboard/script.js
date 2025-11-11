async function fetchJSON(urls) {
  const list = Array.isArray(urls) ? urls : [urls];
  for (const url of list) {
    try {
      const res = await fetch(url, { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const txt = await res.text();
      try {
        return JSON.parse(txt);
      } catch (e) {
        throw new Error(`Not JSON from ${url}. Starts with: ${txt.slice(0,60)}`);
      }
    } catch (e) {
      console.warn(`Fetch failed: ${e.message}`);
    }
  }
  throw new Error(`All sources failed: ${list.join(' | ')}`);
}

async function loadDashboard() {
  // Primær: jsDelivr (stabil CORS). Fallback: raw.githubusercontent
  const META_URLS = [
    'https://cdn.jsdelivr.net/gh/supertedai/energyflow-cosmology@main/api/metadata.json',
    'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/metadata.json',
    'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/index.json'
  ];

  const TERMS_URLS = [
    'https://cdn.jsdelivr.net/gh/supertedai/energyflow-cosmology@main/api/v1/terms.json',
    'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/terms.json'
  ];

  try {
    const [meta, terms] = await Promise.all([
      fetchJSON(META_URLS),
      fetchJSON(TERMS_URLS)
    ]);

    // --- METADATA ---
    const m = document.getElementById('meta-content');
    m.innerHTML = `
      <p><b>Name:</b> ${meta.name ?? 'Energy-Flow Cosmology (EFC) – Dataset'}</p>
      ${meta.description ? `<p><b>Description:</b> ${meta.description}</p>` : ''}
      ${meta.version ? `<p><b>Version:</b> ${meta.version}</p>` : ''}
      <p><b>Last updated:</b> ${meta.dateModified ?? new Date().toISOString().split('T')[0]}</p>
      ${meta.license ? `<p><b>License:</b> <a href="${meta.license}" target="_blank">${meta.license}</a></p>` : ''}
      <p><b>Concept count:</b> ${Array.isArray(terms) ? terms.length : 0}</p>
    `;

    // --- CONCEPTS ---
    const tbody = document.querySelector('#concept-table tbody');
    tbody.innerHTML = (terms || [])
      .map(t => `<tr><td>${t.name}</td><td><a href="${t.url}" target="_blank">${t.url}</a></td></tr>`)
      .join('');
  } catch (err) {
    document.getElementById('meta-content').innerHTML =
      `<p style="color:#b91c1c"><b>Error:</b> ${err.message}</p>`;
  }
}

loadDashboard();
