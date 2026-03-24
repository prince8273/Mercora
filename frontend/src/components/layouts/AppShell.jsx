import { Outlet } from 'react-router-dom'
import { useState } from 'react'
import ModernTopBar from '../organisms/ModernTopBar'
import ModernSideNav from '../organisms/ModernSideNav'
import './AppShell.css'

export default function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="app-shell">
      <ModernTopBar mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />
      <div className="app-body">
        <ModernSideNav mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
