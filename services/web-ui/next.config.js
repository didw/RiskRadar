/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // 메모리 사용량 줄이기
  experimental: {
    // 빌드 시 메모리 최적화
    workerThreads: false,
    cpus: 1
  },
  
  // 개발 모드 최적화
  webpack: (config, { dev }) => {
    if (dev) {
      // 개발 모드에서 메모리 사용량 줄이기
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'async',
          minSize: 20000,
          maxSize: 244000,
        }
      };
      
      // Source map 비활성화 (메모리 절약)
      config.devtool = false;
    }
    return config;
  },

  // SWC 컴파일러 설정 (더 빠르고 메모리 효율적)
  swcMinify: true,
  
  typescript: {
    // !! WARN !!
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    // !! WARN !!
    ignoreBuildErrors: false,
  },
  
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: false,
  },
}

module.exports = nextConfig