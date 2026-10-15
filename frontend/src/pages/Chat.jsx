import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Send,
  MessageSquare,
  Plus,
  Trash2,
  ThumbsUp,
  ThumbsDown,
  Bot,
  User,
  ChevronDown,
  Sparkles,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import EmptyState from '../components/EmptyState'
import {
  sendMessage,
  getConversations,
  getConversation,
  deleteConversation,
  sendFeedback,
} from '../api/chat'

const ANSWER_STYLES = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'concise', label: 'Concise' },
  { value: 'detailed', label: 'Detailed' },
  { value: 'exam_prep', label: 'Exam Prep' },
  { value: 'step_by_step', label: 'Step-by-Step' },
]

export default function Chat() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const [conversations, setConversations] = useState([])
  const [activeConversation, setActiveConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationsLoading, setConversationsLoading] = useState(true)
  const [error, setError] = useState('')
  const [answerStyle, setAnswerStyle] = useState('detailed')
  const [feedbackGiven, setFeedbackGiven] = useState({})
  const [followUpSuggestions, setFollowUpSuggestions] = useState([])
  const messagesEndRef = useRef(null)
  const chatContainerRef = useRef(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  // Fetch conversations list
  const fetchConversations = useCallback(async () => {
    try {
      const data = await getConversations()
      setConversations(data || [])
    } catch (err) {
      // Silently fail for conversations list
    } finally {
      setConversationsLoading(false)
    }
  }, [])

  // Fetch active conversation messages
  const fetchActiveConversation = useCallback(async (id) => {
    if (!id) {
      setActiveConversation(null)
      setMessages([])
      setFollowUpSuggestions([])
      return
    }
    try {
      const data = await getConversation(id)
      setActiveConversation(data)
      setMessages(data?.messages || [])
      setFollowUpSuggestions(data?.follow_up_questions || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load conversation')
    }
  }, [])

  useEffect(() => {
    fetchConversations()
  }, [fetchConversations])

  useEffect(() => {
    if (conversationId) {
      fetchActiveConversation(conversationId)
    } else {
      setActiveConversation(null)
      setMessages([])
      setFollowUpSuggestions([])
    }
  }, [conversationId, fetchActiveConversation])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const handleSend = async (e) => {
    e?.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = { role: 'user', content: input.trim() }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError('')
    setFollowUpSuggestions([])

    try {
      const response = await sendMessage(input.trim(), activeConversation?.id || null)
      const assistantMessage = {
        role: 'assistant',
        content: response?.answer || response?.message || response?.content || 'No response received',
        sources: response?.sources || response?.citations || [],
        follow_up_questions: response?.follow_up_questions || [],
        id: response?.message_id || response?.id,
      }
      setMessages((prev) => [...prev, assistantMessage])
      setFollowUpSuggestions(assistantMessage.follow_up_questions)

      // If this was a new conversation, update the URL
      if (!activeConversation && response?.conversation_id) {
        navigate(`/chat/${response.conversation_id}`, { replace: true })
      }

      // Refresh conversations list
      fetchConversations()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send message')
    } finally {
      setLoading(false)
    }
  }

  const handleNewConversation = () => {
    navigate('/chat')
    setActiveConversation(null)
    setMessages([])
    setFollowUpSuggestions([])
  }

  const handleDeleteConversation = async (id) => {
    try {
      await deleteConversation(id)
      setConversations((prev) => prev.filter((c) => c.id !== id))
      if (activeConversation?.id === id) {
        handleNewConversation()
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete conversation')
    }
  }

  const handleFeedback = async (messageId, feedback) => {
    try {
      await sendFeedback(messageId, feedback)
      setFeedbackGiven((prev) => ({ ...prev, [messageId]: feedback }))
    } catch (err) {
      // Silently fail for feedback
    }
  }

  const handleFollowUpClick = (question) => {
    setInput(question)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="max-w-7xl mx-auto h-[calc(100vh-8rem)] flex gap-4">
      {/* Conversation Sidebar */}
      <div className="hidden md:flex flex-col w-72 bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={handleNewConversation}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {conversationsLoading ? (
            <div className="p-4"><LoadingSpinner size="sm" /></div>
          ) : conversations.length === 0 ? (
            <p className="p-4 text-sm text-gray-500 text-center">No conversations yet</p>
          ) : (
            <div className="p-2 space-y-1">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                    activeConversation?.id === conv.id
                      ? 'bg-primary-50 text-primary-700'
                      : 'hover:bg-gray-50 text-gray-700'
                  }`}
                  onClick={() => navigate(`/chat/${conv.id}`)}
                >
                  <MessageSquare className="h-4 w-4 flex-shrink-0" />
                  <span className="flex-1 text-sm truncate">{conv.title || 'Untitled Chat'}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteConversation(conv.id)
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-opacity"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <MessageSquare className="h-6 w-6 text-primary-600" />
            <h1 className="text-2xl font-bold text-gray-900">AI Tutor</h1>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 hidden sm:inline">Answer style:</label>
            <div className="relative">
              <select
                value={answerStyle}
                onChange={(e) => setAnswerStyle(e.target.value)}
                className="input py-1.5 pr-8 text-sm appearance-none"
              >
                {ANSWER_STYLES.map((style) => (
                  <option key={style.value} value={style.value}>
                    {style.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
            </div>
          </div>
        </div>

        <ErrorAlert message={error} onDismiss={() => setError('')} />

        {/* Messages Area */}
        <div
          ref={chatContainerRef}
          className="card flex-1 overflow-y-auto mb-4 space-y-6"
        >
          {messages.length === 0 ? (
            <EmptyState
              icon={Bot}
              title="Ask Your AI Tutor"
              description="Upload documents first, then ask questions about your study materials. The AI tutor will provide answers with citations from your documents."
              action={
                <div className="flex flex-wrap gap-2 justify-center mt-2">
                  {['What is the main topic of my document?', 'Explain a key concept', 'Help me study for my exam'].map((q) => (
                    <button
                      key={q}
                      onClick={() => setInput(q)}
                      className="px-3 py-1.5 text-sm bg-primary-50 text-primary-700 rounded-full hover:bg-primary-100 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              }
            />
          ) : (
            <>
              {messages.map((msg, i) => (
                <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'assistant' && (
                    <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4 text-primary-600" />
                    </div>
                  )}
                  <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-first' : ''}`}>
                    <div
                      className={`rounded-lg px-4 py-3 ${
                        msg.role === 'user'
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      {msg.role === 'assistant' ? (
                        <div className="prose prose-sm max-w-none prose-gray">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      )}
                    </div>

                    {/* Source Citations */}
                    {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {msg.sources.map((source, j) => (
                          <div
                            key={j}
                            className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-100 rounded-lg"
                          >
                            <Sparkles className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-medium text-blue-800">
                                {source.document_title || source.title || 'Source Document'}
                                {source.page && ` — Page ${source.page}`}
                              </p>
                              <p className="text-xs text-blue-600 mt-0.5 line-clamp-2">
                                {source.excerpt || source.text || source.content || ''}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Feedback Buttons */}
                    {msg.role === 'assistant' && msg.id && (
                      <div className="flex items-center gap-1 mt-2">
                        <button
                          onClick={() => handleFeedback(msg.id, 'positive')}
                          className={`p-1.5 rounded transition-colors ${
                            feedbackGiven[msg.id] === 'positive'
                              ? 'text-green-600 bg-green-50'
                              : 'text-gray-400 hover:text-green-600 hover:bg-green-50'
                          }`}
                          title="Helpful"
                        >
                          <ThumbsUp className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleFeedback(msg.id, 'negative')}
                          className={`p-1.5 rounded transition-colors ${
                            feedbackGiven[msg.id] === 'negative'
                              ? 'text-red-600 bg-red-50'
                              : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
                          }`}
                          title="Not helpful"
                        >
                          <ThumbsDown className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4 text-white" />
                    </div>
                  )}
                </div>
              ))}

              {/* Loading Indicator */}
              {loading && (
                <div className="flex gap-3">
                  <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
                    <Bot className="h-4 w-4 text-primary-600" />
                  </div>
                  <div className="bg-gray-100 rounded-lg px-4 py-3">
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <LoadingSpinner size="sm" />
                      AI Tutor is thinking...
                    </div>
                  </div>
                </div>
              )}

              {/* Follow-up Suggestions */}
              {followUpSuggestions.length > 0 && !loading && (
                <div className="flex flex-wrap gap-2 pl-11">
                  {followUpSuggestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => handleFollowUpClick(q)}
                      className="px-3 py-1.5 text-sm bg-primary-50 text-primary-700 rounded-full hover:bg-primary-100 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Message Input */}
        <form onSubmit={handleSend} className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your question..."
            className="input flex-1 resize-none"
            rows={1}
            disabled={loading}
          />
          <button
            type="submit"
            className="btn-primary px-4 flex items-center gap-2"
            disabled={loading || !input.trim()}
          >
            <Send className="h-4 w-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </form>
      </div>
    </div>
  )
}
