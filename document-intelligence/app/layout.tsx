import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'DevOS Document Intelligence',
  description: 'Evidence-first archive, OCR, AI metadata and portal automation control plane.',
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>
}
