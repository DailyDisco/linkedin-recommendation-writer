import { useEffect, useRef } from 'react';
import ErrorBoundary from './ui/error-boundary';
import { parseGitHubInput, validateGitHubInput } from '@/lib/utils';
import { useRecommendationCount } from '../hooks/useLocalStorage';
import { trackEngagement, trackConversion } from '../utils/analytics';
import { useRecommendationState } from '../hooks/useRecommendationState';
import {
  useGenerateRecommendationOptions,
  useGenerateRecommendationOptionsStream,
  useCreateRecommendationFromOption,
  useRegenerateRecommendation,
  useRegenerateRecommendationStream,
} from '../hooks/useRecommendationQueries';
import { apiClient } from '@/services/api';
import RecommendationModalHeader from './RecommendationModalHeader';
import RecommendationLimitMessage from './RecommendationLimitMessage';
import RecommendationGeneratingState from './RecommendationGeneratingState';
import RecommendationOptionsList from './recommendation/RecommendationOptionsList';
import { RecommendationFormNew } from './recommendation/RecommendationFormNew';
import RecommendationResultDisplay from './RecommendationResultDisplay';
import type {
  ContributorInfo,
  RecommendationRequest,
  RecommendationOption,
} from '../types/index';

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

  const { state, dispatch, updateFormField, reset } = useRecommendationState();

  const generateOptionsMutation = useGenerateRecommendationOptions();
  const generateOptionsStream = useGenerateRecommendationOptionsStream();
  const createFromOptionMutation = useCreateRecommendationFromOption();
  const regenerateMutation = useRegenerateRecommendation();
  const regenerateStream = useRegenerateRecommendationStream();

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        firstInputRef.current?.focus();
      }, 100);

      if (!isLoggedIn && anonRecommendationCount >= ANONYMOUS_LIMIT) {
        dispatch({ type: 'SET_SHOW_LIMIT_EXCEEDED', payload: true });
      } else {
        dispatch({ type: 'SET_SHOW_LIMIT_EXCEEDED', payload: false });
      }
    }
  }, [isOpen, isLoggedIn, anonRecommendationCount, dispatch]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  useEffect(() => {
    if (
      (state.step === 'options' || state.step === 'result') &&
      modalRef.current
    ) {
      const targetRef = state.step === 'options' ? optionsRef : resultRef;
      if (targetRef.current) {
        modalRef.current.scrollTo({
          top: targetRef.current.offsetTop - modalRef.current.offsetTop,
          behavior: 'smooth',
        });
      }
    }
  }, [state.step, state.options.length, state.result]);

  useEffect(() => {
    if (state.formData.github_input.trim()) {
      const parsed = parseGitHubInput(state.formData.github_input);
      dispatch({ type: 'SET_PARSED_GITHUB_INPUT', payload: parsed });

      if (parsed.type === 'repo_url') {
        dispatch({
          type: 'UPDATE_FORM',
          payload: { analysis_type: 'repo_only' },
        });
      } else {
        dispatch({
          type: 'UPDATE_FORM',
          payload: { analysis_type: 'profile' },
        });
      }
    } else {
      dispatch({ type: 'SET_PARSED_GITHUB_INPUT', payload: null });
    }
  }, [state.formData.github_input, dispatch]);

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!state.formData.github_input.trim()) {
      errors.github_input = 'GitHub username or repository URL is required';
    } else {
      const validation = validateGitHubInput(state.formData.github_input);
      if (!validation.isValid) {
        errors.github_input = validation.error || 'Invalid GitHub input';
      }
    }

    if (
      state.formData.analysis_type === 'repo_only' &&
      state.parsedGitHubInput &&
      state.parsedGitHubInput.type === 'username'
    ) {
      if (
        !state.formData.repository_url ||
        !state.formData.repository_url.trim()
      ) {
        errors.repository_url =
          'Repository URL is required for repository-only analysis';
      } else {
        const repoParsed = parseGitHubInput(state.formData.repository_url);
        if (repoParsed.type !== 'repo_url') {
          errors.repository_url = 'Please enter a valid repository URL';
        }
      }
    }

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

    // Use streaming version for real-time progress updates
    generateOptionsStream.generate(
      request,
      progress => {
        // Update progress in state
        dispatch({ type: 'SET_CURRENT_STAGE', payload: progress.stage });
        dispatch({ type: 'SET_PROGRESS', payload: progress.progress });
      },
      data => {
        // Increment count only if not logged in and generation was successful
        if (!isLoggedIn) {
          incrementAnonCount();
        }

        const optionsWithParams = data.options.map(
          (option: RecommendationOption) => ({
            ...option,
            generation_parameters: data.generation_parameters || {},
          })
        );
        dispatch({ type: 'SET_OPTIONS', payload: optionsWithParams });

        trackEngagement.recommendationGenerated({
          githubUsername: contributor.username ? 'true' : 'false',
          tone: state.formData.tone,
          length: state.formData.length,
          hasKeywords: state.formData.specificSkills.trim().length > 0,
        });

        dispatch({ type: 'SET_STEP', payload: 'options' });
      },
      _error => {
        dispatch({ type: 'SET_STEP', payload: 'form' });
      }
    );
  };

  const handleOptionSelect = async (option: RecommendationOption) => {
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

    createFromOptionMutation.mutate(params, {
      onSuccess: recommendation => {
        if (!isLoggedIn) {
          incrementAnonCount();
        }

        dispatch({ type: 'SET_RESULT', payload: recommendation });
        dispatch({
          type: 'SET_SELECTED_OPTION',
          payload: {
            ...option,
            generation_parameters: option.generation_parameters || {},
          },
        });

        trackConversion.recommendationCompleted();

        dispatch({ type: 'SET_STEP', payload: 'result' });
      },
      onError: () => {},
    });
  };

  const handleViewMore = (optionId: number) => {
    dispatch({ type: 'SET_VIEWING_FULL_CONTENT', payload: optionId });
  };

  const handleRegenerate = async (dynamicParams: {
    tone: string;
    length: string;
    include_keywords: string[];
    exclude_keywords: string[];
    refinement_instructions: string;
  }) => {
    if (!state.selectedOption) {
      return;
    }

    if (!isLoggedIn && anonRecommendationCount >= ANONYMOUS_LIMIT) {
      dispatch({ type: 'SET_SHOW_LIMIT_EXCEEDED', payload: true });
      return;
    }

    const params = {
      original_content: state.selectedOption.content,
      refinement_instructions: dynamicParams.refinement_instructions,
      github_username: contributor.username,
      recommendation_type: state.formData.recommendation_type,
      tone: dynamicParams.tone,
      length: dynamicParams.length,
      include_keywords: dynamicParams.include_keywords,
      exclude_keywords: dynamicParams.exclude_keywords,
    };

    dispatch({ type: 'SET_IS_REGENERATING', payload: true });

    // Use streaming version for real-time progress updates during refinement
    regenerateStream.regenerate(
      params,
      progress => {
        // Update progress in state
        dispatch({ type: 'SET_CURRENT_STAGE', payload: progress.stage });
        dispatch({ type: 'SET_PROGRESS', payload: progress.progress });
      },
      regeneratedRecommendation => {
        if (!isLoggedIn) {
          incrementAnonCount();
        }
        dispatch({ type: 'SET_RESULT', payload: regeneratedRecommendation });
        dispatch({ type: 'SET_REGENERATE_INSTRUCTIONS', payload: '' });
        dispatch({ type: 'SET_IS_REGENERATING', payload: false });
      },
      _error => {
        dispatch({ type: 'SET_IS_REGENERATING', payload: false });
      }
    );
  };

  const handleReset = () => {
    reset();
  };

  const handleFetchSuggestions = async (
    githubUsername: string,
    recommendationType: string,
    tone: string,
    length: string
  ) => {
    if (!isLoggedIn && anonRecommendationCount >= ANONYMOUS_LIMIT) {
      dispatch({ type: 'SET_SHOW_LIMIT_EXCEEDED', payload: true });
      return;
    }

    dispatch({ type: 'SET_LOADING_SUGGESTIONS', payload: true });

    try {
      const suggestions = await apiClient.getPromptSuggestions({
        github_username: githubUsername,
        recommendation_type: recommendationType,
        tone,
        length,
      });
      dispatch({ type: 'SET_INITIAL_SUGGESTIONS', payload: suggestions });
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      // Set empty suggestions on error to avoid breaking the UI
      dispatch({ type: 'SET_INITIAL_SUGGESTIONS', payload: null });
    } finally {
      dispatch({ type: 'SET_LOADING_SUGGESTIONS', payload: false });
    }
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
                initialSuggestions={state.initialSuggestions}
                isLoadingSuggestions={state.isLoadingSuggestions}
                onChange={(field, value) => updateFormField(field, value)}
                onAnalysisTypeChange={type =>
                  dispatch({
                    type: 'UPDATE_FORM',
                    payload: { analysis_type: type },
                  })
                }
                onFetchSuggestions={handleFetchSuggestions}
                onSubmit={handleSubmit}
                onCancel={onClose}
              />
            ) : state.step === 'generating' ? (
              <RecommendationGeneratingState
                contributor={contributor}
                currentStage={state.currentStage}
                progress={state.progress}
              />
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
                onEditDetails={() =>
                  dispatch({ type: 'SET_STEP', payload: 'form' })
                }
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
                setActiveTab={tab =>
                  dispatch({ type: 'SET_ACTIVE_TAB', payload: tab })
                }
                setRegenerateInstructions={instructions =>
                  dispatch({
                    type: 'SET_REGENERATE_INSTRUCTIONS',
                    payload: instructions,
                  })
                }
                isRegenerating={regenerateMutation.isPending}
                onBackToOptions={() =>
                  dispatch({ type: 'SET_STEP', payload: 'options' })
                }
                onGenerateAnother={handleReset}
                onRefine={handleRegenerate}
                initialIncludeKeywords={state.dynamicIncludeKeywords}
                initialExcludeKeywords={state.dynamicExcludeKeywords}
              />
            ) : null}
          </div>
        </div>
      </ErrorBoundary>
    </div>
  );
}
