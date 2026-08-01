import type { ImportResponse } from './types'

interface ErrorPayload {
  error?: { message?: string }
}

export async function importRecipe(url: string): Promise<ImportResponse> {
  let response: Response
  try {
    response = await fetch('/api/scrape', {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    })
  } catch {
    throw new Error('The server could not be reached.')
  }

  const payload = (await response.json().catch(() => ({}))) as ImportResponse & ErrorPayload
  if (!response.ok) {
    throw new Error(payload.error?.message ?? 'The request could not be completed.')
  }
  return payload
}
