'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { useMovie } from '@/contexts/MovieContext'
import Navbar from '@/components/Navbar'
import MovieWizard from '@/components/MovieWizard'
import MovieGrid from '@/components/MovieGrid'
import CreditsDisplay from '@/components/CreditsDisplay'
import { Film, Sparkles, Zap, Brain, Camera, Wand2 } from 'lucide-react'

export default function Dashboard() {
  const { user, logout } = useAuth()
  const { movies, setMovies } = useMovie()
  const [showWizard, setShowWizard] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMovies()
  }, [])

  const fetchMovies = async () => {
    try {
      const token = localStorage.getItem('token')
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      const response = await fetch(`${API_BASE}/movies/`, {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setMovies(data)
      }
    } catch (error) {
      console.error('Failed to fetch movies:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen relative">
      <Navbar />

      <main className="container mx-auto px-4 py-8 relative">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12"
        >
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="mx-auto w-24 h-24 glass-card flex items-center justify-center mb-6 neon-glow"
          >
            <Film className="w-12 h-12 text-purple-400" />
          </motion.div>

          <h1 className="text-6xl font-bold mb-4">
            <span className="text-gradient">Cineo AI</span>
          </h1>

          <p className="text-xl text-white/80 mb-8 max-w-2xl mx-auto">
            Transform your imagination into cinematic masterpieces using cutting-edge AI technology
          </p>

          <div className="flex justify-center items-center space-x-6 mb-8">
            <CreditsDisplay />
            <motion.button
              whileHover={{ scale: 1.05, boxShadow: "0 0 30px rgba(147, 51, 234, 0.5)" }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowWizard(true)}
              className="glass-button flex items-center space-x-2 px-8 py-4 text-lg font-semibold cyber-border"
            >
              <Wand2 className="w-5 h-5" />
              <span>Create Movie</span>
            </motion.button>
          </div>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="grid md:grid-cols-3 gap-6 mb-16"
        >
          <motion.div
            whileHover={{ y: -5, scale: 1.02 }}
            className="glass-card p-6 text-center group"
          >
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
              className="w-16 h-16 glass-card flex items-center justify-center mx-auto mb-4 group-hover:neon-glow"
            >
              <Brain className="w-8 h-8 text-purple-400" />
            </motion.div>
            <h3 className="text-xl font-semibold text-white mb-2">AI-Powered Scripts</h3>
            <p className="text-white/70">
              Generate compelling movie scripts with advanced language models
            </p>
          </motion.div>

          <motion.div
            whileHover={{ y: -5, scale: 1.02 }}
            className="glass-card p-6 text-center group"
          >
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
              className="w-16 h-16 glass-card flex items-center justify-center mx-auto mb-4 group-hover:neon-glow"
            >
              <Camera className="w-8 h-8 text-blue-400" />
            </motion.div>
            <h3 className="text-xl font-semibold text-white mb-2">Cinematic Quality</h3>
            <p className="text-white/70">
              Create professional-quality videos with AI storyboarding and generation
            </p>
          </motion.div>

          <motion.div
            whileHover={{ y: -5, scale: 1.02 }}
            className="glass-card p-6 text-center group"
          >
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
              className="w-16 h-16 glass-card flex items-center justify-center mx-auto mb-4 group-hover:neon-glow"
            >
              <Zap className="w-8 h-8 text-cyan-400" />
            </motion.div>
            <h3 className="text-xl font-semibold text-white mb-2">Lightning Fast</h3>
            <p className="text-white/70">
              Generate complete movies in minutes with our optimized AI pipeline
            </p>
          </motion.div>
        </motion.div>

        {/* Movies Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
        >
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-3xl font-bold text-white flex items-center space-x-3">
              <Sparkles className="w-8 h-8 text-purple-400" />
              <span>Your Movies</span>
            </h2>
            <motion.button
              whileHover={{ scale: 1.05 }}
              onClick={fetchMovies}
              className="glass-button px-4 py-2"
            >
              Refresh
            </motion.button>
          </div>
          <MovieGrid movies={movies} loading={loading} />
        </motion.div>
      </main>

      {showWizard && (
        <MovieWizard onClose={() => setShowWizard(false)} onMovieCreated={fetchMovies} />
      )}
    </div>
  )
}
