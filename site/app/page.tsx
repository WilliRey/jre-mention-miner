"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

interface EpisodeSummary {
  episode_id: string;
  products: { name: string }[];
}

export default function HomePage() {
  const [episodes, setEpisodes] = useState<EpisodeSummary[]>([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("/api/episodes");
        const data = await res.json();
        setEpisodes(data);
      } catch (err) {
        console.error(err);
      }
    }
    load();
  }, []);

  const filtered = useMemo(() => {
    if (!query.trim()) return episodes;
    const q = query.toLowerCase();
    return episodes.filter((ep) =>
      ep.products.some((p) => p.name.toLowerCase().includes(q))
    );
  }, [episodes, query]);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-5xl px-4 py-8">
        <header className="mb-6 border-b border-slate-800 pb-4">
          <h1 className="text-3xl font-bold">JRE Mention Miner</h1>
          <p className="mt-2 text-sm text-slate-400">
            Extracting non-obvious product mentions and media cues from Joe Rogan
            Experience episodes.
          </p>
        </header>

        <section className="mb-6 flex items-center justify-between gap-4">
          <div className="flex-1">
            <label className="block text-xs font-medium text-slate-400">
              Search products
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter by product name…"
              className="mt-1 w-full rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
        </section>

        {filtered.length === 0 ? (
          <p className="text-sm text-slate-400">No parsed episodes found.</p>
        ) : (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Episodes</h2>
            <ul className="divide-y divide-slate-800 rounded-md border border-slate-800 bg-slate-900/40">
              {filtered.map((ep) => (
                <li key={ep.episode_id} className="flex items-center justify-between px-4 py-3">
                  <div>
                    <Link
                      href={`/episodes/${ep.episode_id}`}
                      className="text-sm font-medium text-sky-400 hover:underline"
                    >
                      Episode {ep.episode_id}
                    </Link>
                    <p className="mt-1 text-xs text-slate-500">
                      {ep.products.length} product mentions detected
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        <footer className="mt-10 border-t border-slate-800 pt-4 text-xs text-slate-500">
          <p>Some links may be affiliate links.</p>
        </footer>
      </div>
    </main>
  );
}
