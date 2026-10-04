// esbuild config for the frontend build stage (Node only here, never in the
// final Docker image). Real bundling of stage.js/audio.js/tilt.js lands in M4;
// this placeholder produces a valid dist/ so the Docker build stays green.
import { execSync } from "node:child_process";
import { mkdirSync, writeFileSync, existsSync } from "node:fs";

mkdirSync("dist", { recursive: true });

if (existsSync("node_modules/.bin/tailwindcss")) {
  execSync(
    "node_modules/.bin/tailwindcss -i src/css/app.css -o dist/app.css --minify",
    { stdio: "inherit" },
  );
} else {
  writeFileSync("dist/app.css", "");
}

writeFileSync("dist/stage.js", "// 3D stage bundle placeholder, built in M4\n");
