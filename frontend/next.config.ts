import type { NextConfig } from "next"
import { PHASE_DEVELOPMENT_SERVER } from "next/constants.js"

export default function nextConfig(phase: string): NextConfig {
  return {
    ...(phase === PHASE_DEVELOPMENT_SERVER && {
      async rewrites() {
        return [{ source: "/api/analyze", destination: "http://127.0.0.1:8000/analyze" }]
      },
    }),
    async headers() {
      return [
        {
          source: "/(.*)",
          headers: [
            { key: "X-Content-Type-Options", value: "nosniff" },
            { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
            { key: "Strict-Transport-Security", value: "max-age=63072000" },
            { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          ],
        },
      ]
    },
  }
}
