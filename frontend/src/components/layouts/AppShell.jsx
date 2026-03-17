import { Outlet } from 'react-router-dom'
import ModernTopBar from '../organisms/ModernTopBar'
import ModernSideNav from '../organisms/ModernSideNav'
import './AppShell.css'

export default function AppShell() {
  return (
    <div className="app-shell">
      <ModernTopBar />
      <div className="app-body">
        <ModernSideNav />
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
