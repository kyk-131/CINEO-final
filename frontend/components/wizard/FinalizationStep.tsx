'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Sparkles, Download, Play, ArrowLeft } from 'lucide-react'

interface FinalizationStepProps {
  data: any
  updateData: (updates: any) => void
  onComplete: () => void
  onPrev: () => void
}

export default function FinalizationStep({ data, updateData, onComplete, onPrev }: FinalizationStepProps) {
  const [generating, setGenerating] = useState(false)
  const [posterUrl, setPosterUrl] = useState<string | null>(null)
  const [trailerUrl, setTrailerUrl] = useState<string | null>(null)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)

  const generateFinalAssets = async () => {
    setGenerating(true)

    try {
      // Generate poster
      const mockPoster = `https://picsum.photos/400/600?random=${data.title}`
      setPosterUrl(mockPoster)

      // Generate trailer
      const mockTrailer = `https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4`
      setTrailerUrl(mockTrailer)

      // Generate final movie
      const mockVideo = `https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_2mb.mp4`
      setVideoUrl(mockVideo)

      // Update data
      updateData({
        poster_url: mockPoster,
        trailer_url: mockTrailer,
        video_url: mockVideo
      })

      // Simulate API calls in a real app
      // await generatePoster()
      // await generateTrailer()
      // await generateFinalMovie()

    } catch (error) {
      console.error('Generation failed:', error)
    } finally {
      setGenerating(false)
    }
  }

  const handleComplete = () => {
    onComplete()
  }

  return (
    <div className="max-w-4xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <Sparkles className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-3xl font-bold text-white mb-4">Finalize Your Movie</h2>
        <p className="text-dark-300">
          Generate poster, trailer, and final movie file
        </p>
      </motion.div>

      <div className="grid md:grid-cols-3 gap-6 mb-8">
        {/* Poster */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-6 text-center"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Movie Poster</h3>
          <div className="aspect-[2/3] bg-dark-700 rounded-lg flex items-center justify-center mb-4">
            {posterUrl ? (
              <img
                src={posterUrl}
                alt="Movie Poster"
                className="w-full h-full object-cover rounded-lg"
              />
            ) : (
              <Sparkles className="w-12 h-12 text-dark-500" />
            )}
          </div>
          {!posterUrl && (
            <button
              onClick={generateFinalAssets}
              disabled={generating}
              className="btn-primary w-full"
            >
              {generating ? 'Generating...' : 'Generate Poster'}
            </button>
          )}
        </motion.div>

        {/* Trailer */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card p-6 text-center"
        >
          <h3 className="text-lg font-semibold text-white mb-4">30s Trailer</h3>
          <div className="aspect-video bg-dark-700 rounded-lg flex items-center justify-center mb-4">
            {trailerUrl ? (
              <video
                src={trailerUrl}
                className="w-full h-full object-cover rounded-lg"
                controls
              />
            ) : (
              <Play className="w-12 h-12 text-dark-500" />
            )}
          </div>
          {!trailerUrl && (
            <button
              onClick={generateFinalAssets}
              disabled={generating}
              className="btn-primary w-full"
            >
              {generating ? 'Generating...' : 'Generate Trailer'}
            </button>
          )}
        </motion.div>

        {/* Full Movie */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card p-6 text-center"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Full Movie</h3>
          <div className="aspect-video bg-dark-700 rounded-lg flex items-center justify-center mb-4">
            {videoUrl ? (
              <video
                src={videoUrl}
                className="w-full h-full object-cover rounded-lg"
                controls
              />
            ) : (
              <Download className="w-12 h-12 text-dark-500" />
            )}
          </div>
          {!videoUrl && (
            <button
              onClick={generateFinalAssets}
              disabled={generating}
              className="btn-primary w-full"
            >
              {generating ? 'Generating...' : 'Generate Movie'}
            </button>
          )}
        </motion.div>
      </div>

      <div className="card p-6 mb-8">
        <h3 className="text-xl font-semibold text-white mb-4">Movie Details</h3>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <p className="text-dark-300">Title: <span className="text-white">{data.title}</span></p>
            <p className="text-dark-300">Genre: <span className="text-white">{data.genre}</span></p>
            <p className="text-dark-300">Style: <span className="text-white">{data.style}</span></p>
          </div>
          <div>
            <p className="text-dark-300">Scenes: <span className="text-white">{data.script?.length || 0}</span></p>
            <p className="text-dark-300">Duration: <span className="text-white">~3 minutes</span></p>
            <p className="text-dark-300">Credits Used: <span className="text-white">120</span></p>
          </div>
        </div>
      </div>

      <div className="flex justify-between">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onPrev}
          className="btn-secondary flex items-center space-x-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Previous</span>
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleComplete}
          className="btn-primary flex items-center space-x-2"
        >
          <span>Complete Movie</span>
          <Sparkles className="w-4 h-4" />
        </motion.button>
      </div>
    </div>
  )
}
