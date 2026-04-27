/** @type {import('next').NextConfig} */
const nextConfig = {
  // This allows the specific network IP that is causing the block
  allowedDevOrigins: ['10.250.50.121'],
  
  // This helps bridge the gap to your Python backend
  async rewrites() {
    return [
      {
        source: '/api/predict',
        destination: 'http://127.0.0.1:8000/predict',
      },
    ];
  },
};

module.exports = nextConfig;