import React, { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  BookOpen,
  MessageSquare,
  HelpCircle,
  TrendingUp,
  Upload,
  Sparkles,
  Clock,
  ArrowRight,
  FileText,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import EmptyState from '../components/EmptyState'
import { useAuth } from '../contexts/AuthContext'
import { overview, progress, activity } from '../api/analytics'
import { get as getRecommendations } from '../api/recommendations'

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [progressData, setProgressData] = useState([])
  const [activityData, setActivityData] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [overviewData, progData, actData, recs] = await Promise.all([
        overview(),
        progress(),
        activity(),
        getRecommendations(),
      ])
      setStats(overviewData)
      setProgressData(progData || [])
      setActivityData(actData || [])
      setRecommendations((recs || []).slice(0, 3))
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  if (loading) return <LoadingSpinner size="lg" />

  const cards = [
    { label: 'Total Documents', value: stats?.total_documents || 0, icon: BookOpen, to: '/documents', color: 'text-blue-600 bg-blue-50' },
    { label: 'Questions Asked', value: stats?.total_conversations || 0, icon: MessageSquare, to: '/chat', color: 'text-green-600 bg-green-50' },
    { label: 'Quizzes Completed', value: stats?.total_quizzes || 0, icon: HelpCircle, to: '/quizzes', color: 'text-purple-600 bg-purple-50' },
    { label: 'Average Score', value: `${stats?.avg_score || 0}%`, icon: TrendingUp, to: '/analytics', color: 'text-orange-600 bg-orange-50' },
  ]

  const isNewUser = !stats || (stats.total_documents === 0 && stats.total_conversations === 0 && stats.total_quizzes === 0)

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Welcome Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.full_name?.split(' ')[0] || 'Student'}!
        </h1>
        <p className="text-gray-600 mt-1">Here is your learning overview for today.</p>
      </div>

      <ErrorAlert message={error} onDismiss={() => setError('')} />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map(({ label, value, icon: Icon, to, color }) => (
          <Link key={label} to={to} className="card hover:shadow-md transition-shadow">
            <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${color} mb-3`}>
              <Icon className="h-5 w-5" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-sm text-gray-600">{label}</p>
          </Link>
        ))}
      </div>

      {/* New User Empty State */}
      {isNewUser && (
        <div className="card">
          <EmptyState
            icon={Upload}
            title="Get Started with Your Learning"
            description="Upload your first study document to unlock AI-powered tutoring, smart quizzes, and personalized recommendations."
            action={
              <Link to="/documents" className="btn-primary inline-flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Upload Your First Document
              </Link>
            }
          />
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link to="/chat" className="btn-primary text-center flex items-center justify-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Ask a Question
          </Link>
          <Link to="/documents" className="btn-secondary text-center flex items-center justify-center gap-2">
            <Upload className="h-4 w-4" />
            Upload Document
          </Link>
          <Link to="/quizzes" className="btn-secondary text-center flex items-center justify-center gap-2">
            <HelpCircle className="h-4 w-4" />
            Take a Quiz
          </Link>
        </div>
      </div>

      {/* Progress Chart */}
      {progressData.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Learning Progress</h2>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={progressData}>
              <defs>
                <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey="score" stroke="#2563eb" fill="url(#colorScore)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent Activity & Recommendations */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
          {activityData.length === 0 ? (
            <p className="text-sm text-gray-500">No recent activity yet. Start learning to see your progress here.</p>
          ) : (
            <div className="space-y-3">
              {activityData.slice(0, 5).map((item, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-primary-50 flex items-center justify-center">
                      <Clock className="h-4 w-4 text-primary-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{item.activity_type || 'Study Session'}</p>
                      <p className="text-xs text-gray-500">{item.date || item.day || 'Recent'}</p>
                    </div>
                  </div>
                  <span className="text-sm text-gray-600">{item.minutes || item.count || 0} {item.minutes ? 'min' : 'items'}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recommended Materials */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recommended for You</h2>
            <Link to="/recommendations" className="text-sm text-primary-600 hover:underline flex items-center gap-1">
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          {recommendations.length === 0 ? (
            <p className="text-sm text-gray-500">No recommendations yet. Upload documents and take quizzes to get personalized suggestions.</p>
          ) : (
            <div className="space-y-3">
              {recommendations.map((rec) => (
                <Link
                  key={rec.id}
                  to="/recommendations"
                  className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="h-10 w-10 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="h-5 w-5 text-primary-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{rec.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{rec.topic || rec.subject || 'General'}</p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
