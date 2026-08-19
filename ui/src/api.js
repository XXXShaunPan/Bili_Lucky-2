export async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      Accept: 'application/json',
      ...options.headers,
    },
    ...options,
  })

  const payload = await response.json().catch(() => ({
    ok: false,
    error: `服务器返回了无法解析的响应 (${response.status})`,
  }))

  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || `请求失败 (${response.status})`)
  }
  return payload
}
