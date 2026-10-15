import React from 'react'
import { Link } from 'react-router-dom'
import {
  GraduationCap,
  BookOpen,
  Brain,
  Target,
  TrendingUp,
  FileUp,
  MessageSquare,
  Sparkles,
  ArrowRight,
  Upload,
  HelpCircle,
  Lightbulb,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const features = [
  {
    icon: BookOpen,
    title: 'RAG-Powered Learning',
    description: 'Upload your study materials and get AI-powered answers grounded in your own documents with full citations.',
  },
  {
    icon: Brain,
    title: 'AI Tutor with Citations',
    description: 'Chat with an intelligent tutor that explains concepts step-by-step and cites exact sources from your materials.',
  },
  {
    icon: HelpCircle,
    title: 'Smart Quizzes',
    description: 'Auto-generated quizzes tailored to your documents and difficulty level. Track your progress over time.',
  },
  {
    icon: Lightbulb,
    title: 'Personalized Recommendations',
    description: 'Get study recommendations based on your learning patterns, quiz performance, and interests.',
  },
  {
    icon: TrendingUp,
    title: 'Progress Tracking',
    description: 'Visualize your learning journey with detailed analytics, topic mastery, and performance insights.',
  },
  {
    icon: FileUp,
    title: 'Document Upload',
    description: 'Support for PDF, Word, and text files. Your documents are processed and indexed for instant retrieval.',
  },
]

const steps = [
  {
    icon: Upload,
    step: '1',
    title: 'Upload',
    description: 'Upload your study materials — textbooks, notes, or any documents you are learning from.',
  },
  {
    icon: MessageSquare,
    step: '2',
    title: 'Ask',
    description: 'Ask questions in natural language. Our AI tutor provides answers with citations from your documents.',
  },
  {
    icon: Sparkles,
    step: '3',
    title: 'Learn',
    description: 'Take quizzes, track your progress, and get personalized recommendations to master every topic.',
  },
]

export default function Landing() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="px-6 py-4 flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <GraduationCap className="h-8 w-8 text-primary-600" />
          <span className="text-xl font-bold text-gray-900">OrionX : AI Educational Platform</span>
        </div>
        <div className="flex items-center gap-3">
          {user ? (
            <Link to="/dashboard" className="btn-primary">
              Go to Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="btn-secondary">
                Sign In
              </Link>
              <Link to="/register" className="btn-primary">
                Get Started
              </Link>
            </>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-indigo-800">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djItSDI0di0yaDEyek0zNiAyNHYySDI0di0yaDEyeiIvPjwvZz48L2c+PC9zdmc+')] opacity-30" />
        <div className="relative max-w-7xl mx-auto px-6 py-24 lg:py-32 text-center">
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white/90 text-sm font-medium px-4 py-2 rounded-full mb-8">
            <Sparkles className="h-4 w-4" />
            AI-Powered Learning Platform
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
            Learn Smarter with
            <br />
            <span className="text-primary-200">AI-Powered Education</span>
          </h1>
          <p className="text-lg sm:text-xl text-primary-100 max-w-2xl mx-auto mb-10">
            Your personal AI tutor that understands your study materials, generates smart quizzes,
            and adapts to your learning style — all in one platform.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {user ? (
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 bg-white text-primary-700 px-8 py-3 rounded-lg font-semibold hover:bg-primary-50 transition-colors shadow-lg"
              >
                Go to Dashboard
                <ArrowRight className="h-5 w-5" />
              </Link>
            ) : (
              <>
                <Link
                  to="/register"
                  className="inline-flex items-center gap-2 bg-white text-primary-700 px-8 py-3 rounded-lg font-semibold hover:bg-primary-50 transition-colors shadow-lg"
                >
                  Start Learning Free
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white border border-white/30 px-8 py-3 rounded-lg font-semibold hover:bg-white/20 transition-colors"
                >
                  Sign In
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Everything You Need to Excel
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            A complete AI-powered learning ecosystem designed to help you study more effectively and achieve your goals.
          </p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="card hover:shadow-lg hover:border-primary-200 transition-all duration-200 group"
            >
              <div className="h-12 w-12 rounded-lg bg-primary-50 flex items-center justify-center mb-4 group-hover:bg-primary-100 transition-colors">
                <Icon className="h-6 w-6 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
              <p className="text-sm text-gray-600 leading-relaxed">{description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works Section */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Get started in three simple steps and transform the way you learn.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {steps.map(({ icon: Icon, step, title, description }) => (
              <div key={step} className="relative text-center">
                <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-primary-600 text-white mb-6">
                  <Icon className="h-8 w-8" />
                </div>
                <div className="absolute top-8 left-1/2 -translate-x-1/2 -z-10 hidden md:block">
                  <span className="text-6xl font-bold text-primary-100">{step}</span>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">{title}</h3>
                <p className="text-gray-600 max-w-xs mx-auto">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="bg-gradient-to-r from-primary-600 to-indigo-700 rounded-2xl p-12 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Ready to Transform Your Learning?
          </h2>
          <p className="text-lg text-primary-100 mb-8 max-w-xl mx-auto">
            Join thousands of students who are already learning smarter with AI-powered tools.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {user ? (
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 bg-white text-primary-700 px-8 py-3 rounded-lg font-semibold hover:bg-primary-50 transition-colors"
              >
                Go to Dashboard
                <ArrowRight className="h-5 w-5" />
              </Link>
            ) : (
              <>
                <Link
                  to="/register"
                  className="inline-flex items-center gap-2 bg-white text-primary-700 px-8 py-3 rounded-lg font-semibold hover:bg-primary-50 transition-colors"
                >
                  Create Free Account
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-2 text-white border border-white/40 px-8 py-3 rounded-lg font-semibold hover:bg-white/10 transition-colors"
                >
                  Sign In
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <GraduationCap className="h-6 w-6 text-primary-600" />
            <span className="font-semibold text-gray-900">OrionX : AI Educational Platform</span>
          </div>
          <p className="text-sm text-gray-500">
            &copy; {new Date().getFullYear()} OrionX : AI Educational Platform. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}
