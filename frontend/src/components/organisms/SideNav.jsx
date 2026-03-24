import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Brain,
  DollarSign,
  Heart,
  TrendingUp,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import './SideNav.css'

const navItems = [
  {
    section: 'Overview',
    items: [
      { path: '/dashboard/overview', label: 'Dashboard', icon: LayoutDashboard },
    ],
  },
  {
    section: 'Intelligence',
    items: [
      { path: '/dashboard/intelligence', label: 'Query', icon: Brain },
    ],
  },
  {
    section: 'Analytics',
    items: [
      { path: '/dashboard/pricing', label: 'Pricing', icon: DollarSign },
      { path: '/dashboard/sentiment', label: 'Sentiment', icon: Heart },
      { path: '/dashboard/forecast', label: 'Forecast', icon: TrendingUp },
    ],
  },
  {
    section: 'Settings',
    items: [
      { path: '/dashboard/settings', label: 'Settings', icon: Settings },
    ],
  },
]

export default function SideNav() {
  const [isCollapsed, setIsCollapsed] = useState(false)

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed)
  }

  return (
    <nav className={`sidenav ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidenav-header">
        <button 
          className="collapse-button" 
          onClick={toggleSidebar}
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
      
      {navItems.map((section) => (
        <div key={section.section} className="nav-section">
          {!isCollapsed && <h3 className="nav-section-title">{section.section}</h3>}
          <div className="nav-items">
            {section.items.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `nav-item ${isActive ? 'active' : ''}`
                  }
                  title={isCollapsed ? item.label : ''}
                >
                  <Icon size={22} />
                  {!isCollapsed && <span>{item.label}</span>}
                </NavLink>
              )
            })}
          </div>
        </div>
      ))}
    </nav>
  )
}
