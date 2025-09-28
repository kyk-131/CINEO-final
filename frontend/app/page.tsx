'use client'

import { useAuth } from '@/contexts/AuthContext'
import Dashboard from '@/components/Dashboard'
import Login from '@/components/Login'
import Loading from '@/components/Loading'

export default function Home() {
  const { user, loading } = useAuth()

  if (loading) {
    return <Loading />
  }

  if (!user) {
    return <Login />
  }

  return <Dashboard />
}
