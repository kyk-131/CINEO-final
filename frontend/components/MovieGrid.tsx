'use client'

import { motion } from 'framer-motion'
import { Play, Calendar, Clock } from 'lucide-react'

interface Movie {
  id: number
  title: string
  genre: string
  style: string
  description: string
  status: string
  created_at: string
  poster_url?: string
}

interface MovieGridProps {
  movies: Movie[]
  loading: boolean
}

export default function MovieGrid({ movies, loading }: MovieGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.1 }}
            className="card p-6 animate-pulse"
          >
            <div className="aspect-video bg-dark-700 rounded-lg mb-4"></div>
            <div className="h-4 bg-dark-700 rounded mb-2"></div>
            <div className="h-3 bg-dark-700 rounded w-2/3"></div>
          </motion.div>
        ))}
      </div>
    )
  }

  if (movies.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-12"
      >
        <div className="w-24 h-24 bg-dark-700 rounded-full flex items-center justify-center mx-auto mb-4">
          <Play className="w-12 h-12 text-dark-500" />
        </div>
        <h3 className="text-xl font-semibold text-white mb-2">No movies yet</h3>
        <p className="text-dark-300">Create your first AI-generated movie to get started!</p>
      </motion.div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {movies.map((movie, index) => (
        <motion.div
          key={movie.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className="card p-6 hover:shadow-xl transition-shadow duration-300"
        >
          <div className="aspect-video bg-gradient-to-br from-primary-600 to-primary-800 rounded-lg mb-4 flex items-center justify-center">
            {movie.poster_url ? (
              <img
                src={movie.poster_url}
                alt={movie.title}
                className="w-full h-full object-cover rounded-lg"
              />
            ) : (
              <Play className="w-16 h-16 text-white opacity-50" />
            )}
          </div>

          <h3 className="text-xl font-semibold text-white mb-2">{movie.title}</h3>

          <div className="flex items-center justify-between text-sm text-dark-300 mb-3">
            <span className="bg-primary-600 px-2 py-1 rounded text-xs">{movie.genre}</span>
            <span className="capitalize">{movie.status}</span>
          </div>

          <p className="text-dark-300 text-sm mb-4 line-clamp-2">{movie.description}</p>

          <div className="flex items-center justify-between text-xs text-dark-400">
            <div className="flex items-center space-x-1">
              <Calendar className="w-3 h-3" />
              <span>{new Date(movie.created_at).toLocaleDateString()}</span>
            </div>
            <div className="flex items-center space-x-1">
              <Clock className="w-3 h-3" />
              <span>2 min</span>
            </div>
          </div>

          <button className="mt-4 btn-primary w-full">
            {movie.status === 'completed' ? 'Watch Movie' : 'View Progress'}
          </button>
        </motion.div>
      ))}
    </div>
  )
}
