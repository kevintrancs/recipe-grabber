import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from './App'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function grab(value: string) {
  fireEvent.change(screen.getByLabelText('Recipe URL or grocery item'), { target: { value } })
  fireEvent.click(screen.getByRole('button', { name: 'Grab ingredients' }))
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('Recipe Grabber', () => {
  it('adds a manual grocery item without contacting the API', () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch')
    render(<App />)

    grab('ripe avocados')

    expect(screen.getByDisplayValue('ripe avocados')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('imports ingredients and renders the source recipe', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse({
        title: 'Summer tomatoes',
        source_url: 'https://recipes.example/tomatoes',
        ingredients: ['2 ripe tomatoes', '1 tbsp olive oil'],
      }),
    )
    render(<App />)

    grab('https://recipes.example/tomatoes')

    await waitFor(() => expect(screen.getByText('Summer tomatoes')).toBeInTheDocument())
    expect(screen.getByDisplayValue('2 ripe tomatoes')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'View original recipe ↗' })).toHaveAttribute(
      'href',
      'https://recipes.example/tomatoes',
    )
  })

  it('merges a second recipe without duplicating shared ingredients', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        jsonResponse({
          title: 'One',
          source_url: 'https://recipes.example/one',
          ingredients: ['2 ripe tomatoes', 'olive oil'],
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          title: 'Two',
          source_url: 'https://recipes.example/two',
          ingredients: ['Olive   Oil', '1 red onion'],
        }),
      )
    render(<App />)

    grab('https://recipes.example/one')
    await waitFor(() => expect(screen.getByDisplayValue('2 ripe tomatoes')).toBeInTheDocument())

    grab('https://recipes.example/two')
    await waitFor(() => expect(screen.getByDisplayValue('1 red onion')).toBeInTheDocument())

    // Differing case and whitespace still count as the same ingredient.
    expect(screen.getAllByDisplayValue(/olive oil/i)).toHaveLength(1)
    expect(screen.getAllByRole('checkbox')).toHaveLength(3)
  })

  it('reports an import failure and keeps the existing list', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse({ error: { code: 'recipe_not_found', message: 'No ingredients found.' } }, 422),
    )
    render(<App />)

    grab('onions')
    grab('https://recipes.example/mystery')

    await waitFor(() => expect(screen.getByText('No ingredients found.')).toBeInTheDocument())
    expect(screen.getByDisplayValue('onions')).toBeInTheDocument()
  })
})
