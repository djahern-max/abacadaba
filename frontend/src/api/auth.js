import { apiFetch } from './client'

export function register(email, password, displayName) {
  return apiFetch('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, display_name: displayName }),
  })
}

export function login(email, password) {
  return apiFetch('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function logout() {
  return apiFetch('/api/v1/auth/logout', { method: 'POST' })
}

export function getMe() {
  return apiFetch('/api/v1/auth/me')
}
