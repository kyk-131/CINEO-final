'use client'

import { motion } from 'framer-motion'
import { Film } from 'lucide-react'

export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center mx-auto mb-4"
        >
          <Film className="w-8 h-8 text-white" />
        </motion.div>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-xl text-dark-300"
        >
          Loading Cineo AI...
        </motion.p>
      </div>
    </div>
  )
}
