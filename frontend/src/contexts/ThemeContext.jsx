import { createContext, useContext, useState, useEffect } from 'react'

const ThemeContext = createContext(null)

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('system')

  // Function to get the actual theme to apply (resolves 'system' to 'light' or 'dark')
  const getEffectiveTheme = (themePreference) => {
    if (themePreference === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
    return themePreference
  }

  // Function to apply theme to document
  const applyTheme = (themePreference) => {
    const effectiveTheme = getEffectiveTheme(themePreference)
    document.documentElement.setAttribute('data-theme', effectiveTheme)
  }

  useEffect(() => {
    // Load theme from localStorage or user preferences
    const storedPreferences = localStorage.getItem('userPreferences')
    let themePreference = 'system'
    
    if (storedPreferences) {
      try {
        const preferences = JSON.parse(storedPreferences)
        themePreference = preferences.theme || 'system'
      } catch (error) {
        console.error('Failed to parse user preferences:', error)
      }
    } else {
      // Fallback to old theme storage
      themePreference = localStorage.getItem('theme') || 'system'
    }
    
    setTheme(themePreference)
    applyTheme(themePreference)

    // Listen for system theme changes when using 'system' theme
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleSystemThemeChange = () => {
      if (theme === 'system') {
        applyTheme('system')
      }
    }

    mediaQuery.addEventListener('change', handleSystemThemeChange)
    return () => mediaQuery.removeEventListener('change', handleSystemThemeChange)
  }, [])

  // Listen for preferences changes from settings page
  useEffect(() => {
    const handlePreferencesChange = (event) => {
      const { preferences } = event.detail
      if (preferences.theme && preferences.theme !== theme) {
        setTheme(preferences.theme)
        applyTheme(preferences.theme)
      }
    }

    window.addEventListener('preferencesChanged', handlePreferencesChange)
    return () => window.removeEventListener('preferencesChanged', handlePreferencesChange)
  }, [theme])

  // Update theme when it changes
  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    
    // Update user preferences
    try {
      const storedPreferences = localStorage.getItem('userPreferences')
      const preferences = storedPreferences ? JSON.parse(storedPreferences) : {}
      preferences.theme = newTheme
      localStorage.setItem('userPreferences', JSON.stringify(preferences))
    } catch (error) {
      console.error('Failed to update theme in preferences:', error)
    }
  }

  const setThemePreference = (newTheme) => {
    setTheme(newTheme)
    
    // Update user preferences
    try {
      const storedPreferences = localStorage.getItem('userPreferences')
      const preferences = storedPreferences ? JSON.parse(storedPreferences) : {}
      preferences.theme = newTheme
      localStorage.setItem('userPreferences', JSON.stringify(preferences))
    } catch (error) {
      console.error('Failed to update theme in preferences:', error)
    }
  }

  const value = {
    theme,
    effectiveTheme: getEffectiveTheme(theme),
    toggleTheme,
    setTheme: setThemePreference,
  }

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return context
}
