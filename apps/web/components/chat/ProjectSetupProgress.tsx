import React from 'react';

interface SetupStep {
  id: string;
  title: string;
  icon: string;
  status: 'pending' | 'in_progress' | 'completed';
}

interface ProjectSetupProgressProps {
  currentStep: number;
  steps: SetupStep[];
  isComplete: boolean;
}

const ProjectSetupProgress: React.FC<ProjectSetupProgressProps> = ({ 
  currentStep, 
  steps, 
  isComplete 
}) => {
  const getStepIcon = (step: SetupStep, index: number) => {
    if (step.status === 'completed') {
      return (
        <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      );
    } else if (step.status === 'in_progress') {
      return (
        <div className="w-5 h-5 rounded-full bg-orange-500 flex items-center justify-center flex-shrink-0">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
        </div>
      );
    } else {
      return (
        <div className="w-5 h-5 rounded-full border-2 border-gray-400 flex-shrink-0"></div>
      );
    }
  };

  const progressPercentage = isComplete ? 100 : ((currentStep + 1) / steps.length) * 100;

  return (
    <div className="bg-gray-800/80 rounded-lg p-3 mb-3">
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <div className="w-5 h-5 rounded-md bg-orange-500 flex items-center justify-center">
          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        </div>
        <h3 className="text-white font-bold text-sm">
          {isComplete ? 'Project setup complete!' : 'Setting up project...'}
        </h3>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className="bg-orange-500 h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
        <div className="text-xs text-gray-400 mt-1 text-right">
          {Math.round(progressPercentage)}%
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-1">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center gap-2">
            {getStepIcon(step, index)}
            <div className="flex-1 min-w-0">
              <div className={`text-sm leading-relaxed ${
                step.status === 'completed' 
                  ? 'text-gray-300 line-through opacity-60' 
                  : step.status === 'in_progress'
                  ? 'text-white'
                  : 'text-gray-400'
              }`}>
                {step.title}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProjectSetupProgress;
