import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'
import { Button } from '@/components/ui/Button'

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-center px-4">
      <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center mb-4">
        <Compass className="w-7 h-7 text-muted-foreground" />
      </div>
      <h1 className="text-lg font-bold text-foreground">Page not found</h1>
      <p className="text-sm text-muted-foreground mt-1 max-w-sm">
        The page you&apos;re looking for doesn&apos;t exist or may have moved.
      </p>
      <Link to="/" className="mt-5">
        <Button variant="primary">Back to Overview</Button>
      </Link>
    </div>
  )
}
