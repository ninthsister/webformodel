import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "172.23.148.30",
    "172.23.148.30:3000",
    "http://172.23.148.30:3000",
    "http://172.23.148.30:8080",
  ],
};

export default nextConfig;