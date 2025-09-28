'use client'

import { motion } from 'framer-motion'
import { Coins } from 'lucide-react'

interface CreditsDisplayProps {
  credits?: number
}

export default function CreditsDisplay({ credits }: CreditsDisplayProps) {
  // For now, we'll use a static value. In a real app, this would come from the API
  const userCredits = credits || 300

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 }}
      className="flex items-center space-x-2 bg-dark-700 px-4 py-2 rounded-lg"
    >
      <Coins className="w-5 h-5 text-yellow-500" />
      <span className="text-white font-medium">{userCredits} Credits</span>
    </motion.div>
  )
}
