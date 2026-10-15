import client from './client'

export const register = async (email, password, fullName) => {
  const res = await client.post('/auth/register', { email, password, full_name: fullName })
  return res.data
}

export const login = async (email, password) => {
  const res = await client.post('/auth/login', { email, password })
  return res.data
}

export const getMe = async () => {
  const res = await client.get('/users/me')
  return res.data
}

export const updateMe = async (data) => {
  const res = await client.put('/users/me', data)
  return res.data
}

export const getPreferences = async () => {
  const res = await client.get('/users/me/preferences')
  return res.data
}

export const updatePreferences = async (data) => {
  const res = await client.put('/users/me/preferences', data)
  return res.data
}
