import fs from "fs";
import path from "path";

const rootEpisodes = path.resolve(process.cwd(), "..", "public", "episodes");
const siteEpisodes = path.resolve(process.cwd(), "public", "episodes");

if (!fs.existsSync(rootEpisodes)) {
  console.log("No root episodes directory yet, skipping copy.");
  process.exit(0);
}

fs.mkdirSync(siteEpisodes, { recursive: true });

for (const file of fs.readdirSync(rootEpisodes)) {
  const src = path.join(rootEpisodes, file);
  const dest = path.join(siteEpisodes, file);
  fs.copyFileSync(src, dest);
}

console.log("Copied episodes into site/public/episodes");
