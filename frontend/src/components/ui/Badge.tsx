import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'success' | 'warning' | 'info' | 'neutral' | 'offline' | 'danger';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  className = '',
  ...props
}) => {
  const baseStyles = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold';

  const variantStyles = {
    success: 'bg-leaf-100 text-forest-900 border border-leaf-500/20',
    warning: 'bg-paddy-400/20 text-soil-700 border border-paddy-400/30',
    info: 'bg-sky-600/10 text-sky-600 border border-sky-600/20',
    neutral: 'bg-surface text-ink-600 border border-line-200',
    offline: 'bg-soil-100 text-soil-700 border border-soil-700/20',
    danger: 'bg-danger-600/10 text-danger-600 border border-danger-600/20',
  };

  return (
    <span className={`${baseStyles} ${variantStyles[variant]} ${className}`} {...props}>
      {children}
    </span>
  );
};
