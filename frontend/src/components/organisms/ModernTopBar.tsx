import { Bell, Search, User, LogOut, Settings } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import './TopBar.css'

export default function ModernTopBar() {
  const { user, logout } = useAuth()

  const handleLogout = () => {
    logout()
  }

  const handleSettings = () => {
    // Navigate to settings page
    window.location.href = '/dashboard/settings'
  }

  return (
    <header className="topbar">
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
        <Button variant="ghost" size="icon" title="Notifications">
          <Bell size={20} />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center gap-2 px-3">
              <div className="h-8 w-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
                <User className="h-4 w-4 text-white" />
              </div>
              <span className="hidden md:inline-block text-sm font-medium">
                {user?.full_name || user?.email?.split('@')[0] || 'User'}
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end">
            <DropdownMenuLabel>
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">
                  {user?.full_name || 'User'}
                </p>
                <p className="text-xs leading-none text-muted-foreground">
                  {user?.email || 'No email'}
                </p>
                <p className="text-xs leading-none text-muted-foreground">
                  {user?.is_superuser ? 'Superuser' : 'User'}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleSettings}>
              <Settings className="mr-2 h-4 w-4" />
              <span>Settings</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}