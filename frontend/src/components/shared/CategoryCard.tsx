import { useState, type ReactNode } from 'react';
import { ChevronDown, type LucideIcon } from 'lucide-react';
import { cn } from '../../lib/utils';

interface CategoryCardProps {
  title: string;
  icon?: LucideIcon;
  children: ReactNode;
  defaultOpen?: boolean;
  collapsible?: boolean;
}

export function CategoryCard({
  title,
  icon: Icon,
  children,
  defaultOpen = true,
  collapsible = true,
}: CategoryCardProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const toggleOpen = () => {
    if (collapsible) {
      setIsOpen((prev) => !prev);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden mb-4 sm:mb-5 lg:mb-6">
      {/* Header */}
      <div
        className={cn(
          'bg-primary-dark text-white px-3 sm:px-4 py-2 sm:py-3 flex items-center justify-between',
          collapsible && 'cursor-pointer hover:bg-blue-700 transition-colors'
        )}
        onClick={toggleOpen}
      >
        <div className="flex items-center space-x-2 sm:space-x-3">
          {Icon && <Icon className="w-5 h-5 sm:w-6 sm:h-6 flex-shrink-0" />}
          <h3 className="text-base sm:text-lg lg:text-xl font-bold">{title}</h3>
        </div>

        {collapsible && (
          <ChevronDown
            className={cn('w-5 h-5 sm:w-6 sm:h-6 transition-transform flex-shrink-0', {
              'transform rotate-180': isOpen,
            })}
          />
        )}
      </div>

      {/* Content */}
      {isOpen && <div className="p-2 sm:p-3 lg:p-4">{children}</div>}
    </div>
  );
}
