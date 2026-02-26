import { Loader2 } from 'lucide-react'
import './Button.css'

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  isLoading = false,
  disabled = false,
  onClick,
  type = 'button',
  ...props
}) {
  const className = `btn btn-${variant} btn-${size} ${fullWidth ? 'btn-full' : ''} ${
    isLoading || disabled ? 'btn-disabled' : ''
  }`

  return (
    <button
      type={type}
      className={className}
      onClick={onClick}
      disabled={isLoading || disabled}
      {...props}
    >
      {isLoading && <Loader2 size={16} className="btn-spinner" />}
      {children}
    </button>
  )
}
