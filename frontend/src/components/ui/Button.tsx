import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  isLoading = false,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-btn transition-colors duration-150 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none disabled:active:scale-100 select-none';

  const sizeStyles = {
    sm: 'min-h-[44px] px-3.5 py-2 text-sm gap-1.5',
    md: 'min-h-[48px] px-5 py-2.5 text-base gap-2',
    lg: 'min-h-[52px] sm:min-h-[56px] px-6 py-3 text-lg gap-2.5',
  };

  const variantStyles = {
    primary: 'bg-forest-700 text-canvas hover:bg-forest-900 shadow-sm',
    secondary: 'bg-leaf-100 text-forest-900 hover:bg-leaf-500/20',
    outline: 'border border-line-200 text-ink-900 hover:bg-surface hover:border-forest-700',
    ghost: 'text-forest-700 hover:bg-surface',
    danger: 'bg-danger-600 text-canvas hover:bg-danger-600/90 shadow-sm',
  };

  const widthStyle = fullWidth ? 'w-full' : '';

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${widthStyle} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="inline-block animate-spin mr-2">◌</span>
      ) : null}
      {children}
    </button>
  );
};
