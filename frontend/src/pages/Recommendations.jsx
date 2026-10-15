import React, { useState, useEffect, useCallback } from 'react'
import {
  Lightbulb,
  RefreshCw,
  Bookmark,
  X,
  Undo2,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import EmptyState from '../components/EmptyState'
import { get, refresh, bookmark, unbookmark } from '../api/recommendations'

export default function Recommendations() {
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refreshing, setRefreshing] = useState(false)
  const [dismissed, setDismissed] = useState([])
  const [showUndo, setShowUndo] = useState(false)
  const [lastDismissed, setLastDismissed] = useState(null)
  const [activeTopic, setActiveTopic] = useState('')

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const data = await get()
      setRecommendations(data || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load recommendations')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleRefresh = async () => {
    setRefreshing(true)
    setError('')
    try {
      const data = await refresh()
      setRecommendations(data || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to refresh recommendations')
    } finally {
      setRefreshing(false)
    }
  }

  const handleBookmark = async (id, isBookmarked) => {
    try {
      if (isBookmarked) await unbookmark(id)
      else await bookmark(id)
      setRecommendations((prev) =>
        prev.map((r) => (r.id === id ? { ...r, bookmarked: !isBookmarked } : r))
      )
    } catch (err) {
      setError(err.response?.data?.detail || 'Action failed')
    }
  }

  const handleDismiss = (id) => {
    const rec = recommendations.find((r) => r.id === id)
    setLastDismissed(rec)
    setRecommendations((prev) => prev.filter((r) => r.id !== id))
    setDismissed((prev) => [...prev, id])
    setShowUndo(true)
    setTimeout(() => setShowUndo(false), 5000)
  }

  const handleUndo = () => {
    if (lastDismissed) {
      setRecommendations((prev) => [lastDismissed, ...prev])
      setDismissed((prev) => prev.filter((id) => id !== lastDismissed.id))
      setLastDismissed(null)
      setShowUndo(false)
    }
  }

  // Get unique topics
  const topics = [...new Set(recommendations.map((r) => r.topic || r.subject).filter(Boolean))]

  // Filter by topic
  const filtered = activeTopic
    ? recommendations.filter((r) => (r.topic || r.subject) === activeTopic)
    : recommendations

  if (loading) return <LoadingSpinner size="lg" />

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Recommendations</h1>
          <p className="text-gray-600 mt-1">Personalized learning suggestions for you</p>
        </div>
        <button onClick={handleRefresh} className="btn-secondary flex items-center gap-2" disabled={refreshing}>
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <ErrorAlert message={error} onDismiss={() => setError('')} />

      {/* Undo Toast */}
      {showUndo && (
        <div className="flex items-center justify-between p-3 bg-gray-900 text-white rounded-lg">
          <span className="text-sm">Recommendation dismissed</span>
          <button onClick={handleUndo} className="flex items-center gap-1 text-sm text-primary-300 hover:text-primary-200">
            <Undo2 className="h-4 w-4" />
            Undo
          </button>
        </div>
      )}

      {/* Topic Filter Tabs */}
      {topics.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActiveTopic('')}
            className={`px-3 py-1.5 text-sm font-medium rounded-full transition-colors ${
              !activeTopic
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            All Topics
          </button>
          {topics.map((topic) => (
            <button
              key={topic}
              onClick={() => setActiveTopic(topic)}
              className={`px-3 py-1.5 text-sm font-medium rounded-full transition-colors ${
                activeTopic === topic
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {topic}
            </button>
          ))}
        </div>
      )}

      {/* Recommendations Grid */}
      {recommendations.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={Lightbulb}
            title="No recommendations yet"
            description="Start learning! Upload documents, ask questions, and take quizzes to get personalized study recommendations."
          />
        </div>
      ) : filtered.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={Lightbulb}
            title="No recommendations for this topic"
            description="Try selecting a different topic or refresh to get new recommendations."
          />
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((rec) => (
            <div key={rec.id} className="card relative group">
              {/* Dismiss Button */}
              <button
                onClick={() => handleDismiss(rec.id)}
                className="absolute top-3 right-3 p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                title="Dismiss"
              >
                <X className="h-4 w-4" />
              </button>

              {/* Bookmark Button */}
              <button
                onClick={() => handleBookmark(rec.id, rec.bookmarked)}
                className={`absolute top-3 right-10 p-1 transition-colors ${
                  rec.bookmarked ? 'text-primary-600' : 'text-gray-400 hover:text-primary-600'
                }`}
                title={rec.bookmarked ? 'Remove bookmark' : 'Bookmark'}
              >
                <Bookmark className="h-4 w-4" fill={rec.bookmarked ? 'currentColor' : 'none'} />
              </button>

              <div className="flex items-start gap-3 mb-3">
                <div className="h-10 w-10 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0">
                  <Sparkles className="h-5 w-5 text-primary-600" />
                </div>
                <div className="flex-1 min-w-0 pr-16">
                  <h3 className="font-semibold text-gray-900 truncate">{rec.title}</h3>
                  {(rec.topic || rec.subject) && (
                    <span className="inline-block mt-1 px-2 py-0.5 text-xs font-medium bg-primary-50 text-primary-700 rounded">
                      {rec.topic || rec.subject}
                    </span>
                  )}
                </div>
              </div>

              <p className="text-sm text-gray-600 mb-3 line-clamp-3">{rec.description}</p>

              {/* Relevance Score */}
              {rec.relevance_score !== undefined && (
                <div className="mb-3">
                  <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                    <span>Relevance</span>
                    <span>{Math.round(rec.relevance_score * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-primary-600 h-1.5 rounded-full"
                      style={{ width: `${rec.relevance_score * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Reason */}
              {rec.reason && (
                <div className="flex items-start gap-2 p-2 bg-gray-50 rounded-lg">
                  <TrendingUp className="h-3.5 w-3.5 text-gray-400 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-gray-500">{rec.reason}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
