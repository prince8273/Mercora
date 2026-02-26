import { Bell, Search, User, LogOut } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import './TopBar.css'

export default function TopBar() {
  const { user, logout } = useAuth()

  // Force re-render when user changes
  console.log('TopBar rendering with user:', user?.email)

  return (
    <header className="topbar" key={user?.id}>
      <div className="topbar-left">
        <h1 className="topbar-logo">E-commerce Intelligence</h1>
      </div>

      <div className="topbar-center">
        <div className="search-bar">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search... (⌘K)"
            className="search-input"
          />
        </div>
      </div>

      <div className="topbar-right">
        <button className="icon-button" title="Notifications">
          <Bell size={20} />
        </button>

        <div className="user-menu">
          <button className="user-button">
            <User size={20} />
            <span className="user-name">{user?.full_name || user?.email || 'User'}</span>
          </button>
          <div className="user-dropdown">
            <div className="user-info">
              <p className="user-email">{user?.email || 'No email'}</p>
              <p className="user-role">
                {user?.is_superuser ? 'Superuser' : 'User'}
              </p>
            </div>
            <button className="dropdown-item" onClick={logout}>
              <LogOut size={16} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
