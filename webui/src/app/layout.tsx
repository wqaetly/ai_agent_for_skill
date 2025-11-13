import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Link from 'next/link'
import { Database, Home, Settings } from 'lucide-react'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Skill Agent - RAG技能管理系统',
  description: '基于RAG的Unity技能配置管理和查询系统',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          {/* 顶部导航栏 */}
          <header className="border-b bg-white sticky top-0 z-50">
            <div className="container mx-auto px-4">
              <div className="flex h-16 items-center justify-between">
                {/* Logo */}
                <Link href="/" className="flex items-center space-x-2">
                  <Database className="h-6 w-6 text-primary" />
                  <span className="font-bold text-xl">Skill Agent</span>
                </Link>

                {/* 导航链接 */}
                <nav className="flex items-center space-x-6">
                  <Link
                    href="/"
                    className="flex items-center space-x-1 text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
                  >
                    <Home className="h-4 w-4" />
                    <span>主页</span>
                  </Link>
                  <Link
                    href="/rag"
                    className="flex items-center space-x-1 text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
                  >
                    <Database className="h-4 w-4" />
                    <span>RAG查询</span>
                  </Link>
                  <Link
                    href="/settings"
                    className="flex items-center space-x-1 text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
                  >
                    <Settings className="h-4 w-4" />
                    <span>设置</span>
                  </Link>
                </nav>
              </div>
            </div>
          </header>

          {/* 主内容区域 */}
          <main className="flex-1 bg-gray-50">
            {children}
          </main>

          {/* 页脚 */}
          <footer className="border-t bg-white py-6">
            <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
              <p>Skill Agent - Unity技能配置管理系统 v1.0.0</p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
