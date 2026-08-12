import { apiFetch } from './client'

export function getCourses() {
  return apiFetch('/api/v1/courses')
}

export function getCourse(slug) {
  return apiFetch(`/api/v1/courses/${slug}`)
}

export function getCourseThumbnailUrl(slug) {
  return apiFetch(`/api/v1/courses/${slug}/thumbnail-url`)
}

export function getCourseWatchStatus(slug) {
  return apiFetch(`/api/v1/courses/${slug}/watch-status`)
}

export function getLessonSegment(courseSlug, lessonSlug) {
  return apiFetch(`/api/v1/courses/${courseSlug}/lessons/${lessonSlug}`)
}

export function getLessonVideoUrl(courseSlug, lessonSlug) {
  return apiFetch(`/api/v1/courses/${courseSlug}/lessons/${lessonSlug}/video-url`)
}

export function getLessonThumbnailUrl(courseSlug, lessonSlug) {
  return apiFetch(`/api/v1/courses/${courseSlug}/lessons/${lessonSlug}/thumbnail-url`)
}
