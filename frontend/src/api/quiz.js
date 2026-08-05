import { apiFetch } from './client'

export function getQuiz(slug) {
  return apiFetch(`/api/v1/lessons/${slug}/quiz`)
}
