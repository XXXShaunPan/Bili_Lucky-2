import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ArrowLeft,
  CalendarDays,
  Check,
  CheckSquare2,
  ChevronRight,
  CircleDot,
  FileText,
  GitFork,
  Heart,
  Layers3,
  MessageCircle,
  RefreshCw,
  Repeat2,
  Sparkles,
  UserPlus,
  X,
  LoaderCircle,
} from 'lucide-react'
import { apiRequest } from '../api'
import DynamicPreview from './DynamicPreview'
import GlassPanel from './GlassPanel'
import { EmptyState, ErrorState, LoadingState } from './States'

function formatDate(value) {
  if (!value) return '时间未知'
  return new Date(value).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function compactNumber(value) {
  return new Intl.NumberFormat('zh-CN', { notation: 'compact' }).format(value || 0)
}

function ArticleRow({ article, selected, onClick }) {
  return (
    <button
      type="button"
      className={`list-row article-row ${selected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <span className="article-cover">
        <FileText size={22} />
        {article.cover && (
          <img
            src={article.cover}
            alt=""
            onError={(event) => { event.currentTarget.style.display = 'none' }}
          />
        )}
      </span>
      <span className="row-main">
        <span className="row-title">{article.title}</span>
        <span className="row-meta">
          <span>CV {article.id}</span>
          <span>{formatDate(article.published_at)}</span>
        </span>
        <span className="article-stats">
          <span><Heart size={13} />{compactNumber(article.stats?.like)}</span>
          <span><MessageCircle size={13} />{compactNumber(article.stats?.reply)}</span>
          <i className={article.eligible ? 'eligible' : ''}>
            {article.eligible ? '待处理' : article.processed ? '已处理' : '历史'}
          </i>
        </span>
      </span>
      <ChevronRight className="row-chevron" size={18} />
    </button>
  )
}

function DynamicRow({
  dynamic,
  selected,
  checked,
  child = false,
  onClick,
  onToggle,
}) {
  function onKeyDown(event) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      onClick()
    }
  }

  return (
    <div
      className={`list-row dynamic-row ${selected ? 'selected' : ''} ${checked ? 'checked' : ''} ${child ? 'child-row' : ''}`}
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={onKeyDown}
    >
      <label
        className="glass-checkbox"
        title="选择这条动态"
        onClick={(event) => event.stopPropagation()}
      >
        <input
          type="checkbox"
          checked={checked}
          onChange={(event) => onToggle(event.target.checked)}
          aria-label={`选择动态 ${dynamic.id}`}
        />
        <span>{checked && <Check size={13} />}</span>
      </label>
      <span className="dynamic-author">
        <CircleDot size={18} />
        {dynamic.author?.face && (
          <img
            src={dynamic.author.face}
            alt=""
            onError={(event) => { event.currentTarget.style.display = 'none' }}
          />
        )}
        {dynamic.author?.official_type === 1 && <i aria-label="官方认证" />}
      </span>
      <span className="row-main">
        <span className="dynamic-name">
          {dynamic.author?.name || '未知发布者'}
          <em>{formatDate(dynamic.published_at)}</em>
        </span>
        <span className="dynamic-text">{dynamic.text || '无文字动态'}</span>
        <span className="row-meta dynamic-meta">
          <span><Repeat2 size={13} />{compactNumber(dynamic.stats?.forward)}</span>
          <span><MessageCircle size={13} />{compactNumber(dynamic.stats?.comment)}</span>
          <span>ID {dynamic.id}</span>
        </span>
        {child && dynamic.discovered_from?.name && (
          <span className="discovery-label">
            经 {dynamic.discovered_from.name} 的转发链发现
          </span>
        )}
      </span>
      <ChevronRight className="row-chevron" size={18} />
    </div>
  )
}

function SelectionDock({ count, loading, onClear, onConfirm }) {
  return (
    <div className="selection-dock" role="status">
      <span className="selection-count">
        <CheckSquare2 size={18} />
        已选择 <strong>{count}</strong> 条
      </span>
      <button type="button" className="selection-clear" onClick={onClear} disabled={loading}>
        清空
      </button>
      <button
        type="button"
        className="participate-button"
        onClick={onConfirm}
        disabled={loading || count > 30}
      >
        {loading ? <LoaderCircle className="spin" size={17} /> : <UserPlus size={17} />}
        {count > 30 ? '最多选择 30 条' : '一键关转评'}
      </button>
    </div>
  )
}

function ParticipationConfirm({ count, loading, onCancel, onSubmit }) {
  return (
    <div className="confirm-backdrop" role="presentation" onMouseDown={loading ? undefined : onCancel}>
      <section
        className="confirm-dialog"
        role="dialog"
        aria-modal="true"
        aria-label="确认一键关转评"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="confirm-icon"><CheckSquare2 size={25} /></div>
        <h2>确认参与 {count} 条动态？</h2>
        <p>系统将按顺序为每条动态执行关注、转发和评论。执行期间请勿关闭页面。</p>
        <div className="confirm-flow" aria-label="执行步骤">
          <span><UserPlus size={16} />关注</span>
          <i />
          <span><Repeat2 size={16} />转发</span>
          <i />
          <span><MessageCircle size={16} />评论</span>
        </div>
        <div className="confirm-actions">
          <button type="button" onClick={onCancel} disabled={loading}>取消</button>
          <button type="button" className="confirm-submit" onClick={onSubmit} disabled={loading}>
            {loading && <LoaderCircle className="spin" size={17} />}
            {loading ? '正在依次执行…' : '确认关转评'}
          </button>
        </div>
      </section>
    </div>
  )
}

export default function Workspace({ uid, onBack }) {
  const [articles, setArticles] = useState([])
  const [articlesState, setArticlesState] = useState({ loading: true, error: '' })
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [dynamics, setDynamics] = useState([])
  const [dynamicsState, setDynamicsState] = useState({ loading: false, error: '' })
  const [selectedDynamic, setSelectedDynamic] = useState(null)
  const [children, setChildren] = useState([])
  const [childrenState, setChildrenState] = useState({ loading: false, error: '' })
  const [previewDynamic, setPreviewDynamic] = useState(null)
  const [checkedIds, setCheckedIds] = useState(() => new Set())
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [participationState, setParticipationState] = useState({
    loading: false,
    message: '',
    tone: 'success',
  })

  const loadArticles = useCallback(() => {
    setArticlesState({ loading: true, error: '' })
    apiRequest(`/api/articles?uid=${encodeURIComponent(uid)}&limit=12`)
      .then((payload) => {
        setArticles(payload.items)
        setArticlesState({ loading: false, error: '' })
      })
      .catch((error) => setArticlesState({ loading: false, error: error.message }))
  }, [uid])

  useEffect(() => {
    loadArticles()
  }, [loadArticles])

  const selectArticle = useCallback((article) => {
    setSelectedArticle(article)
    setSelectedDynamic(null)
    setChildren([])
    setCheckedIds(new Set())
    setDynamics([])
    setDynamicsState({ loading: true, error: '' })
    apiRequest(`/api/articles/${article.id}/dynamics`)
      .then((payload) => {
        setDynamics(payload.items)
        const parseError = !payload.items.length && payload.errors?.length
          ? `已发现 ${payload.source_count} 个链接，但 ${payload.errors.length} 条动态详情获取失败。${payload.errors[0]?.error || ''}`
          : ''
        setDynamicsState({ loading: false, error: parseError })
      })
      .catch((error) => setDynamicsState({ loading: false, error: error.message }))
  }, [])

  const selectDynamic = useCallback((dynamic) => {
    setSelectedDynamic(dynamic)
    setPreviewDynamic(dynamic)
    setChildren([])
    setChildrenState({ loading: true, error: '' })
    apiRequest(`/api/dynamics/${dynamic.id}/children`)
      .then((payload) => {
        setChildren(payload.items)
        setChildrenState({ loading: false, error: '' })
      })
      .catch((error) => setChildrenState({ loading: false, error: error.message }))
  }, [])

  const toggleChecked = useCallback((dynamicId, checked) => {
    setCheckedIds((current) => {
      const next = new Set(current)
      if (checked) next.add(dynamicId)
      else next.delete(dynamicId)
      return next
    })
  }, [])

  const submitParticipation = useCallback(() => {
    const selectedIds = [...checkedIds]
    setParticipationState({ loading: true, message: '', tone: 'success' })
    apiRequest('/api/actions/participate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dynamic_ids: selectedIds }),
    })
      .then((payload) => {
        const completedIds = new Set(
          payload.results
            .filter((result) => ['success', 'already_processed'].includes(result.status))
            .map((result) => result.id),
        )
        setCheckedIds((current) => new Set(
          [...current].filter((id) => !completedIds.has(id)),
        ))
        setParticipationState({
          loading: false,
          tone: payload.failed_count ? 'warning' : 'success',
          message: `完成 ${payload.success_count} 条，已处理 ${payload.already_count} 条，失败 ${payload.failed_count} 条`,
        })
        setConfirmOpen(false)
      })
      .catch((error) => {
        setParticipationState({ loading: false, message: error.message, tone: 'error' })
        setConfirmOpen(false)
      })
  }, [checkedIds])

  const articleCountLabel = useMemo(
    () => articles.filter((article) => article.eligible).length,
    [articles],
  )

  return (
    <section className="workspace-screen">
      <header className="workspace-topbar">
        <div className="workspace-brand">
          <span className="brand-mark"><Sparkles size={18} /></span>
          <span>
            <strong>Bili Lucky Studio</strong>
            <small>动态发现工作台</small>
          </span>
        </div>

        <div className="workspace-controls">
          <div className="active-source">
            <span>Article UID</span>
            <strong>{uid}</strong>
          </div>
          <button type="button" className="icon-button" title="刷新专栏" onClick={loadArticles}>
            <RefreshCw size={18} />
          </button>
          <button type="button" className="back-button" onClick={onBack}>
            <ArrowLeft size={18} />
            切换 UID
          </button>
        </div>
      </header>

      <div className="workspace-grid">
        <GlassPanel
          icon={<FileText size={19} />}
          title="Article List"
          subtitle={`最近发布 · ${articleCountLabel} 篇待处理`}
          count={articles.length}
          tone="cyan"
        >
          {articlesState.loading ? (
            <LoadingState label="获取专栏列表" />
          ) : articlesState.error ? (
            <ErrorState message={articlesState.error} onRetry={loadArticles} />
          ) : articles.length ? (
            <div className="list-stack">
              {articles.map((article) => (
                <ArticleRow
                  key={article.id}
                  article={article}
                  selected={selectedArticle?.id === article.id}
                  onClick={() => selectArticle(article)}
                />
              ))}
            </div>
          ) : (
            <EmptyState title="没有可显示的专栏" description="请尝试切换 UID 或稍后刷新。" />
          )}
        </GlassPanel>

        <GlassPanel
          icon={<Layers3 size={19} />}
          title="Lottery Dynamics"
          subtitle={selectedArticle ? `CV ${selectedArticle.id}` : '选择左侧专栏后加载'}
          count={dynamics.length}
          tone="violet"
        >
          {!selectedArticle ? (
            <EmptyState title="等待选择 Article" description="选择一篇专栏以解析其中的抽奖动态。" />
          ) : dynamicsState.loading ? (
            <LoadingState label="解析抽奖动态" />
          ) : dynamicsState.error ? (
            <ErrorState message={dynamicsState.error} onRetry={() => selectArticle(selectedArticle)} />
          ) : dynamics.length ? (
            <div className="list-stack">
              {dynamics.map((dynamic) => (
                <DynamicRow
                  key={dynamic.id}
                  dynamic={dynamic}
                  selected={selectedDynamic?.id === dynamic.id}
                  checked={checkedIds.has(dynamic.id)}
                  onClick={() => selectDynamic(dynamic)}
                  onToggle={(checked) => toggleChecked(dynamic.id, checked)}
                />
              ))}
            </div>
          ) : (
            <EmptyState title="未解析到抽奖动态" description="该专栏可能暂时没有可处理的动态链接。" />
          )}
        </GlassPanel>

        <GlassPanel
          icon={<GitFork size={19} />}
          title="Child Dynamics"
          subtitle={selectedDynamic ? `源动态 ${selectedDynamic.id}` : '选择中间动态后发现'}
          count={children.length}
          tone="coral"
        >
          {!selectedDynamic ? (
            <EmptyState title="等待选择动态" description="选择一条动态以追踪官方子抽奖转发链。" />
          ) : childrenState.loading ? (
            <LoadingState label="追踪子动态" />
          ) : childrenState.error ? (
            <ErrorState message={childrenState.error} onRetry={() => selectDynamic(selectedDynamic)} />
          ) : children.length ? (
            <div className="list-stack">
              {children.map((dynamic) => (
                <DynamicRow
                  key={dynamic.id}
                  dynamic={dynamic}
                  child
                  checked={checkedIds.has(dynamic.id)}
                  onClick={() => setPreviewDynamic(dynamic)}
                  onToggle={(checked) => toggleChecked(dynamic.id, checked)}
                />
              ))}
            </div>
          ) : (
            <EmptyState title="没有发现子动态" description="已检查转发链，但未找到官方账号发布的子抽奖。" />
          )}
        </GlassPanel>
      </div>

      <footer className="workspace-footer">
        <span><CircleDot size={13} />API 已连接</span>
        <span><CalendarDays size={13} />筛选窗口 36 小时</span>
        <span><Repeat2 size={13} />点击动态打开完整预览</span>
      </footer>

      {previewDynamic && (
        <DynamicPreview dynamic={previewDynamic} onClose={() => setPreviewDynamic(null)} />
      )}

      {checkedIds.size > 0 && (
        <SelectionDock
          count={checkedIds.size}
          loading={participationState.loading}
          onClear={() => setCheckedIds(new Set())}
          onConfirm={() => setConfirmOpen(true)}
        />
      )}

      {confirmOpen && (
        <ParticipationConfirm
          count={checkedIds.size}
          loading={participationState.loading}
          onCancel={() => setConfirmOpen(false)}
          onSubmit={submitParticipation}
        />
      )}

      {participationState.message && (
        <div className={`action-toast toast-${participationState.tone}`}>
          <span>{participationState.message}</span>
          <button
            type="button"
            aria-label="关闭提示"
            onClick={() => setParticipationState((state) => ({ ...state, message: '' }))}
          >
            <X size={15} />
          </button>
        </div>
      )}
    </section>
  )
}
