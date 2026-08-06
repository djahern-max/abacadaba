import { apiFetch } from './client'

const BASE_URL = import.meta.env.VITE_API_URL

export function getAdminLessons() {
  return apiFetch('/api/v1/admin/lessons')
}

export function getAdminLesson(id) {
  return apiFetch(`/api/v1/admin/lessons/${id}`)
}

export function getLessonStats(id) {
  return apiFetch(`/api/v1/admin/lessons/${id}/stats`)
}

export function createAdminLesson(payload) {
  return apiFetch('/api/v1/admin/lessons', { method: 'POST', body: JSON.stringify(payload) })
}

export function updateAdminLesson(id, payload) {
  return apiFetch(`/api/v1/admin/lessons/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export function deleteAdminLesson(id) {
  return apiFetch(`/api/v1/admin/lessons/${id}`, { method: 'DELETE' })
}

export function publishAdminLesson(id) {
  return apiFetch(`/api/v1/admin/lessons/${id}/publish`, { method: 'POST' })
}

export function unpublishAdminLesson(id) {
  return apiFetch(`/api/v1/admin/lessons/${id}/unpublish`, { method: 'POST' })
}

export function createAdminQuestion(lessonId, prompt) {
  return apiFetch(`/api/v1/admin/lessons/${lessonId}/questions`, {
    method: 'POST',
    body: JSON.stringify({ prompt }),
  })
}

export function updateAdminQuestion(id, prompt) {
  return apiFetch(`/api/v1/admin/questions/${id}`, { method: 'PATCH', body: JSON.stringify({ prompt }) })
}

export function deleteAdminQuestion(id) {
  return apiFetch(`/api/v1/admin/questions/${id}`, { method: 'DELETE' })
}

export function moveAdminQuestion(id, direction) {
  return apiFetch(`/api/v1/admin/questions/${id}/move`, {
    method: 'POST',
    body: JSON.stringify({ direction }),
  })
}

export function createAdminChoice(questionId, text) {
  return apiFetch(`/api/v1/admin/questions/${questionId}/choices`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  })
}

export function updateAdminChoice(id, text) {
  return apiFetch(`/api/v1/admin/choices/${id}`, { method: 'PATCH', body: JSON.stringify({ text }) })
}

export function deleteAdminChoice(id) {
  return apiFetch(`/api/v1/admin/choices/${id}`, { method: 'DELETE' })
}

export function moveAdminChoice(id, direction) {
  return apiFetch(`/api/v1/admin/choices/${id}/move`, {
    method: 'POST',
    body: JSON.stringify({ direction }),
  })
}

export function setCorrectChoice(questionId, choiceId) {
  return apiFetch(`/api/v1/admin/questions/${questionId}/correct-choice`, {
    method: 'POST',
    body: JSON.stringify({ choice_id: choiceId }),
  })
}

export function uploadAdminVideo(slug, file, onProgress) {
  return new Promise((resolve, reject) => {
    const formData = new FormData()
    formData.append('file', file)

    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${BASE_URL}/api/v1/admin/lessons/${slug}/video`)
    xhr.withCredentials = true

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100))
      }
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText))
      } else {
        const error = new Error(`Upload failed: ${xhr.status}`)
        error.status = xhr.status
        reject(error)
      }
    }
    xhr.onerror = () => reject(new Error('Upload failed'))
    xhr.send(formData)
  })
}
