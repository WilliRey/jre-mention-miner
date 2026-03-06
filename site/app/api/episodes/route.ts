import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

interface EpisodeMeta {
  number?: number;
  title?: string;
  guest?: string;
  notes?: string;
}

export async function GET() {
  const episodesDir = path.join(process.cwd(), "public", "episodes");
  if (!fs.existsSync(episodesDir)) {
    return NextResponse.json([]);
  }

  const metaPath = path.join(process.cwd(), "..", "config", "episodes.json");
  let meta: Record<string, EpisodeMeta> = {};
  if (fs.existsSync(metaPath)) {
    try {
      meta = JSON.parse(fs.readFileSync(metaPath, "utf8"));
    } catch {
      meta = {};
    }
  }

  const files = fs
    .readdirSync(episodesDir)
    .filter((f) => f.endsWith("-parsed.json"));

  const episodes = files.map((file) => {
    const fullPath = path.join(episodesDir, file);
    const data = JSON.parse(fs.readFileSync(fullPath, "utf8"));
    const id = data.episode_id as string;
    const m = meta[id] || {};
    return {
      ...data,
      number: m.number,
      title: m.title,
      guest: m.guest,
    };
  });

  return NextResponse.json(episodes);
}
