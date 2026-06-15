import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "172.23.148.30",
    "172.23.148.30:3000",
    "http://172.23.148.30:3000",
    "http://172.23.148.30:8080",
    "localhost",
    "localhost:3000",
    "http://localhost:3000",
    "http://localhost:8080",
  ],
};

export default nextConfig;