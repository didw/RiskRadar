const crypto = require('crypto');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // 이미지 최적화
  images: {
    domains: ['cdn.riskradar.ai', 'localhost'],
    formats: ['image/avif', 'image/webp'],
  },
  
  // 메모리 사용량 줄이기
  experimental: {
    // 빌드 시 메모리 최적화
    workerThreads: false,
    cpus: 1
  },
  
  // 개발 모드 최적화
  webpack: (config, { dev, isServer }) => {
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
    
    // 프로덕션 빌드 최적화
    if (!dev && !isServer) {
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            default: false,
            vendors: false,
            commons: {
              name: 'commons',
              chunks: 'all',
              minChunks: 2,
            },
            lib: {
              test(module) {
                return module.size() > 160000;
              },
              name(module) {
                const hash = crypto.createHash('sha1');
                hash.update(module.identifier());
                return hash.digest('hex').substring(0, 8);
              },
              priority: 30,
              minChunks: 1,
              reuseExistingChunk: true,
            },
          },
        },
      };
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