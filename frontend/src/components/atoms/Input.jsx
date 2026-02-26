import './Input.css'

export function Input({
  label,
  error,
  helperText,
  fullWidth = true,
  ...props
}) {
  return (
    <div className={`input-wrapper ${fullWidth ? 'input-full' : ''}`}>
      {label && <label className="input-label">{label}</label>}
      <input
        className={`input ${error ? 'input-error' : ''}`}
        {...props}
      />
      {error && <span className="input-error-text">{error}</span>}
      {helperText && !error && (
        <span className="input-helper-text">{helperText}</span>
      )}
    </div>
  )
}
