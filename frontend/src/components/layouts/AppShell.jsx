import { Outlet } from 'react-router-dom'
import TopBar from '../organisms/TopBar'
import SideNav from '../organisms/SideNav'
import './AppShell.css'

export default function AppShell() {
  return (
    <div className="app-shell">
      <TopBar />
      <div className="app-body">
        <SideNav />
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
