import { useEffect, useRef } from 'react';
import ErrorBoundary from './ui/error-boundary';
import { parseGitHubInput, validateGitHubInput } from '@/lib/utils';
import { useRecommendationCount } from '../hooks/useLocalStorage';
import { trackEngagement, trackConversion } from '../utils/analytics';
import { useRecommendationState } from '../hooks/useRecommendationState';
import {
  useGenerateRecommendationOptions,
  useCreateRecommendationFromOption,
  useRegenerateRecommendation,
} from '../hooks/useRecommendationQueries';
import RecommendationModalHeader from './RecommendationModalHeader';
import RecommendationLimitMessage from './RecommendationLimitMessage';
import RecommendationGeneratingState from './RecommendationGeneratingState';
import RecommendationOptionsList from './recommendation/RecommendationOptionsList';
import { RecommendationFormNew } from './recommendation/RecommendationFormNew';
import RecommendationResultDisplay from './RecommendationResultDisplay';

interface RecommendationModalProps {
  contributor: ContributorInfo;
  isOpen: boolean;
  onClose: () => void;
  isLoggedIn: boolean;
}

export default function RecommendationModal({
  contributor,
  isOpen,
  onClose,
  isLoggedIn,
}: RecommendationModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const firstInputRef = useRef<HTMLTextAreaElement>(null);
  const optionsRef = useRef<HTMLDivElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  const { count: anonRecommendationCount, incrementCount: incrementAnonCount } =
    useRecommendationCount();
  const ANONYMOUS_LIMIT = 3;

  // Use the new reducer-based state management
  const { state, dispatch, updateFormField, reset } = useRecommendationState();

  // React Query mutations
  const generateOptionsMutation = useGenerateRecommendationOptions();
  const createFromOptionMutation = useCreateRecommendationFromOption();
  const regenerateMutation = useRegenerateRecommendation();

  // Log modal open/close events and initialize state
  useEffect(() => {
    if (isOpen) {
      // Focus the first input when modal opens
      setTimeout(() => {
        firstInputRef.current?.focus();
      }, 100);

      // Check anonymous limit and update state
      if (!isLoggedIn && anonRecommendationCount >= ANONYMOUS_LIMIT) {
        dispatch({ type: 'SET_SHOW_LIMIT_EXCEEDED', payload: true });
      } else {
        dispatch({ type: 'SET_SHOW_LIMIT_EXCEEDED', payload: false });
      }
    }
  }, [isOpen, isLoggedIn, anonRecommendationCount, dispatch]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Handle click outside
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // Auto-scroll to options/result when step changes
  useEffect(() => {
    if ((state.step === 'options' || state.step === 'result') && modalRef.current) {
      const targetRef = state.step === 'options' ? optionsRef : resultRef;
      if (targetRef.current) {
        modalRef.current.scrollTo({
          top: targetRef.current.offsetTop - modalRef.current.offsetTop,
          behavior: 'smooth',
        });
      }
    }
  }, [state.step, state.options.length, state.result]);

  // Parse GitHub input when it changes
  useEffect(() => {
    if (state.formData.github_input.trim()) {
      const parsed = parseGitHubInput(state.formData.github_input);
      dispatch({ type: 'SET_PARSED_GITHUB_INPUT', payload: parsed });

      // Auto-set analysis type based on input type
      if (parsed.type === 'repo_url') {
        dispatch({ type: 'UPDATE_FORM', payload: { analysis_type: 'repo_only' } });
      } else {
        dispatch({ type: 'UPDATE_FORM', payload: { analysis_type: 'profile' } });
      }
    } else {
      dispatch({ type: 'SET_PARSED_GITHUB_INPUT', payload: null });
    }
  }, [state.formData.github_input, dispatch]);

  const validateForm = () => {
    const errors: Record<string, string> = {};

    // Validate GitHub input
    if (!state.formData.github_input.trim()) {
      errors.github_input = 'GitHub username or repository URL is required';
    } else {
      const validation = validateGitHubInput(state.formData.github_input);
      if (!validation.isValid) {
        errors.github_input = validation.error || 'Invalid GitHub input';
      }
    }

    // Validate repository URL for repo_only mode
    if (
      state.formData.analysis_type === 'repo_only' &&
      state.parsedGitHubInput &&
      state.parsedGitHubInput.type === 'username'
    ) {
      if (!state.formData.repository_url || !state.formData.repository_url.trim()) {
        errors.repository_url =
          'Repository URL is required for repository-only analysis';
      } else {
        const repoValidation = validateGitHubInput(state.formData.repository_url);
        if (!repoValidation.isValid) {
          errors.repository_url =
            repoValidation.error || 'Invalid repository URL';
        } else {
          const repoParsed = parseGitHubInput(state.formData.repository_url);
          if (repoParsed.type !== 'repo_url') {
            errors.repository_url = 'Please enter a valid repository URL';
          }
        }
      }
    }

    // Validate working relationship
    if (!state.formData.workingRelationship.trim()) {
      errors.workingRelationship = 'Please describe your working relationship';
    } else if (state.formData.workingRelationship.trim().length < 10) {
      errors.workingRelationship =
        'Please provide more details about your working relationship (at least 10 characters)';
    }

    dispatch({ type: 'SET_ERRORS', payload: errors });
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isLoggedIn && anonRecommendationCount >= ANONYMOUS_LIMIT) {
      dispatch({ type: 'SET_SHOW_LIMIT_EXCEEDED', payload: true });
      return;
    }

    if (!validateForm()) {
      return;
    }

    dispatch({ type: 'SET_STEP', payload: 'generating' });

    // Create custom prompt from form data
    const customPrompt = `
Working Relationship: ${state.formData.workingRelationship}
Notable Skills Observed: ${state.formData.specificSkills}
Time Period: ${state.formData.timeWorkedTogether}
Key Achievements: ${state.formData.notableAchievements}
            `.trim();

    const request: RecommendationRequest = {
      github_username: contributor.username,
      recommendation_type: state.formData.recommendation_type,
      tone: state.formData.tone,
      length: state.formData.length,
      custom_prompt: customPrompt,
      include_specific_skills: state.formData.specificSkills
        .split(',')
        .map(s => s.trim())
        .filter(Boolean),
      target_role:
        state.formData.analysis_type === 'repo_only'
          ? `Repository: ${state.parsedGitHubInput!.repository || parseGitHubInput(state.formData.repository_url || '').repository}`
          : undefined,
      analysis_type: state.formData.analysis_type,
      repository_url: state.formData.repository_url,
    };

    // Use React Query mutation - it handles loading, error, and success states
    generateOptionsMutation.mutate(request, {
      onSuccess: (data) => {
        // Increment count only if not logged in and generation was successful
        if (!isLoggedIn) {
          incrementAnonCount();
        }

        // Transform API response to include generation_parameters on each option
        const optionsWithParams = data.options.map(option => ({
          ...option,
          generation_parameters: data.generation_parameters || {},
        }));
        dispatch({ type: 'SET_OPTIONS', payload: optionsWithParams });

        // Track successful recommendation generation
        trackEngagement.recommendationGenerated({
          githubUsername: contributor.username ? 'true' : 'false',
          tone: state.formData.tone,
          length: state.formData.length,
          hasKeywords: state.formData.specificSkills.trim().length > 0,
        });

        dispatch({ type: 'SET_STEP', payload: 'options' });
      },
      onError: () => {
        // Error handled by mutation
        dispatch({ type: 'SET_STEP', payload: 'form' });
      },
    });
  };

  const handleOptionSelect = async (option: {
    id: number;
    name: string;
    content: string;
    title: string;
    word_count: number;
    focus: string;
    explanation: string;
    generation_parameters?: Record<string, unknown>;
  }) => {
    if (!isLoggedIn && anonRecommendationCount >= ANONYMOUS_LIMIT) {
      dispatch({ type: 'SET_SHOW_LIMIT_EXCEEDED', payload: true });
      return;
    }

    const params = {
      github_username: contributor.username,
      option: {
        ...option,
        generation_parameters: option.generation_parameters || {},
      },
      options: state.options.map(opt => ({
        ...opt,
        generation_parameters: opt.generation_parameters || {},
      })),
      analysis_type: state.formData.analysis_type,
      repository_url: state.formData.repository_url,
      recommendation_type: state.formData.recommendation_type,
      tone: state.formData.tone,
      length: state.formData.length,
    };

    // Use React Query mutation - it handles loading, error, and success states
    createFromOptionMutation.mutate(params, {
      onSuccess: (recommendation) => {
        // Increment count only if not logged in and creation was successful
        if (!isLoggedIn) {
          incrementAnonCount();
        }

        dispatch({ type: 'SET_RESULT', payload: recommendation });
        dispatch({
          type: 'SET_SELECTED_OPTION', payload: {
            ...option,
            generation_parameters: option.generation_parameters || {},
          }
        });

        // Track completed recommendation
        trackConversion.recommendationCompleted();

        dispatch({ type: 'SET_STEP', payload: 'result' });
      },
      onError: () => {
        // Error handled by mutation
      },
    });
  };

  const handleViewMore = (optionId: number) => {
    dispatch({ type: 'SET_VIEWING_FULL_CONTENT', payload: optionId });
  };

  const handleRegenerate = async () => {
    if (!state.selectedOption || !state.regenerateInstructions.trim()) {
      return;
    }

    if (!isLoggedIn && anonRecommendationCount >= ANONYMOUS_LIMIT) {
      dispatch({ type: 'SET_SHOW_LIMIT_EXCEEDED', payload: true });
      return;
    }

    const params = {
      original_content: state.selectedOption.content,
      refinement_instructions: state.regenerateInstructions,
      github_username: contributor.username,
      recommendation_type: state.formData.recommendation_type,
      tone: state.formData.tone,
      length: state.formData.length,
    };

    // Use React Query mutation - it handles loading, error, and success states
    regenerateMutation.mutate(params, {
      onSuccess: (regeneratedRecommendation) => {
        // Increment count only if not logged in and regeneration was successful
        if (!isLoggedIn) {
          incrementAnonCount();
        }

        dispatch({ type: 'SET_RESULT', payload: regeneratedRecommendation });
        dispatch({ type: 'SET_REGENERATE_INSTRUCTIONS', payload: '' });
      },
      onError: () => {
        // Error handled by mutation
      },
    });
  };

  const handleReset = () => {
    reset();
  };

  if (!isOpen) return null;

  return (
    <div
      className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50'
      onClick={handleBackdropClick}
      role='dialog'
      aria-modal='true'
      aria-labelledby='modal-title'
    >
      <ErrorBoundary>
        <div
          ref={modalRef}
          className='bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto'
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <RecommendationModalHeader
            contributor={contributor}
            onClose={onClose}
          />

          {/* Content */}
          <div className='p-6'>
            {state.showLimitExceededMessage ? (
              <RecommendationLimitMessage onClose={onClose} />
            ) : state.step === 'form' ? (
              <RecommendationFormNew
                contributor={contributor}
                formData={state.formData}
                errors={state.errors}
                parsedGitHubInput={state.parsedGitHubInput}
                isGenerating={generateOptionsMutation.isPending}
                firstInputRef={firstInputRef}
                onChange={(field, value) => updateFormField(field, value)}
                onAnalysisTypeChange={(type) =>
                  dispatch({ type: 'UPDATE_FORM', payload: { analysis_type: type } })
                }
                onSubmit={handleSubmit}
                onCancel={onClose}
              />
            ) : state.step === 'generating' ? (
              <RecommendationGeneratingState contributor={contributor} />
            ) : state.step === 'options' && state.options.length > 0 ? (
              <RecommendationOptionsList
                options={state.options}
                contributor={contributor}
                formData={state.formData}
                parsedGitHubInput={state.parsedGitHubInput}
                isCreatingFromOption={createFromOptionMutation.isPending}
                viewingFullContent={state.viewingFullContent}
                onViewMore={handleViewMore}
                onOptionSelect={handleOptionSelect}
                onEditDetails={() => dispatch({ type: 'SET_STEP', payload: 'form' })}
                onStartOver={handleReset}
              />
            ) : state.step === 'result' &&
              (state.result || state.selectedOption) ? (
              <RecommendationResultDisplay
                generatedRecommendation={state.result}
                selectedOption={state.selectedOption}
                contributor={contributor}
                formData={state.formData}
                activeTab={state.activeTab}
                resultRef={resultRef}
                regenerateInstructions={state.regenerateInstructions}
                setActiveTab={(tab) => dispatch({ type: 'SET_ACTIVE_TAB', payload: tab })}
                setRegenerateInstructions={(instructions) =>
                  dispatch({ type: 'SET_REGENERATE_INSTRUCTIONS', payload: instructions })
                }
                setGeneratedRecommendation={(rec) =>
                  rec ? dispatch({ type: 'SET_RESULT', payload: rec }) : null
                }
                isRegenerating={regenerateMutation.isPending}
                onBackToOptions={() => dispatch({ type: 'SET_STEP', payload: 'options' })}
                onGenerateAnother={handleReset}
                onRefine={handleRegenerate}
                onClose={onClose}
              />
            ) : null}
          </div>
        </div>
      </ErrorBoundary>
    </div>
  );
}
