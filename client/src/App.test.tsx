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

/** Mirrors the server: every recipe line carries the food it names. */
function recipe(title: string, ingredients: [text: string, name: string][]) {
  return {
    title,
    source_url: `https://recipes.example/${title}`,
    ingredients: ingredients.map(([text, name]) => ({ text, name })),
  }
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

  it('lists the food name rather than the recipe line', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse(
        recipe('Summer tomatoes', [
          ['2 ripe tomatoes', 'tomatoes'],
          ['1 tbsp olive oil', 'olive oil'],
        ]),
      ),
    )
    render(<App />)

    grab('https://recipes.example/tomatoes')

    await waitFor(() => expect(screen.getByText('Summer tomatoes')).toBeInTheDocument())
    expect(screen.getByDisplayValue('tomatoes')).toBeInTheDocument()
    expect(screen.queryByDisplayValue('2 ripe tomatoes')).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'View original recipe ↗' })).toHaveAttribute(
      'href',
      'https://recipes.example/Summer tomatoes',
    )
  })

  it('collapses lines that name the same food onto one row', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse(
        recipe('Garlic everything', [
          ['10 cloves garlic, minced', 'garlic'],
          ['3 cloves roasted garlic', 'garlic'],
          ['1 red onion', 'red onion'],
        ]),
      ),
    )
    render(<App />)

    grab('https://recipes.example/garlic')

    await waitFor(() => expect(screen.getByDisplayValue('red onion')).toBeInTheDocument())
    expect(screen.getAllByDisplayValue('garlic')).toHaveLength(1)
    expect(screen.getAllByRole('checkbox')).toHaveLength(2)
  })

  it('merges a second recipe without duplicating shared ingredients', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        jsonResponse(
          recipe('One', [
            ['2 ripe tomatoes', 'tomatoes'],
            ['1 tbsp olive oil', 'olive oil'],
          ]),
        ),
      )
      .mockResolvedValueOnce(
        jsonResponse(
          recipe('Two', [
            ['2 tbsp Olive   Oil', 'Olive   Oil'],
            ['1 red onion', 'red onion'],
          ]),
        ),
      )
    render(<App />)

    grab('https://recipes.example/one')
    await waitFor(() => expect(screen.getByDisplayValue('tomatoes')).toBeInTheDocument())

    grab('https://recipes.example/two')
    await waitFor(() => expect(screen.getByDisplayValue('red onion')).toBeInTheDocument())

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
