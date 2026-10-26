import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'surface' | 'accent' | 'outlined';
  hoverEffect?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  hoverEffect = false,
  className = '',
  ...props
}) => {
  const baseStyles = 'rounded-card p-5 sm:p-6 transition-all duration-200';

  const variantStyles = {
    default: 'bg-canvas border border-line-200 shadow-soft',
    surface: 'bg-surface border border-line-200/80',
    accent: 'bg-leaf-100 border border-leaf-500/20',
    outlined: 'bg-transparent border border-line-200',
  };

  const hoverStyles = hoverEffect
    ? 'hover:-translate-y-0.5 hover:shadow-md hover:border-forest-700/30'
    : '';

  return (
    <div
      className={`${baseStyles} ${variantStyles[variant]} ${hoverStyles} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
