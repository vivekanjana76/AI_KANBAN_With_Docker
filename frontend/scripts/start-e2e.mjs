import { execSync, spawn } from "node:child_process";
import { existsSync, mkdirSync, rmSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendDir = path.resolve(__dirname, "..");
const repoRoot = path.resolve(frontendDir, "..");
const backendDir = path.join(repoRoot, "backend");
const e2eDir = path.join(frontendDir, ".e2e");
const dbPath = path.join(e2eDir, "pm.sqlite3");

const uvCommand = process.platform === "win32" ? "uv.exe" : "uv";

mkdirSync(e2eDir, { recursive: true });
if (existsSync(dbPath)) {
  rmSync(dbPath, { force: true });
}

execSync("npm run build", {
  cwd: frontendDir,
  shell: true,
  stdio: "inherit",
});

const server = spawn(
  uvCommand,
  ["run", "--directory", backendDir, "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
  {
    cwd: repoRoot,
    stdio: "inherit",
    env: {
      ...process.env,
      DB_PATH: dbPath,
      SESSION_SECRET: "e2e-session-secret",
    },
  }
);

const shutdown = (signal) => {
  if (!server.killed) {
    server.kill(signal);
  }
};

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));

server.on("exit", (code, signal) => {
  if (signal) {
    process.exit(0);
  }
  process.exit(code ?? 0);
});
