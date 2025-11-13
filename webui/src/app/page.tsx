import Link from 'next/link'
import { Database, Search, Zap, FileJson, ArrowRight } from 'lucide-react'

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-12">
      {/* Hero Section */}
      <div className="text-center mb-16">
        <h1 className="text-4xl font-bold mb-4">
          Skill Agent
        </h1>
        <p className="text-xl text-muted-foreground mb-8">
          基于RAG的Unity技能配置管理和查询系统
        </p>
        <Link
          href="/rag"
          className="inline-flex items-center space-x-2 bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors"
        >
          <span>开始使用</span>
          <ArrowRight className="h-5 w-5" />
        </Link>
      </div>

      {/* 功能特性 */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
        <FeatureCard
          icon={<Search className="h-8 w-8 text-primary" />}
          title="技能语义搜索"
          description="使用自然语言搜索相似的技能配置，快速找到参考实现"
        />
        <FeatureCard
          icon={<Zap className="h-8 w-8 text-primary" />}
          title="Action智能推荐"
          description="根据上下文描述推荐合适的Action类型，提升开发效率"
        />
        <FeatureCard
          icon={<FileJson className="h-8 w-8 text-primary" />}
          title="参数智能推荐"
          description="为指定Action类型推荐参数配置示例，减少重复工作"
        />
        <FeatureCard
          icon={<Database className="h-8 w-8 text-primary" />}
          title="索引管理"
          description="实时查看索引状态，一键重建RAG索引，管理查询缓存"
        />
      </div>

      {/* 快速开始指南 */}
      <div className="bg-white rounded-lg border p-8">
        <h2 className="text-2xl font-bold mb-6">快速开始</h2>
        <div className="space-y-4">
          <Step
            number={1}
            title="确保后端服务运行"
            description="在Unity中: Tools → SkillAgent → 启动服务器"
          />
          <Step
            number={2}
            title="访问RAG查询页面"
            description="点击顶部导航栏的 'RAG查询' 或上方的 '开始使用' 按钮"
          />
          <Step
            number={3}
            title="开始查询"
            description="输入自然语言查询，获取技能推荐和参数建议"
          />
        </div>
      </div>

      {/* 系统状态 */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-2">💡 提示</h3>
        <p className="text-blue-800 text-sm">
          本系统已从Unity Editor完全迁移到WebUI。所有RAG查询、Inspector智能推荐功能现在都在此WebUI中完成。
          Unity端仅保留技能编辑和描述管理功能。详见{' '}
          <a href="/MIGRATION_GUIDE.md" className="underline font-medium">迁移指南</a>
        </p>
      </div>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div className="bg-white rounded-lg border p-6 hover:shadow-md transition-shadow">
      <div className="mb-4">{icon}</div>
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  )
}

function Step({
  number,
  title,
  description,
}: {
  number: number
  title: string
  description: string
}) {
  return (
    <div className="flex items-start space-x-4">
      <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold">
        {number}
      </div>
      <div>
        <h4 className="font-semibold mb-1">{title}</h4>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  )
}
