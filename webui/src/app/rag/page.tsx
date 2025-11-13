'use client'

import { useState, useEffect, useCallback } from 'react'
import { Search, Zap, FileJson, Database, AlertCircle, CheckCircle, Copy, ChevronDown, ChevronUp, RefreshCw, Trash2, BarChart3 } from 'lucide-react'

// ==================== 类型定义 ====================

type TabType = 'search' | 'actions' | 'parameters' | 'index'

interface SearchResult {
  skill_id: string
  skill_name: string
  similarity: number
  actions: string[]
  full_data?: any
}

interface ActionRecommendation {
  action_type: string
  similarity: number
  description: string
  usage_suggestion: string
}

interface ParameterExample {
  source_skill: string
  similarity: number
  parameters: any
}

interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  skill_count: number
  action_count: number
  last_updated: string
}

interface IndexStats {
  total_skills: number
  total_actions: number
  total_parameters: number
  index_size_mb: number
}

interface ToastMessage {
  type: 'success' | 'error' | 'info'
  message: string
}

// ==================== API配置 ====================

const API_BASE_URL = 'http://localhost:2024'

// ==================== 主组件 ====================

export default function RAGPage() {
  const [activeTab, setActiveTab] = useState<TabType>('search')
  const [toast, setToast] = useState<ToastMessage | null>(null)
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)

  // 显示Toast消息
  const showToast = useCallback((type: ToastMessage['type'], message: string) => {
    setToast({ type, message })
    setTimeout(() => setToast(null), 4000)
  }, [])

  // 检查服务健康状态
  const checkHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/rag/health`)
      if (!response.ok) throw new Error('服务不可用')
      const data = await response.json()
      setHealthStatus(data)
    } catch (error) {
      console.error('健康检查失败:', error)
      setHealthStatus({
        status: 'unhealthy',
        skill_count: 0,
        action_count: 0,
        last_updated: '未知'
      })
    }
  }, [])

  // 页面加载时检查服务状态
  useEffect(() => {
    checkHealth()
  }, [checkHealth])

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* 页面头部 */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">RAG 技能查询系统</h1>
          <p className="text-gray-600">基于向量数据库的智能技能检索与推荐</p>

          {/* 服务状态指示器 */}
          {healthStatus && (
            <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow-sm">
              {healthStatus.status === 'healthy' ? (
                <CheckCircle className="w-4 h-4 text-green-500" />
              ) : (
                <AlertCircle className="w-4 h-4 text-red-500" />
              )}
              <span className="text-sm text-gray-600">
                服务状态: <span className={healthStatus.status === 'healthy' ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                  {healthStatus.status === 'healthy' ? '正常' : '异常'}
                </span>
                {healthStatus.status === 'healthy' && (
                  <span className="ml-2 text-gray-500">
                    | 技能: {healthStatus.skill_count} | Action: {healthStatus.action_count}
                  </span>
                )}
              </span>
            </div>
          )}
        </div>

        {/* Tab导航 */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <nav className="flex border-b">
            <TabButton
              icon={<Search className="w-5 h-5" />}
              label="技能搜索"
              active={activeTab === 'search'}
              onClick={() => setActiveTab('search')}
            />
            <TabButton
              icon={<Zap className="w-5 h-5" />}
              label="Action推荐"
              active={activeTab === 'actions'}
              onClick={() => setActiveTab('actions')}
            />
            <TabButton
              icon={<FileJson className="w-5 h-5" />}
              label="参数推荐"
              active={activeTab === 'parameters'}
              onClick={() => setActiveTab('parameters')}
            />
            <TabButton
              icon={<Database className="w-5 h-5" />}
              label="索引管理"
              active={activeTab === 'index'}
              onClick={() => setActiveTab('index')}
            />
          </nav>

          {/* Tab内容 */}
          <div className="p-6">
            {activeTab === 'search' && <SearchTab showToast={showToast} />}
            {activeTab === 'actions' && <ActionsTab showToast={showToast} />}
            {activeTab === 'parameters' && <ParametersTab showToast={showToast} />}
            {activeTab === 'index' && <IndexTab showToast={showToast} onHealthUpdate={checkHealth} />}
          </div>
        </div>

        {/* Toast消息 */}
        {toast && (
          <Toast
            type={toast.type}
            message={toast.message}
            onClose={() => setToast(null)}
          />
        )}
      </div>
    </div>
  )
}

// ==================== Tab按钮组件 ====================

interface TabButtonProps {
  icon: React.ReactNode
  label: string
  active: boolean
  onClick: () => void
}

function TabButton({ icon, label, active, onClick }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors relative ${
        active
          ? 'text-blue-600'
          : 'text-gray-600 hover:text-gray-800'
      }`}
    >
      {icon}
      <span>{label}</span>
      {active && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />
      )}
    </button>
  )
}

