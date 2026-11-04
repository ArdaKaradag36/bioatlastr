import type { NextConfig } from "next";

// Plain (classic) static generation: pages are built once from public/data/*.json.
// No `output: "export"` on purpose, so a server endpoint (e.g. /api/identify for
// photo identification) can be added later without changing the deployment.
const nextConfig: NextConfig = {
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
