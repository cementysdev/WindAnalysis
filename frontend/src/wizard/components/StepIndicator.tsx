import type { WizardStep } from '../../types/wizard';
import { cn } from '../../lib/utils';

interface StepIndicatorProps {
  currentStep: WizardStep;
}

const steps: Array<{ id: WizardStep; label: string; number: number }> = [
  { id: 'dataSource', label: 'Source de données', number: 1 },
  { id: 'configReview', label: 'Configuration', number: 2 },
  { id: 'results', label: 'Résultats', number: 3 },
];

export function StepIndicator({ currentStep }: StepIndicatorProps) {
  const currentIndex = steps.findIndex((step) => step.id === currentStep);

  return (
    <div className="mb-4 sm:mb-6 lg:mb-8">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent = index === currentIndex;
          const isUpcoming = index > currentIndex;

          return (
            <div key={step.id} className="flex items-center flex-1">
              {/* Step Circle */}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 rounded-full flex items-center justify-center font-bold text-sm sm:text-base lg:text-lg transition-colors',
                    {
                      'bg-primary-dark text-white': isCurrent,
                      'bg-green-500 text-white': isCompleted,
                      'bg-gray-300 text-gray-600': isUpcoming,
                    }
                  )}
                >
                  {isCompleted ? (
                    <svg
                      className="w-4 h-4 sm:w-5 sm:h-5 lg:w-6 lg:h-6"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  ) : (
                    step.number
                  )}
                </div>
                <span
                  className={cn('mt-1 sm:mt-2 text-xs sm:text-sm font-medium text-center max-w-[80px] sm:max-w-none', {
                    'text-primary-dark': isCurrent,
                    'text-green-600': isCompleted,
                    'text-gray-500': isUpcoming,
                  })}
                >
                  {step.label}
                </span>
              </div>

              {/* Connector Line */}
              {index < steps.length - 1 && (
                <div
                  className={cn('flex-1 h-0.5 sm:h-1 mx-1 sm:mx-2 lg:mx-4 transition-colors', {
                    'bg-green-500': index < currentIndex,
                    'bg-gray-300': index >= currentIndex,
                  })}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
