import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET() {
  const episodesDir = path.join(process.cwd(), "public", "episodes");
  if (!fs.existsSync(episodesDir)) {
    return NextResponse.json([]);
  }

  const files = fs
    .readdirSync(episodesDir)
    .filter((f) => f.endsWith("-parsed.json"));

  const episodes = files.map((file) => {
    const fullPath = path.join(episodesDir, file);
    const data = JSON.parse(fs.readFileSync(fullPath, "utf8"));
    return data;
  });

  return NextResponse.json(episodes);
}
