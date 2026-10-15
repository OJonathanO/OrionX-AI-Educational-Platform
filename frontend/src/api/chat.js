import client from './client'

export const sendMessage = async (message, conversationId = null) => {
  const res = await client.post('/chat', { message, conversation_id: conversationId })
  return res.data
}

export const getConversations = async () => {
  const res = await client.get('/chat/conversations')
  return res.data
}

export const getConversation = async (id) => {
  const res = await client.get(`/chat/conversations/${id}`)
  return res.data
}

export const deleteConversation = async (id) => {
  const res = await client.delete(`/chat/conversations/${id}`)
  return res.data
}

export const sendFeedback = async (messageId, feedback) => {
  const res = await client.post(`/chat/${messageId}/feedback`, { feedback })
  return res.data
}
