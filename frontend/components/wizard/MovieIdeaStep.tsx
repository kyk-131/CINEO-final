'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Lightbulb, ArrowRight } from 'lucide-react'

interface MovieIdeaStepProps {
  data: any
  updateData: (updates: any) => void
  onNext: () => void
}

export default function MovieIdeaStep({ data, updateData, onNext }: MovieIdeaStepProps) {
  const [title, setTitle] = useState(data.title)
  const [genre, setGenre] = useState(data.genre)
  const [description, setDescription] = useState(data.description)

  const genres = [
    'Action', 'Adventure', 'Comedy', 'Drama', 'Horror', 'Romance',
    'Sci-Fi', 'Thriller', 'Fantasy', 'Mystery', 'Animation', 'Documentary'
  ]

  const handleNext = () => {
    if (title && genre && description) {
      updateData({ title, genre, description })
      onNext()
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <Lightbulb className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-3xl font-bold text-white mb-4">What's your movie idea?</h2>
        <p className="text-dark-300">
          Tell us about your vision and we'll bring it to life with AI-powered generation
        </p>
      </motion.div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-dark-200 mb-2">
            Movie Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input w-full"
            placeholder="Enter your movie title..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-dark-200 mb-2">
            Genre
          </label>
          <select
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
            className="input w-full"
          >
            <option value="">Select a genre...</option>
            {genres.map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-dark-200 mb-2">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input w-full h-32 resize-none"
            placeholder="Describe your movie idea, plot, characters, and key scenes..."
          />
        </div>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleNext}
          disabled={!title || !genre || !description}
          className="btn-primary w-full py-4 text-lg font-semibold flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>Generate Script</span>
          <ArrowRight className="w-5 h-5" />
        </motion.button>
      </div>
    </div>
  )
}
