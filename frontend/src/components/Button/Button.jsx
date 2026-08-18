import styles from './Button.module.css'

function Button({ variant = 'secondary', className = '', type = 'button', ...props }) {
  const variantClass = styles[variant] ?? styles.secondary
  return <button type={type} className={`${styles.button} ${variantClass} ${className}`.trim()} {...props} />
}

export default Button
