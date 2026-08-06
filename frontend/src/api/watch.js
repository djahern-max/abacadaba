import { apiFetch } from './client'

export function sendHeartbeat(slug, position) {
  return apiFetch(`/api/v1/lessons/${slug}/watch`, {
    method: 'POST',
    body: JSON.stringify({ position }),
  })
}

export function getWatchProgress(slug) {
  return apiFetch(`/api/v1/lessons/${slug}/watch`)
}
