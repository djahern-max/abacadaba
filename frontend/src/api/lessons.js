import { apiFetch } from './client'

export function getLessons() {
  return apiFetch('/api/v1/lessons')
}

export function getLesson(slug) {
  return apiFetch(`/api/v1/lessons/${slug}`)
}

export function getVideoUrl(slug) {
  return apiFetch(`/api/v1/lessons/${slug}/video-url`)
}

export function getThumbnailUrl(slug) {
  return apiFetch(`/api/v1/lessons/${slug}/thumbnail-url`)
}
