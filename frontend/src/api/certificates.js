import { apiFetch } from './client'

const BASE_URL = import.meta.env.VITE_API_URL

export function claimCertificate(attemptId, name) {
  return apiFetch(`/api/v1/attempts/${attemptId}/certificate`, {
    method: 'POST',
    body: JSON.stringify(name ? { recipient_name: name } : {}),
  })
}

export function certificatePdfUrl(attemptId) {
  return `${BASE_URL}/api/v1/attempts/${attemptId}/certificate.pdf`
}

export function verifyCertificate(code) {
  return apiFetch(`/api/v1/certificates/${encodeURIComponent(code)}`)
}
