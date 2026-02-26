import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Brain,
  DollarSign,
  Heart,
  TrendingUp,
  Settings,
} from 'lucide-react'
import './SideNav.css'

const navItems = [
  {
    section: 'Overview',
    items: [
      { path: '/overview', label: 'Dashboard', icon: LayoutDashboard },
    ],
  },
  {
    section: 'Intelligence',
    items: [
      { path: '/intelligence', label: 'Query', icon: Brain },
    ],
  },
  {
    section: 'Analytics',
    items: [
      { path: '/pricing', label: 'Pricing', icon: DollarSign },
      { path: '/sentiment', label: 'Sentiment', icon: Heart },
      { path: '/forecast', label: 'Forecast', icon: TrendingUp },
    ],
  },
  {
    section: 'Settings',
    items: [
      { path: '/settings', label: 'Settings', icon: Settings },
    ],
  },
]

export default function SideNav() {
  return (
    <nav className="sidenav">
      {navItems.map((section) => (
        <div key={section.section} className="nav-section">
          <h3 className="nav-section-title">{section.section}</h3>
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
                >
                  <Icon size={20} />
                  <span>{item.label}</span>
                </NavLink>
              )
            })}
          </div>
        </div>
      ))}
    </nav>
  )
}
