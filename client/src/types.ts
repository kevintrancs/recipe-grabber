export interface Ingredient {
  id: string
  name: string
  checked: boolean
}

/** One recipe line, plus the food it names. */
export interface ImportedIngredient {
  text: string
  name: string
}

export interface ImportResponse {
  title: string
  source_url: string
  ingredients: ImportedIngredient[]
}

export type Notice = {
  tone: 'success' | 'error' | 'info'
  message: string
} | null
