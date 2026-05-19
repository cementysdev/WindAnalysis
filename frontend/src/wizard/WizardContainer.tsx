import { useWizard } from '../hooks/useWizard';
import { StepIndicator } from './components/StepIndicator';
import { Step1DataSource } from './components/Step1DataSource';
import { Step2ConfigReview } from './components/Step2ConfigReview';
import { Step3Results } from './components/Step3Results';
import { ErrorNotification } from '../components/ErrorNotification';

export function WizardContainer() {
  const { state, setError } = useWizard();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      {/* Main Content */}
      <div className="container mx-auto px-2 sm:px-4 lg:px-6 py-4 sm:py-6 lg:py-8 max-w-[98%] sm:max-w-[96%] lg:max-w-[95%] xl:max-w-[92%]">
        {/* Step Indicator - Centered */}
        <div className="max-w-4xl mx-auto mb-4 sm:mb-6">
          <StepIndicator currentStep={state.currentStep} />
        </div>

        {/* Step Content - Centered */}
        <div className="bg-white rounded-lg shadow-lg p-3 sm:p-4 lg:p-6">
          {state.currentStep === 'dataSource' && <Step1DataSource />}
          {state.currentStep === 'configReview' && <Step2ConfigReview />}
          {state.currentStep === 'results' && <Step3Results />}
        </div>
      </div>

      {/* Error Notification */}
      {state.error && (
        <ErrorNotification
          message={state.error}
          onClose={() => setError(null)}
        />
      )}
    </div>
  );
}