// ==================== 技能搜索Tab ====================

interface SearchTabProps {
  showToast: (type: ToastMessage['type'], message: string) => void
}

function SearchTab({ showToast }: SearchTabProps) {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [filters, setFilters] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<SearchResult[]>([])
  const [expandedResults, setExpandedResults] = useState<Set<string>>(new Set())

  const handleSearch = async () => {
    if (!query.trim()) {
      showToast('error', '请输入查询内容')
      return
    }

    setLoading(true)
    try {
      let filtersObj = undefined
      if (filters.trim()) {
        try {
          filtersObj = JSON.parse(filters)
        } catch (e) {
          showToast('error', '过滤条件JSON格式错误')
          setLoading(false)
          return
        }
      }

      const response = await fetch(`${API_BASE_URL}/rag/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          top_k: topK,
          filters: filtersObj
        })
      })

      if (!response.ok) {
        throw new Error(`搜索失败: ${response.statusText}`)
      }

      const data = await response.json()
      setResults(data.results || [])
      showToast('success', `找到 ${data.results?.length || 0} 个相关技能`)
    } catch (error) {
      console.error('搜索出错:', error)
      showToast('error', error instanceof Error ? error.message : '搜索失败')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const toggleExpand = (skillId: string) => {
    const newExpanded = new Set(expandedResults)
    if (newExpanded.has(skillId)) {
      newExpanded.delete(skillId)
    } else {
      newExpanded.add(skillId)
    }
    setExpandedResults(newExpanded)
  }

  return (
    <div className="space-y-6">
      {/* 搜索输入区 */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            查询内容
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="输入查询，如：AOE伤害技能"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>搜索中...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>搜索</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* 高级选项 */}
        <div>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
          >
            {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            <span>高级选项</span>
          </button>

          {showAdvanced && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  返回数量: {topK}
                </label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>1</span>
                  <span>10</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  过滤条件 (可选JSON)
                </label>
                <textarea
                  value={filters}
                  onChange={(e) => setFilters(e.target.value)}
                  placeholder='例如: {"skill_type": "attack"}'
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none font-mono text-sm"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 搜索结果 */}
      {results.length > 0 ? (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">搜索结果</h3>
          {results.map((result) => (
            <div
              key={result.skill_id}
              className="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h4 className="text-xl font-bold text-gray-800 mb-1">
                    {result.skill_name}
                  </h4>
                  <p className="text-sm text-gray-500">{result.skill_id}</p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-2xl font-bold text-blue-600">
                      {(result.similarity * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">相似度</div>
                  </div>
                </div>
              </div>

              {/* 相似度进度条 */}
              <div className="mb-4">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${result.similarity * 100}%` }}
                  />
                </div>
              </div>

              {/* Actions标签 */}
              {result.actions && result.actions.length > 0 && (
                <div className="mb-3">
                  <div className="flex flex-wrap gap-2">
                    {result.actions.map((action, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full"
                      >
                        {action}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 展开完整JSON */}
              <button
                onClick={() => toggleExpand(result.skill_id)}
                className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
              >
                {expandedResults.has(result.skill_id) ? (
                  <>
                    <ChevronUp className="w-4 h-4" />
                    <span>收起</span>
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-4 h-4" />
                    <span>查看完整JSON</span>
                  </>
                )}
              </button>

              {expandedResults.has(result.skill_id) && result.full_data && (
                <div className="mt-3">
                  <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs">
                    {JSON.stringify(result.full_data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : !loading && (
        <EmptyState message="暂无搜索结果，请输入查询内容后点击搜索" />
      )}
    </div>
  )
}

// ==================== Action推荐Tab ====================

interface ActionsTabProps {
  showToast: (type: ToastMessage['type'], message: string) => void
}

function ActionsTab({ showToast }: ActionsTabProps) {
  const [context, setContext] = useState('')
  const [topK, setTopK] = useState(3)
  const [loading, setLoading] = useState(false)
  const [recommendations, setRecommendations] = useState<ActionRecommendation[]>([])

  const handleRecommend = async () => {
    if (!context.trim()) {
      showToast('error', '请输入上下文描述')
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/rag/recommend-actions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          context,
          top_k: topK
        })
      })

      if (!response.ok) {
        throw new Error(`推荐失败: ${response.statusText}`)
      }

      const data = await response.json()
      setRecommendations(data.recommendations || [])
      showToast('success', `获得 ${data.recommendations?.length || 0} 个Action推荐`)
    } catch (error) {
      console.error('推荐出错:', error)
      showToast('error', error instanceof Error ? error.message : '推荐失败')
      setRecommendations([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 输入区 */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            功能描述
          </label>
          <textarea
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="描述需要的Action功能，如：造成伤害并击退敌人"
            rows={4}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
          />
        </div>

        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              推荐数量
            </label>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            >
              {[1, 2, 3, 4, 5].map(n => (
                <option key={n} value={n}>{n} 个</option>
              ))}
            </select>
          </div>

          <div className="pt-7">
            <button
              onClick={handleRecommend}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>推荐中...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  <span>获取推荐</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* 推荐结果 */}
      {recommendations.length > 0 ? (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">推荐结果</h3>
          <div className="grid gap-4">
            {recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="bg-gradient-to-r from-blue-50 to-white border border-blue-200 rounded-lg p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                      {idx + 1}
                    </div>
                    <div>
                      <h4 className="text-lg font-bold text-gray-800">
                        {rec.action_type}
                      </h4>
                      <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-blue-600">
                      {(rec.similarity * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">匹配度</div>
                  </div>
                </div>

                {/* 使用建议 */}
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <div className="text-sm font-medium text-gray-700 mb-1">使用建议:</div>
                  <p className="text-sm text-gray-600">{rec.usage_suggestion}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : !loading && (
        <EmptyState message="暂无推荐结果，请输入功能描述后点击获取推荐" />
      )}
    </div>
  )
}

// ==================== 参数推荐Tab ====================

interface ParametersTabProps {
  showToast: (type: ToastMessage['type'], message: string) => void
}

function ParametersTab({ showToast }: ParametersTabProps) {
  const [actionType, setActionType] = useState('')
  const [skillContext, setSkillContext] = useState('')
  const [loading, setLoading] = useState(false)
  const [examples, setExamples] = useState<ParameterExample[]>([])
  const [expandedExamples, setExpandedExamples] = useState<Set<number>>(new Set())

  const handleRecommend = async () => {
    if (!actionType.trim()) {
      showToast('error', '请输入Action类型')
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/rag/recommend-parameters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action_type: actionType,
          skill_context: skillContext || undefined
        })
      })

      if (!response.ok) {
        throw new Error(`推荐失败: ${response.statusText}`)
      }

      const data = await response.json()
      setExamples(data.examples || [])
      showToast('success', `获得 ${data.examples?.length || 0} 个参数示例`)
    } catch (error) {
      console.error('推荐出错:', error)
      showToast('error', error instanceof Error ? error.message : '推荐失败')
      setExamples([])
    } finally {
      setLoading(false)
    }
  }

  const toggleExpand = (idx: number) => {
    const newExpanded = new Set(expandedExamples)
    if (newExpanded.has(idx)) {
      newExpanded.delete(idx)
    } else {
      newExpanded.add(idx)
    }
    setExpandedExamples(newExpanded)
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      showToast('success', '已复制到剪贴板')
    } catch (error) {
      showToast('error', '复制失败')
    }
  }

  return (
    <div className="space-y-6">
      {/* 输入区 */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Action类型 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={actionType}
            onChange={(e) => setActionType(e.target.value)}
            placeholder="例如: DamageAction"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            技能上下文 (可选)
          </label>
          <textarea
            value={skillContext}
            onChange={(e) => setSkillContext(e.target.value)}
            placeholder="描述技能的使用场景，可以获得更精准的参数推荐"
            rows={3}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
          />
        </div>

        <button
          onClick={handleRecommend}
          disabled={loading}
          className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>获取中...</span>
            </>
          ) : (
            <>
              <FileJson className="w-4 h-4" />
              <span>获取参数示例</span>
            </>
          )}
        </button>
      </div>

      {/* 参数示例 */}
      {examples.length > 0 ? (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">参数示例</h3>
          {examples.map((example, idx) => (
            <div
              key={idx}
              className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
            >
              <div
                className="p-4 bg-gradient-to-r from-purple-50 to-white cursor-pointer hover:bg-purple-100 transition-colors"
                onClick={() => toggleExpand(idx)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                      {idx + 1}
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-800">
                        {example.source_skill}
                      </h4>
                      <p className="text-sm text-gray-500">
                        相似度: {(example.similarity * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        copyToClipboard(JSON.stringify(example.parameters, null, 2))
                      }}
                      className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                      title="复制JSON"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                    {expandedExamples.has(idx) ? (
                      <ChevronUp className="w-5 h-5 text-gray-600" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-600" />
                    )}
                  </div>
                </div>
              </div>

              {expandedExamples.has(idx) && (
                <div className="p-4 bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">参数配置:</span>
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(example.parameters, null, 2))}
                      className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
                    >
                      <Copy className="w-3 h-3" />
                      <span>一键复制</span>
                    </button>
                  </div>
                  <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs">
                    {JSON.stringify(example.parameters, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : !loading && (
        <EmptyState message="暂无参数示例，请输入Action类型后点击获取参数示例" />
      )}
    </div>
  )
}

// ==================== 索引管理Tab ====================

interface IndexTabProps {
  showToast: (type: ToastMessage['type'], message: string) => void
  onHealthUpdate: () => void
}

function IndexTab({ showToast, onHealthUpdate }: IndexTabProps) {
  const [loading, setLoading] = useState(false)
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)
  const [stats, setStats] = useState<IndexStats | null>(null)
  const [showRebuildConfirm, setShowRebuildConfirm] = useState(false)
  const [operationHistory, setOperationHistory] = useState<Array<{ time: string; operation: string; status: string }>>([])

  // 加载健康状态
  const loadHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/rag/health`)
      if (!response.ok) throw new Error('获取状态失败')
      const data = await response.json()
      setHealthStatus(data)
    } catch (error) {
      console.error('加载健康状态失败:', error)
      showToast('error', '获取服务状态失败')
    }
  }

  // 加载统计信息
  const loadStats = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/rag/index/stats`)
      if (!response.ok) throw new Error('获取统计失败')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('加载统计信息失败:', error)
      showToast('error', '获取索引统计失败')
    } finally {
      setLoading(false)
    }
  }

  // 刷新所有数据
  const handleRefresh = async () => {
    await Promise.all([loadHealth(), loadStats()])
    onHealthUpdate()
    showToast('success', '刷新成功')
  }

  // 重建索引
  const handleRebuildIndex = async () => {
    setShowRebuildConfirm(false)
    setLoading(true)

    const startTime = new Date().toLocaleTimeString()

    try {
      const response = await fetch(`${API_BASE_URL}/rag/index/rebuild`, {
        method: 'POST'
      })

      if (!response.ok) throw new Error('重建失败')

      const data = await response.json()
      showToast('success', '索引重建成功')

      setOperationHistory(prev => [
        { time: startTime, operation: '重建索引', status: '成功' },
        ...prev.slice(0, 9)
      ])

      // 重新加载数据
      await handleRefresh()
    } catch (error) {
      console.error('重建索引失败:', error)
      showToast('error', error instanceof Error ? error.message : '重建索引失败')

      setOperationHistory(prev => [
        { time: startTime, operation: '重建索引', status: '失败' },
        ...prev.slice(0, 9)
      ])
    } finally {
      setLoading(false)
    }
  }

  // 清空缓存
  const handleClearCache = async () => {
    setLoading(true)
    const startTime = new Date().toLocaleTimeString()

    try {
      const response = await fetch(`${API_BASE_URL}/rag/cache`, {
        method: 'DELETE'
      })

      if (!response.ok) throw new Error('清空失败')

      showToast('success', '缓存清空成功')

      setOperationHistory(prev => [
        { time: startTime, operation: '清空缓存', status: '成功' },
        ...prev.slice(0, 9)
      ])
    } catch (error) {
      console.error('清空缓存失败:', error)
      showToast('error', error instanceof Error ? error.message : '清空缓存失败')

      setOperationHistory(prev => [
        { time: startTime, operation: '清空缓存', status: '失败' },
        ...prev.slice(0, 9)
      ])
    } finally {
      setLoading(false)
    }
  }

  // 页面加载时获取数据
  useEffect(() => {
    loadHealth()
    loadStats()
  }, [])

  return (
    <div className="space-y-6">
      {/* 服务状态卡片 */}
      <div className="bg-gradient-to-r from-blue-50 to-white border border-blue-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800">服务状态</h3>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors disabled:opacity-50"
            title="刷新"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {healthStatus ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-3">
              {healthStatus.status === 'healthy' ? (
                <CheckCircle className="w-8 h-8 text-green-500" />
              ) : (
                <AlertCircle className="w-8 h-8 text-red-500" />
              )}
              <div>
                <div className="text-sm text-gray-600">服务状态</div>
                <div className={`text-lg font-bold ${healthStatus.status === 'healthy' ? 'text-green-600' : 'text-red-600'}`}>
                  {healthStatus.status === 'healthy' ? '正常运行' : '异常'}
                </div>
              </div>
            </div>

            <div>
              <div className="text-sm text-gray-600">技能数量</div>
              <div className="text-2xl font-bold text-blue-600">
                {healthStatus.skill_count.toLocaleString()}
              </div>
            </div>

            <div>
              <div className="text-sm text-gray-600">Action数量</div>
              <div className="text-2xl font-bold text-purple-600">
                {healthStatus.action_count.toLocaleString()}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-500">加载中...</div>
        )}

        {healthStatus && (
          <div className="mt-4 pt-4 border-t border-blue-200">
            <div className="text-sm text-gray-600">
              最后更新: <span className="font-medium">{healthStatus.last_updated}</span>
            </div>
          </div>
        )}
      </div>

      {/* 索引统计 */}
      {stats && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">索引统计</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label="总技能数"
              value={stats.total_skills.toLocaleString()}
              color="blue"
            />
            <StatCard
              label="总Action数"
              value={stats.total_actions.toLocaleString()}
              color="purple"
            />
            <StatCard
              label="参数配置数"
              value={stats.total_parameters.toLocaleString()}
              color="green"
            />
            <StatCard
              label="索引大小"
              value={`${stats.index_size_mb.toFixed(2)} MB`}
              color="orange"
            />
          </div>
        </div>
      )}

      {/* 操作按钮区 */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">索引操作</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => setShowRebuildConfirm(true)}
            disabled={loading}
            className="p-4 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
          >
            <Database className="w-5 h-5" />
            <span className="font-medium">重建索引</span>
          </button>

          <button
            onClick={handleClearCache}
            disabled={loading}
            className="p-4 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
          >
            <Trash2 className="w-5 h-5" />
            <span className="font-medium">清空缓存</span>
          </button>

          <button
            onClick={handleRefresh}
            disabled={loading}
            className="p-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
          >
            <BarChart3 className="w-5 h-5" />
            <span className="font-medium">查看统计</span>
          </button>
        </div>
      </div>

      {/* 操作历史 */}
      {operationHistory.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">操作历史</h3>
          <div className="space-y-2">
            {operationHistory.map((record, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded"
              >
                <span className="text-sm text-gray-600">{record.time}</span>
                <span className="text-sm font-medium text-gray-800">{record.operation}</span>
                <span className={`text-sm font-medium ${record.status === '成功' ? 'text-green-600' : 'text-red-600'}`}>
                  {record.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 重建确认对话框 */}
      {showRebuildConfirm && (
        <ConfirmDialog
          title="确认重建索引"
          message="重建索引将清空现有数据并重新加载所有技能配置。此操作可能需要几分钟时间，确定要继续吗？"
          onConfirm={handleRebuildIndex}
          onCancel={() => setShowRebuildConfirm(false)}
        />
      )}
    </div>
  )
}

// ==================== 统计卡片组件 ====================

interface StatCardProps {
  label: string
  value: string
  color: 'blue' | 'purple' | 'green' | 'orange'
}

function StatCard({ label, value, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    purple: 'bg-purple-50 text-purple-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600'
  }

  return (
    <div className={`${colorClasses[color]} rounded-lg p-4`}>
      <div className="text-sm opacity-80 mb-1">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  )
}

// ==================== 空状态组件 ====================

interface EmptyStateProps {
  message: string
}

function EmptyState({ message }: EmptyStateProps) {
  return (
    <div className="text-center py-12">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
        <Search className="w-8 h-8 text-gray-400" />
      </div>
      <p className="text-gray-500">{message}</p>
    </div>
  )
}

// ==================== Toast消息组件 ====================

interface ToastProps {
  type: 'success' | 'error' | 'info'
  message: string
  onClose: () => void
}

function Toast({ type, message, onClose }: ToastProps) {
  const icons = {
    success: <CheckCircle className="w-5 h-5" />,
    error: <AlertCircle className="w-5 h-5" />,
    info: <AlertCircle className="w-5 h-5" />
  }

  const bgColors = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    info: 'bg-blue-500'
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 animate-slide-up">
      <div className={`${bgColors[type]} text-white px-6 py-4 rounded-lg shadow-lg flex items-center gap-3 min-w-[300px]`}>
        {icons[type]}
        <span className="flex-1">{message}</span>
        <button
          onClick={onClose}
          className="text-white hover:text-gray-200 transition-colors"
        >
          ✕
        </button>
      </div>
    </div>
  )
}

// ==================== 确认对话框组件 ====================

interface ConfirmDialogProps {
  title: string
  message: string
  onConfirm: () => void
  onCancel: () => void
}

function ConfirmDialog({ title, message, onConfirm, onCancel }: ConfirmDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 animate-fade-in">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 animate-scale-up">
        <div className="p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">{title}</h3>
          <p className="text-gray-600 mb-6">{message}</p>
          <div className="flex gap-3 justify-end">
            <button
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              onClick={onConfirm}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              确认
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
