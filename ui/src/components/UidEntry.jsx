import { useMemo, useState } from 'react'
import {
  ArrowRight,
  Check,
  CircleUserRound,
  Radio,
  Sparkles,
} from 'lucide-react'

const UID_META = {
  226257459: {
    label: '_大锦鲤_',
    tint: 'cyan',
  },
  100680137: {
    label: '你的抽奖工具人',
    tint: 'violet',
  },
}

export default function UidEntry({ uids, error, onEnter }) {
  const [selected, setSelected] = useState('')
  const [customUid, setCustomUid] = useState('')

  const options = useMemo(
    () => [...new Set((uids || []).map(String))],
    [uids],
  )
  const activeUid = selected === 'custom' ? customUid.trim() : selected
  const canEnter = /^\d+$/.test(activeUid)

  function submit(event) {
    event.preventDefault()
    if (canEnter) onEnter(activeUid)
  }

  return (
    <section className="entry-screen">
      <div className="entry-brand" aria-label="Bili Lucky Studio">
        <span className="brand-mark"><Sparkles size={19} /></span>
        <span>Bili Lucky Studio</span>
      </div>

      <form className="entry-glass" onSubmit={submit}>
        <div className="entry-copy">
          <h1>选择 Article UID</h1>
          <p>先选择抽奖专栏来源，再进入动态浏览工作台。</p>
        </div>

        <div className="uid-options" role="radiogroup" aria-label="Article UID">
          {options.map((uid, index) => {
            const meta = UID_META[uid] || {
              label: `专栏来源 ${index + 1}`,
              tint: index % 2 ? 'violet' : 'cyan',
            }
            const isSelected = selected === uid
            return (
              <button
                className={`uid-option tint-${meta.tint} ${isSelected ? 'selected' : ''}`}
                type="button"
                role="radio"
                aria-checked={isSelected}
                key={uid}
                onClick={() => setSelected(uid)}
              >
                <span className="uid-avatar"><Radio size={20} /></span>
                <span className="uid-details">
                  <strong>{meta.label}</strong>
                  <span>{uid}</span>
                </span>
                <span className="uid-check">{isSelected && <Check size={17} />}</span>
              </button>
            )
          })}

          <div className={`custom-uid ${selected === 'custom' ? 'selected' : ''}`}>
            <button
              type="button"
              className="custom-uid-label"
              onClick={() => setSelected('custom')}
            >
              <span className="uid-avatar"><CircleUserRound size={20} /></span>
              <span>
                <strong>自定义 UID</strong>
                <small>输入其他专栏作者</small>
              </span>
            </button>
            <input
              inputMode="numeric"
              pattern="[0-9]*"
              aria-label="自定义 Article UID"
              placeholder="输入 UID"
              value={customUid}
              onFocus={() => setSelected('custom')}
              onChange={(event) => {
                setSelected('custom')
                setCustomUid(event.target.value.replace(/\D/g, ''))
              }}
            />
          </div>
        </div>

        {error && <p className="entry-error">{error}</p>}

        <button className="primary-liquid-button" type="submit" disabled={!canEnter}>
          <span>进入工作台</span>
          <ArrowRight size={19} />
        </button>

        <div className="entry-status">
          <span className="status-dot" />
          本地数据界面 · 使用现有脚本配置
        </div>
      </form>
    </section>
  )
}
