export type SseEvent = {
  event?: string
  data: string
}

export async function streamSse(
  url: string,
  options: { signal?: AbortSignal } = {},
  onEvent?: (evt: SseEvent) => void,
) {
  try {
    const headers: Record<string, string> = {
      Accept: 'text/event-stream',
    }

    if (typeof localStorage !== 'undefined') {
      const token = localStorage.getItem('token')
      if (token && token !== 'null' && token !== 'undefined') {
        headers.Authorization = `Bearer ${token}`
      }
    }

    const res = await fetch(url, {
      method: 'GET',
      signal: options.signal,
      headers,
    })

    if (!res.ok) {
      throw new Error(`SSE request failed: ${res.status}`)
    }

    if (!res.body) {
      throw new Error('SSE response has no body')
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder('utf-8')

    let buffer = ''
    let currentEvent: string | undefined
    let dataLines: string[] = []

    const flush = () => {
      if (!dataLines.length) return
      const data = dataLines.join('\n')
      dataLines = []
      onEvent?.({ event: currentEvent, data })
      currentEvent = undefined
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        flush()
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split(/\r?\n/)
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (line === '') {
          flush()
          continue
        }
        if (line.startsWith(':')) continue

        const idx = line.indexOf(':')
        const field = idx === -1 ? line : line.slice(0, idx)
        let val = idx === -1 ? '' : line.slice(idx + 1)
        if (val.startsWith(' ')) val = val.slice(1)

        if (field === 'event') currentEvent = val
        if (field === 'data') dataLines.push(val)
      }
    }
  } catch (err) {
    if (options.signal?.aborted) return
    if ((err as any)?.name === 'AbortError') return
    throw err
  }
}
