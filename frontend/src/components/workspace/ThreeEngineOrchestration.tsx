import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Zap, Palette, CheckCircle } from 'lucide-react';

interface EngineStatus {
  memory: { active: boolean; entities?: number };
  parallel: { active: boolean; tasks?: number };
  creative: { active: boolean; ideas?: number };
}

interface ThreeEngineOrchestrationProps {
  onComplete: () => void;
  engineStatus: EngineStatus;
}

const ThreeEngineOrchestration: React.FC<ThreeEngineOrchestrationProps> = ({
  onComplete,
  engineStatus
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  const orchestrationSteps = [
    {
      id: 0,
      name: 'Memory Engine Initialization',
      icon: Brain,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20',
      description: 'Loading context and entity relationships',
      duration: 1500
    },
    {
      id: 1,
      name: 'Parallel Processing Setup',
      icon: Zap,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/20',
      description: 'Distributing tasks across multiple agents',
      duration: 1200
    },
    {
      id: 2,
      name: 'Creative Engine Activation',
      icon: Palette,
      color: 'text-pink-400',
      bgColor: 'bg-pink-500/20',
      description: 'Generating innovative solutions and ideas',
      duration: 1800
    },
    {
      id: 3,
      name: 'Engine Synchronization',
      icon: CheckCircle,
      color: 'text-green-400',
      bgColor: 'bg-green-500/20',
      description: 'Coordinating all engines for optimal response',
      duration: 1000
    }
  ];

  useEffect(() => {
    const timer = setTimeout(() => {
      if (currentStep < orchestrationSteps.length - 1) {
        setCompletedSteps(prev => [...prev, currentStep]);
        setCurrentStep(prev => prev + 1);
      } else {
        setCompletedSteps(prev => [...prev, currentStep]);
        setTimeout(() => {
          onComplete();
        }, 1000);
      }
    }, orchestrationSteps[currentStep].duration);

    return () => clearTimeout(timer);
  }, [currentStep, onComplete]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="bg-gray-800/95 backdrop-blur-md rounded-2xl p-6 border border-gray-700 max-w-lg mx-auto"
    >
      <div className="text-center mb-6">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full flex items-center justify-center"
        >
          <Zap className="w-8 h-8 text-white" />
        </motion.div>
        <h3 className="text-xl font-bold text-white mb-2">
          Three-Engine Orchestration
        </h3>
        <p className="text-gray-300 text-sm">
          Coordinating Memory🧠 + Parallel⚡ + Creative🎨 engines for optimal response
        </p>
      </div>

      <div className="space-y-4">
        {orchestrationSteps.map((step, index) => {
          const Icon = step.icon;
          const isActive = currentStep === index;
          const isCompleted = completedSteps.includes(index);
          const isUpcoming = index > currentStep;

          return (
            <motion.div
              key={step.id}
              className={`flex items-center space-x-4 p-4 rounded-lg border transition-all ${
                isActive
                  ? `${step.bgColor} border-current ${step.color}`
                  : isCompleted
                  ? 'bg-green-500/10 border-green-500/30 text-green-400'
                  : 'bg-gray-700/30 border-gray-600/30 text-gray-400'
              }`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <div className="relative">
                <motion.div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    isActive
                      ? step.bgColor
                      : isCompleted
                      ? 'bg-green-500/20'
                      : 'bg-gray-600/50'
                  }`}
                  animate={isActive ? { scale: [1, 1.1, 1] } : {}}
                  transition={{ duration: 1, repeat: Infinity }}
                >
                  <Icon className="w-5 h-5" />
                </motion.div>
                
                {isActive && (
                  <motion.div
                    className="absolute inset-0 rounded-full border-2 border-current"
                    animate={{ scale: [1, 1.2, 1], opacity: [1, 0, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                )}
              </div>

              <div className="flex-1">
                <div className="font-medium">{step.name}</div>
                <div className="text-sm opacity-75">{step.description}</div>
              </div>

              <div className="flex items-center space-x-2">
                {isCompleted && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center"
                  >
                    <CheckCircle className="w-4 h-4 text-white" />
                  </motion.div>
                )}
                
                {isActive && (
                  <motion.div
                    className="w-6 h-6 border-2 border-current rounded-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  />
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Engine Status Display */}
      <div className="mt-6 pt-4 border-t border-gray-700">
        <div className="grid grid-cols-3 gap-4 text-center text-sm">
          <div className={`${engineStatus.memory.active ? 'text-blue-400' : 'text-gray-500'}`}>
            <Brain className="w-5 h-5 mx-auto mb-1" />
            <div>Memory</div>
            <div className="text-xs opacity-75">
              {engineStatus.memory.entities || 0} entities
            </div>
          </div>
          
          <div className={`${engineStatus.parallel.active ? 'text-yellow-400' : 'text-gray-500'}`}>
            <Zap className="w-5 h-5 mx-auto mb-1" />
            <div>Parallel</div>
            <div className="text-xs opacity-75">
              {engineStatus.parallel.tasks || 0} tasks
            </div>
          </div>
          
          <div className={`${engineStatus.creative.active ? 'text-pink-400' : 'text-gray-500'}`}>
            <Palette className="w-5 h-5 mx-auto mb-1" />
            <div>Creative</div>
            <div className="text-xs opacity-75">
              {engineStatus.creative.ideas || 0} ideas
            </div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-4">
        <div className="flex justify-between text-xs text-gray-400 mb-2">
          <span>Orchestration Progress</span>
          <span>{Math.round(((currentStep + 1) / orchestrationSteps.length) * 100)}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <motion.div
            className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 h-2 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${((currentStep + 1) / orchestrationSteps.length) * 100}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
      </div>
    </motion.div>
  );
};

export default ThreeEngineOrchestration;