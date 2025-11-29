import { ReactNode, CSSProperties } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  gradient?: boolean;
  style?: CSSProperties;
}

export default function Card({ children, className = '', hover = false, gradient = false, style }: CardProps) {
  const baseClasses = 'bg-white rounded-xl border border-gray-200/60 shadow-sm';
  const hoverClasses = hover 
    ? 'card-hover cursor-pointer' 
    : '';
  const gradientClasses = gradient
    ? 'bg-gradient-to-br from-white to-gray-50'
    : '';

  return (
    <div
      className={`
        ${baseClasses}
        ${hoverClasses}
        ${gradientClasses}
        ${className}
      `}
      style={style}
    >
      {children}
    </div>
  );
}
