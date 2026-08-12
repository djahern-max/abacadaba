import { apiFetch } from './client'

export function sendHeartbeat(courseSlug, lessonSlug, position) {
  return apiFetch(`/api/v1/courses/${courseSlug}/lessons/${lessonSlug}/watch`, {
    method: 'POST',
    body: JSON.stringify({ position }),
  })
}

export function getWatchProgress(courseSlug, lessonSlug) {
  return apiFetch(`/api/v1/courses/${courseSlug}/lessons/${lessonSlug}/watch`)
}
