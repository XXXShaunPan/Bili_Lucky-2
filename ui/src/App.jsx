import { useEffect, useState } from 'react'
import { apiRequest } from './api'
import UidEntry from './components/UidEntry'
import Workspace from './components/Workspace'

function AmbientBackground() {
  return (
    <div className="ambient-background" aria-hidden="true">
      <span className="ambient-orb orb-cyan" />
      <span className="ambient-orb orb-violet" />
      <span className="ambient-orb orb-coral" />
      <span className="ambient-orb orb-lime" />
      <span className="ambient-noise" />
    </div>
  )
}

export default function App() {
  const [config, setConfig] = useState({ article_uids: [] })
  const [selectedUid, setSelectedUid] = useState('')
  const [configError, setConfigError] = useState('')

  useEffect(() => {
    apiRequest('/api/config')
      .then(setConfig)
      .catch((error) => setConfigError(error.message))
  }, [])

  return (
    <main className="app-shell">
      <AmbientBackground />
      {selectedUid ? (
        <Workspace
          uid={selectedUid}
          onBack={() => setSelectedUid('')}
        />
      ) : (
        <UidEntry
          uids={config.article_uids}
          error={configError}
          onEnter={setSelectedUid}
        />
      )}
    </main>
  )
}
