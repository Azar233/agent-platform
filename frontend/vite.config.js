import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // [PWA] 配置渐进式 Web 应用，支持添加到手机主屏幕
    VitePWA({
      registerType: 'autoUpdate',
      manifest: false, // 使用 public/manifest.json，不通过插件内联生成
      workbox: {
        // [PWA] 缓存策略：缓存所有静态资源，提升离线体验
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
      },
      devOptions: {
        // [PWA] 开发模式下也启用 PWA，方便调试
        enabled: true,
      },
    }),
  ],
  //路径别名
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  //css预处理器配置
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/assets/styles/variables.scss" as *;`,
      },
    },
  },
  //开发服务器配置
  server: {
    port: 5173,
    open: true, // 启动时⾃动打开浏览器
    // API 代理：将 /api 开头的请求转发到后端
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    // 使用 happy-dom 模拟浏览器环境
    environment: "happy-dom",
    // 全局 setup 文件
    setupFiles: ["./tests/setup.js"],
    // 测试文件匹配模式
    include: ["tests/**/*.{test,spec}.{js,ts}"],
    // 覆盖率(可选)
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
    },
  },
})
