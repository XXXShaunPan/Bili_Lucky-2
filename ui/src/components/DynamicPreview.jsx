import { useEffect, useMemo, useState } from 'react'
import {
  AtSign,
  CalendarDays,
  ChevronDown,
  ExternalLink,
  FileJson,
  Heart,
  ImageOff,
  LoaderCircle,
  MessageCircle,
  Repeat2,
  Share2,
  X,
} from 'lucide-react'
import { apiRequest } from '../api'

function MetaItem({ label, value }) {
  return (
    <div className="preview-meta-item">
      <span>{label}</span>
      <strong title={value || '—'}>{value || '—'}</strong>
    </div>
  )
}

function Stat({ icon, label, value }) {
  return (
    <div className="preview-stat">
      {icon}
      <span>{label}</span>
      <strong>{Number(value || 0).toLocaleString('zh-CN')}</strong>
    </div>
  )
}

function MediaTile({ media }) {
  const [failed, setFailed] = useState(false)
  if (failed) {
    return (
      <div className="media-fallback">
        <ImageOff size={24} />
        <span>图片加载失败</span>
      </div>
    )
  }
  return (
    <img
      src={media.url}
      alt="动态媒体"
      onError={() => setFailed(true)}
    />
  )
}

export default function DynamicPreview({ dynamic, onClose }) {
  const [detail, setDetail] = useState(dynamic)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    apiRequest(`/api/dynamics/${dynamic.id}`)
      .then((payload) => active && setDetail(payload.item))
      .catch((requestError) => active && setError(requestError.message))
      .finally(() => active && setLoading(false))
    return () => { active = false }
  }, [dynamic.id])

  useEffect(() => {
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    function onKeyDown(event) {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [onClose])

  const rawJson = useMemo(
    () => JSON.stringify(detail?.raw || {}, null, 2),
    [detail],
  )

  return (
    <div className="preview-backdrop" role="presentation" onMouseDown={onClose}>
      <article
        className="preview-dialog"
        role="dialog"
        aria-modal="true"
        aria-label="动态预览"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="preview-header">
          <div className="preview-author">
            <span className="avatar-fallback">
              <AtSign size={20} />
              {detail.author?.face && (
                <img
                  src={detail.author.face}
                  alt=""
                  onError={(event) => { event.currentTarget.style.display = 'none' }}
                />
              )}
            </span>
            <span>
              <strong>{detail.author?.name || '未知发布者'}</strong>
              <small>{detail.author?.mid ? `UID ${detail.author.mid}` : '动态详情'}</small>
            </span>
          </div>
          <div className="preview-actions">
            <a href={detail.url} target="_blank" rel="noreferrer">
              <ExternalLink size={17} />
              Bilibili
            </a>
            <button type="button" aria-label="关闭预览" onClick={onClose}>
              <X size={20} />
            </button>
          </div>
        </header>

        <div className="preview-scroll">
          {loading && (
            <div className="preview-loading"><LoaderCircle className="spin" /> 获取完整数据</div>
          )}
          {error && <div className="preview-error">{error}</div>}

          <div className="preview-hero">
            <div className="preview-copy">
              <div className="preview-time">
                <CalendarDays size={15} />
                {detail.published_at
                  ? new Date(detail.published_at).toLocaleString('zh-CN')
                  : detail.published_label || '时间未知'}
              </div>
              <p>{detail.text || '该动态没有文字内容。'}</p>
            </div>

            {detail.media?.length > 0 && (
              <div className={`preview-media media-count-${Math.min(detail.media.length, 4)}`}>
                {detail.media.slice(0, 4).map((media, index) => (
                  <MediaTile key={`${media.url}-${index}`} media={media} />
                ))}
              </div>
            )}
          </div>

          <div className="preview-stats">
            <Stat icon={<Repeat2 size={18} />} label="转发" value={detail.stats?.forward} />
            <Stat icon={<MessageCircle size={18} />} label="评论" value={detail.stats?.comment} />
            <Stat icon={<Heart size={18} />} label="点赞" value={detail.stats?.like} />
            <Stat icon={<Share2 size={18} />} label="媒体" value={detail.media?.length} />
          </div>

          <section className="preview-section">
            <h3>动态信息</h3>
            <div className="preview-meta-grid">
              <MetaItem label="动态 ID" value={detail.id} />
              <MetaItem label="动态类型" value={detail.type} />
              <MetaItem label="评论 OID" value={detail.comment_id} />
              <MetaItem label="评论类型" value={String(detail.comment_type || '')} />
              <MetaItem label="原动态 ID" value={detail.origin_id} />
              <MetaItem
                label="账号类型"
                value={detail.author?.official_type === 1 ? '官方认证' : '普通账号'}
              />
            </div>
          </section>

          <details className="raw-details">
            <summary>
              <span><FileJson size={18} />完整原始数据</span>
              <ChevronDown size={18} />
            </summary>
            <pre>{rawJson}</pre>
          </details>
        </div>
      </article>
    </div>
  )
}
