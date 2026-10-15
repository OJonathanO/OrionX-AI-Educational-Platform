import React, { useState, useEffect, useCallback } from 'react'
import {
  BarChart3,
  TrendingUp,
  BookOpen,
  HelpCircle,
  Target,
  Calendar,
  Award,
  AlertTriangle,
} from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import EmptyState from '../components/EmptyState'
import { overview, progress, topics, activity } from '../api/analytics'

const TIME_PERIODS = [
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
  { value: '90d', label: 'Last 90 Days' },
  { value: 'all', label: 'All Time' },
]

export default function Analytics() {
  const [period, setPeriod] = useState('30d')
  const [overviewData, setOverviewData] = useState(null)
  const [progressData, setProgressData] = useState([])
  const [topicsData, setTopicsData] = useState([])
  const [activityData, setActivityData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [ovData, progData, topData, actData] = await Promise.all([
        overview(),
        progress(),
        topics(),
        activity(),
      ])
      setOverviewData(ovData)
      setProgressData(progData || [])
      setTopicsData(topData || [])
      setActivityData(actData || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  if (loading) return <LoadingSpinner size="lg" />

  // Calculate weak topics (sorted by lowest avg score)
  const weakTopics = [...topicsData]
    .sort((a, b) => (a.avg_score || 0) - (b.avg_score || 0))
    .slice(0, 5)

  // Calculate topic mastery
  const topicMastery = [...topicsData]
    .sort((a, b) => (b.avg_score || 0) - (a.avg_score || 0))

  const statsCards = [
    { label: 'Total Study Time', value: `${overviewData?.total_study_time || 0}h`, icon: Calendar, color: 'text-blue-600 bg-blue-50' },
    { label: 'Quizzes Taken', value: overviewData?.total_quizzes || 0, icon: HelpCircle, color: 'text-purple-600 bg-purple-50' },
    { label: 'Average Score', value: `${overviewData?.avg_score || 0}%`, icon: Target, color: 'text-green-600 bg-green-50' },
    { label: 'Topics Mastered', value: overviewData?.topics_mastered || 0, icon: Award, color: 'text-orange-600 bg-orange-50' },
  ]

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BarChart3 className="h-8 w-8 text-primary-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
            <p className="text-gray-600 mt-0.5">Track your learning progress and performance</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600 hidden sm:inline">Period:</label>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="input py-1.5 text-sm w-auto"
          >
            {TIME_PERIODS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>
      </div>

      <ErrorAlert message={error} onDismiss={() => setError('')} />

      {/* Overview Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsCards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card">
            <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${color} mb-3`}>
              <Icon className="h-5 w-5" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-sm text-gray-600">{label}</p>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Quiz Performance Over Time */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary-600" />
            Quiz Performance Over Time
          </h2>
          {progressData.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No quiz data available yet. Take some quizzes to see your progress.</p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={progressData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="score" stroke="#2563eb" strokeWidth={2} name="Score %" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Subject-Level Performance */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary-600" />
            Subject Performance
          </h2>
          {topicsData.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No subject data available yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={topicsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="topic" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="avg_score" fill="#3b82f6" name="Avg Score %" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Activity Chart */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Calendar className="h-5 w-5 text-primary-600" />
          Daily Activity
        </h2>
        {activityData.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">No activity data available yet.</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={activityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="minutes" fill="#2563eb" name="Study Minutes" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Weak Topics & Topic Mastery */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Weak Topics */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
            Topics Needing Attention
          </h2>
          {weakTopics.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No topic data available yet.</p>
          ) : (
            <div className="space-y-3">
              {weakTopics.map((topic) => (
                <div key={topic.topic} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">{topic.topic}</span>
                      <span className={`text-sm font-medium ${
                        (topic.avg_score || 0) >= 70 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {topic.avg_score || 0}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          (topic.avg_score || 0) >= 70 ? 'bg-green-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${topic.avg_score || 0}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Topic Mastery */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Award className="h-5 w-5 text-primary-600" />
            Topic Mastery
          </h2>
          {topicMastery.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No topic data available yet.</p>
          ) : (
            <div className="space-y-3">
              {topicMastery.map((topic) => {
                const score = topic.avg_score || 0
                const masteryLevel = score >= 80 ? 'Mastered' : score >= 60 ? 'Proficient' : score >= 40 ? 'Learning' : 'Needs Work'
                return (
                  <div key={topic.topic}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">{topic.topic}</span>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        score >= 80 ? 'bg-green-100 text-green-700' :
                        score >= 60 ? 'bg-blue-100 text-blue-700' :
                        score >= 40 ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {masteryLevel}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          score >= 80 ? 'bg-green-500' :
                          score >= 60 ? 'bg-blue-500' :
                          score >= 40 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${score}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
