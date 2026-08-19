import { AlertCircle, Inbox, LoaderCircle } from 'lucide-react'

export function LoadingState({ label = '正在加载数据' }) {
  return (
    <div className="state-block">
      <LoaderCircle className="spin" size={25} />
      <strong>{label}</strong>
      <span>正在与 Bilibili API 同步</span>
    </div>
  )
}

export function EmptyState({ title, description }) {
  return (
    <div className="state-block">
      <Inbox size={26} />
      <strong>{title}</strong>
      <span>{description}</span>
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="state-block state-error">
      <AlertCircle size={26} />
      <strong>加载失败</strong>
      <span>{message}</span>
      {onRetry && <button type="button" onClick={onRetry}>重新加载</button>}
    </div>
  )
}
