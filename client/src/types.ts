export interface Ingredient {
  id: string
  text: string
  checked: boolean
}

export interface ImportResponse {
  title: string
  source_url: string
  ingredients: string[]
}

export type Notice = {
  tone: 'success' | 'error' | 'info'
  message: string
} | null
