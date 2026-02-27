import fs from "fs";
import path from "path";
import Link from "next/link";

interface Product {
  t: number;
  name: string;
  context: string;
  tags: string[];
}

interface MediaCue {
  t: number;
  cue: string;
  type?: string;
}

interface ParsedEpisode {
  episode_id: string;
  products: Product[];
  media: MediaCue[];
}

function loadEpisode(id: string): ParsedEpisode | null {
  const filePath = path.join(
    process.cwd(),
    "public",
    "episodes",
    `${id}-parsed.json`
  );
  if (!fs.existsSync(filePath)) return null;
  const data = JSON.parse(fs.readFileSync(filePath, "utf8"));
  return data as ParsedEpisode;
}

function formatTime(seconds: number): string {
  const s = Math.floor(seconds);
  const m = Math.floor(s / 60);
  const ss = s % 60;
  return `${m.toString().padStart(2, "0")}:${ss.toString().padStart(2, "0")}`;
}

function buildAffiliateNotes(ep: ParsedEpisode): string {
  const lines: string[] = [];
  lines.push(`Episode ${ep.episode_id}`);
  lines.push("Products:");
  for (const p of ep.products) {
    const t = formatTime(p.t);
    const tags = p.tags.length ? ` [${p.tags.join(", ")}]` : "";
    lines.push(`- (${t}) ${p.name}${tags} — ${p.context}`);
  }
  if (ep.media.length) {
    lines.push("\nMedia cues:");
    for (const m of ep.media) {
      const t = formatTime(m.t);
      const type = m.type ? ` [${m.type}]` : "";
      lines.push(`- (${t})${type} ${m.cue}`);
    }
  }
  lines.push("\nSome links may be affiliate links.");
  return lines.join("\n");
}

export default function EpisodePage({ params }: { params: { id: string } }) {
  const episode = loadEpisode(params.id);

  if (!episode) {
    return (
      <main className="min-h-screen bg-slate-950 text-slate-100">
        <div className="mx-auto max-w-5xl px-4 py-8">
          <p className="mb-4 text-sm text-slate-400">Episode not found.</p>
          <Link href="/" className="text-sm text-sky-400 hover:underline">
            ← Back to episodes
          </Link>
        </div>
      </main>
    );
  }

  const affiliateNotes = buildAffiliateNotes(episode);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-5xl px-4 py-8">
        <header className="mb-6 border-b border-slate-800 pb-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold">Episode {episode.episode_id}</h1>
              <p className="mt-1 text-xs text-slate-400">
                Non-obvious product mentions and media cues.
              </p>
            </div>
            <button
              onClick={() => navigator.clipboard.writeText(affiliateNotes)}
              className="rounded bg-sky-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-500"
            >
              Copy affiliate notes
            </button>
          </div>
        </header>

        <section className="mb-8">
          <h2 className="text-lg font-semibold">Products</h2>
          {episode.products.length === 0 ? (
            <p className="mt-2 text-sm text-slate-400">No products detected.</p>
          ) : (
            <div className="mt-2 overflow-x-auto rounded-md border border-slate-800 bg-slate-900/40">
              <table className="min-w-full text-left text-xs">
                <thead className="bg-slate-900/80 text-slate-400">
                  <tr>
                    <th className="px-3 py-2">Time</th>
                    <th className="px-3 py-2">Product</th>
                    <th className="px-3 py-2">Context</th>
                    <th className="px-3 py-2">Tags</th>
                  </tr>
                </thead>
                <tbody>
                  {episode.products.map((p, idx) => (
                    <tr
                      key={`${p.name}-${p.t}-${idx}`}
                      className="border-t border-slate-800 hover:bg-slate-900/80"
                    >
                      <td className="px-3 py-2 font-mono text-[11px] text-slate-300">
                        {formatTime(p.t)}
                      </td>
                      <td className="px-3 py-2 text-xs font-medium text-slate-100">
                        {p.name}
                      </td>
                      <td className="px-3 py-2 text-xs text-slate-300">
                        {p.context}
                      </td>
                      <td className="px-3 py-2 text-[11px] text-slate-300">
                        {p.tags.map((tag) => (
                          <span
                            key={tag}
                            className="mr-1 inline-flex rounded-full bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-300"
                          >
                            {tag}
                          </span>
                        ))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="mb-8">
          <h2 className="text-lg font-semibold">Media cues</h2>
          {episode.media.length === 0 ? (
            <p className="mt-2 text-sm text-slate-400">No media cues detected.</p>
          ) : (
            <div className="mt-2 overflow-x-auto rounded-md border border-slate-800 bg-slate-900/40">
              <table className="min-w-full text-left text-xs">
                <thead className="bg-slate-900/80 text-slate-400">
                  <tr>
                    <th className="px-3 py-2">Time</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Cue</th>
                  </tr>
                </thead>
                <tbody>
                  {episode.media.map((m, idx) => (
                    <tr
                      key={`${m.cue}-${m.t}-${idx}`}
                      className="border-t border-slate-800 hover:bg-slate-900/80"
                    >
                      <td className="px-3 py-2 font-mono text-[11px] text-slate-300">
                        {formatTime(m.t)}
                      </td>
                      <td className="px-3 py-2 text-xs text-slate-200">
                        {m.type || ""}
                      </td>
                      <td className="px-3 py-2 text-xs text-slate-300">
                        {m.cue}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <footer className="mt-10 border-t border-slate-800 pt-4 text-xs text-slate-500">
          <p>Some links may be affiliate links.</p>
          <Link href="/" className="mt-2 inline-block text-sky-400 hover:underline">
            ← Back to episodes
          </Link>
        </footer>
      </div>
    </main>
  );
}
