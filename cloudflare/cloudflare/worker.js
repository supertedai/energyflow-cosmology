export default {
  async fetch(request) {
    const url = new URL(request.url);
    const query = url.searchParams.get("q") || "";

    if (!query) {
      return new Response(JSON.stringify({
        error: "missing query parameter ?q="
      }), {
        headers: { "Content-Type": "application/json" }
      });
    }

    // 1. Hent semantic index
    const indexUrl = "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/semantic-search-index.json";
    const indexRes = await fetch(indexUrl);
    const index = await indexRes.json();

    const q = query.toLowerCase();

    // 2. Rank nodes etter match
    function score(node) {
      return JSON.stringify(node).toLowerCase().split(q).length - 1;
    }

    const topNodes = index
      .map(n => ({ n, s: score(n) }))
      .filter(x => x.s > 0)
      .sort((a, b) => b.s - a.s)
      .slice(0, 5);

    // 3. Hent snippets fra Markdown-filer
    async function fetchSnippet(path) {
      if (!path.endsWith(".md")) return null;

      const raw = `https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/${path}`;
      try {
        const res = await fetch(raw);
        if (!res.ok) return null;

        const text = await res.text();
        return text.split("\n").slice(0, 12).join("\n");
      } catch {
        return null;
      }
    }

    const results = [];

    for (const { n } of topNodes) {
      const snippet = await fetchSnippet(n.path);

      results.push({
        title: n.title || null,
        path: n.path || null,
        summary: n.summary || null,
        tags: n.tags || [],
        domain: n.domain || null,
        snippet: snippet
      });
    }

    return new Response(JSON.stringify({
      query: query,
      results: results
    }), {
      headers: { "Content-Type": "application/json" }
    });
  }
};
