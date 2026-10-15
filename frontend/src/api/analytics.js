import client from './client'

export const overview = async () => {
  const res = await client.get('/analytics/overview')
  return res.data
}

export const progress = async () => {
  const res = await client.get('/analytics/progress')
  return res.data
}

export const topics = async () => {
  const res = await client.get('/analytics/topics')
  return res.data
}

export const activity = async () => {
  const res = await client.get('/analytics/activity')
  return res.data
}
