/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // 允许访问本地API
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:2024/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
