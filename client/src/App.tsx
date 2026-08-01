import { useState } from 'react'
import type { FormEvent } from 'react'

import { importRecipe } from './api'
import type { ImportResponse, Ingredient, Notice } from './types'

function makeIngredient(name: string): Ingredient {
  const id = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`
  return { id, name, checked: false }
}

function normalizeText(value: string): string {
  return value.trim().replace(/\s+/g, ' ')
}

function looksLikeUrl(value: string): boolean {
  const candidate = value.toLowerCase()
  return candidate.startsWith('http://') || candidate.startsWith('https://') || candidate.startsWith('www.')
}

export default function App() {
  const [entry, setEntry] = useState('')
  const [ingredients, setIngredients] = useState<Ingredient[]>([])
  const [recipe, setRecipe] = useState<ImportResponse | null>(null)
  const [notice, setNotice] = useState<Notice>(null)
  const [isImporting, setIsImporting] = useState(false)

  const remainingCount = ingredients.filter((ingredient) => !ingredient.checked).length

  // Merge on the food name, so "10 cloves garlic, minced" and "3 cloves roasted garlic"
  // both land on one "garlic" row.
  function mergeIngredients(names: string[]) {
    setIngredients((current) => {
      const seen = new Set(current.map((item) => normalizeText(item.name).toLocaleLowerCase()))
      const additions: Ingredient[] = []
      for (const rawName of names) {
        const name = normalizeText(rawName)
        const key = name.toLocaleLowerCase()
        if (name && !seen.has(key)) {
          seen.add(key)
          additions.push(makeIngredient(name))
        }
      }
      return [...current, ...additions]
    })
  }

  async function handleAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = normalizeText(entry)
    if (!value) {
      setNotice({ tone: 'error', message: 'Enter a recipe URL or grocery item.' })
      return
    }

    if (!looksLikeUrl(value)) {
      mergeIngredients([value])
      setEntry('')
      setNotice({ tone: 'success', message: `Added “${value}”.` })
      return
    }

    setIsImporting(true)
    setNotice({ tone: 'info', message: 'Reading the recipe page…' })
    try {
      const response = await importRecipe(value)
      const count = response.ingredients.length
      mergeIngredients(response.ingredients.map((item) => item.name))
      setRecipe(response)
      setEntry('')
      setNotice({
        tone: 'success',
        message: `Imported ${count} ingredient${count === 1 ? '' : 's'}.`,
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Something went wrong. Try again.'
      setNotice({ tone: 'error', message })
    } finally {
      setIsImporting(false)
    }
  }

  function updateIngredient(id: string, name: string) {
    setIngredients((current) =>
      current.map((ingredient) => (ingredient.id === id ? { ...ingredient, name } : ingredient)),
    )
  }

  function toggleIngredient(id: string) {
    setIngredients((current) =>
      current.map((ingredient) =>
        ingredient.id === id ? { ...ingredient, checked: !ingredient.checked } : ingredient,
      ),
    )
  }

  function removeIngredient(id: string) {
    setIngredients((current) => current.filter((ingredient) => ingredient.id !== id))
  }

  function listText(): string {
    return ingredients.map((ingredient) => `• ${normalizeText(ingredient.name)}`).join('\n')
  }

  async function copyList() {
    try {
      await navigator.clipboard.writeText(listText())
      setNotice({ tone: 'success', message: 'Ingredient list copied.' })
    } catch {
      setNotice({ tone: 'error', message: 'Your browser could not copy the list.' })
    }
  }

  async function shareList() {
    if (!navigator.share) {
      await copyList()
      return
    }
    try {
      await navigator.share({ title: recipe?.title ?? 'Recipe ingredients', text: listText() })
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return
      setNotice({ tone: 'error', message: 'The list could not be shared.' })
    }
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="/" aria-label="Recipe Grabber home">
          <span className="brand-mark" aria-hidden="true">RG</span>
          <span>Recipe Grabber</span>
        </a>
      </header>

      <main>
        <section className="hero" aria-labelledby="hero-title">
          <p className="eyebrow">Recipe to grocery list</p>
          <h1 id="hero-title">Pls cook more<br />Easily fetch ingredients</h1>
          <p className="hero-copy">
            Paste a recipe link and get a list of ingredients. Or just add your own, but don't do that.
          </p>

          <form className="grabber-form" onSubmit={handleAdd}>
            <label htmlFor="recipe-entry">Recipe URL or grocery item</label>
            <div className="input-action">
              <input
                id="recipe-entry"
                type="text"
                value={entry}
                onChange={(event) => setEntry(event.target.value)}
                placeholder="https://… or avocados"
                autoComplete="off"
                disabled={isImporting}
              />
              <button className="primary-button" type="submit" disabled={isImporting}>
                {isImporting ? 'Grabbing…' : 'Grab ingredients'}
              </button>
            </div>
          </form>
        </section>

        {notice && (
          <div className={`notice notice-${notice.tone}`} role="status" aria-live="polite">
            <span>{notice.message}</span>
            <button type="button" onClick={() => setNotice(null)} aria-label="Dismiss message">×</button>
          </div>
        )}

        <section className="workspace" aria-label="Ingredient workspace">
          <div className="list-card">
            <div className="card-heading">
              <div>
                <p className="eyebrow">Your list</p>
                <h2>{recipe?.title ?? 'Ingredients'}</h2>
                {recipe && (
                  <a href={recipe.source_url} target="_blank" rel="noreferrer">View original recipe ↗</a>
                )}
              </div>
              <div className="count-badge" aria-label={`${remainingCount} items remaining`}>
                <strong>{remainingCount}</strong>
                <span>to get</span>
              </div>
            </div>

            {ingredients.length === 0 ? (
              <div className="empty-state">
                <div className="empty-illustration" aria-hidden="true">🥕</div>
                <h3>Your add is $0</h3>
                <p>Paste a recipe above or add your first grocery item.</p>
              </div>
            ) : (
              <>
                <ul className="ingredient-list">
                  {ingredients.map((ingredient) => (
                    <li key={ingredient.id} className={ingredient.checked ? 'is-checked' : undefined}>
                      <input
                        className="check-input"
                        type="checkbox"
                        checked={ingredient.checked}
                        onChange={() => toggleIngredient(ingredient.id)}
                        aria-label={`Mark ${ingredient.name} as ${ingredient.checked ? 'needed' : 'collected'}`}
                      />
                      <input
                        className="ingredient-input"
                        value={ingredient.name}
                        onChange={(event) => updateIngredient(ingredient.id, event.target.value)}
                        aria-label={`Edit ${ingredient.name}`}
                      />
                      <button
                        className="icon-button"
                        type="button"
                        onClick={() => removeIngredient(ingredient.id)}
                        aria-label={`Remove ${ingredient.name}`}
                      >
                        ×
                      </button>
                    </li>
                  ))}
                </ul>
                <div className="list-actions">
                  <button type="button" className="text-button" onClick={() => setIngredients((items) => items.filter((item) => !item.checked))}>
                    Clear checked
                  </button>
                  <button type="button" className="text-button danger" onClick={() => { setIngredients([]); setRecipe(null) }}>
                    Clear list
                  </button>
                </div>
              </>
            )}
          </div>

          <aside className="share-card">
            <p className="eyebrow">Take it with you</p>
            <h2>Share your list</h2>
            <p>Copy it, or hand it to your phone’s share sheet to text, message, or mail it.</p>

            <div className="share-actions">
              <button type="button" className="secondary-button" onClick={copyList} disabled={!ingredients.length}>
                Copy list
              </button>
              <button type="button" className="secondary-button" onClick={shareList} disabled={!ingredients.length}>
                Share…
              </button>
            </div>

            <p className="privacy-note">No account required. Your list stays in this browser.</p>
          </aside>
        </section>
      </main>

      <footer>
        <span>Built for less scrolling and fewer forgotten onions.</span>
        <a href="/api/health">API status</a>
      </footer>
    </div>
  )
}
