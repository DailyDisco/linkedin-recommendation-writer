import { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { recommendationApi } from '../services/api';
import type {
  ContributorInfo,
  HttpError,
  RegenerateRequest,
  RecommendationRequest,
} from '../types/index';
import ErrorBoundary from './ui/error-boundary';
import { parseGitHubInput, validateGitHubInput } from '@/lib/utils';
import { useRecommendationCount } from '../hooks/useLocalStorage';
import { trackEngagement, trackConversion } from '../utils/analytics';
import RecommendationModalHeader from './RecommendationModalHeader';
import RecommendationLimitMessage from './RecommendationLimitMessage';
import RecommendationForm from './RecommendationForm';
import RecommendationGeneratingState from './RecommendationGeneratingState';
import RecommendationOptionsDisplay from './RecommendationOptionsDisplay';
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
  const optionsRef = useRef<HTMLDivElement>(null); // New ref for options
  const resultRef = useRef<HTMLDivElement>(null); // New ref for result

  const { count: anonRecommendationCount, incrementCount: incrementAnonCount } =
    useRecommendationCount();
  const ANONYMOUS_LIMIT = 3; // Updated to match backend limit for anonymous users

  const [showLimitExceededMessage, setShowLimitExceededMessage] =
    useState(false);

  // Log modal open/close events
  useEffect(() => {
    if (isOpen) {
      // Focus the first input when modal opens
      setTimeout(() => {
        firstInputRef.current?.focus();
      }, 100);

      // Check anonymous limit only if not logged in
      if (!isLoggedIn && anonRecommendationCount >= ANONYMOUS_LIMIT) {
        setShowLimitExceededMessage(true);
      } else {
        setShowLimitExceededMessage(false);
      }
    }
  }, [isOpen, contributor, isLoggedIn, anonRecommendationCount]);

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

  // State declarations
  const [step, setStep] = useState<
    'form' | 'generating' | 'options' | 'result'
  >('form');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedRecommendation, setGeneratedRecommendation] = useState<{
    id: number;
    title: string;
    content: string;
    recommendation_type: string;
    tone: string;
    length: string;
    word_count: number;
    created_at: string;
    github_username: string;
  } | null>(null);
  const [recommendationOptions, setRecommendationOptions] = useState<
    Array<{
      id: number;
      name: string;
      content: string;
      title: string;
      word_count: number;
      focus: string;
      explanation: string;
      generation_parameters: Record<string, unknown>;
    }>
  >([]);
  const [selectedOption, setSelectedOption] = useState<{
    id: number;
    name: string;
    content: string;
    title: string;
    word_count: number;
    focus: string;
    explanation: string;
    generation_parameters: Record<string, unknown>;
  } | null>(null);
  const [isCreatingFromOption, setIsCreatingFromOption] = useState(false);

  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenerateInstructions, setRegenerateInstructions] = useState('');
  const [viewingFullContent, setViewingFullContent] = useState<number | null>(
    null
  );
  const [activeTab, setActiveTab] = useState<'preview' | 'refine'>('preview');

  // Auto-scroll to options/result when step changes
  useEffect(() => {
    if ((step === 'options' || step === 'result') && modalRef.current) {
      const targetRef = step === 'options' ? optionsRef : resultRef;
      if (targetRef.current) {
        modalRef.current.scrollTo({
          top: targetRef.current.offsetTop - modalRef.current.offsetTop,
          behavior: 'smooth',
        });
      }
    }
  }, [step, recommendationOptions.length, generatedRecommendation]); // Dependency on options/generated recs ensures it runs after content renders

  const [formData, setFormData] = useState<{
    workingRelationship: string;
    specificSkills: string;
    timeWorkedTogether: string;
    notableAchievements: string;
    recommendation_type:
      | 'professional'
      | 'technical'
      | 'leadership'
      | 'academic'
      | 'personal';
    tone: 'professional' | 'friendly' | 'formal' | 'casual';
    length: 'short' | 'medium' | 'long';
    github_input: string;
    analysis_type: 'profile' | 'repo_only';
    repository_url?: string;
  }>({
    workingRelationship: '',
    specificSkills: '',
    timeWorkedTogether: '',
    notableAchievements: '',
    recommendation_type: 'professional',
    tone: 'professional',
    length: 'medium',
    github_input: '',
    analysis_type: 'profile',
  });

  const [validationErrors, setValidationErrors] = useState<
    Record<string, string>
  >({});
  const [parsedGitHubInput, setParsedGitHubInput] = useState<{
    type: 'username' | 'repo_url';
    username: string;
    repository?: string;
    fullUrl?: string;
  } | null>(null);

  // Parse GitHub input when it changes
  useEffect(() => {
    if (formData.github_input.trim()) {
      const parsed = parseGitHubInput(formData.github_input);
      setParsedGitHubInput(parsed);

      // Auto-set analysis type based on input type
      if (parsed.type === 'repo_url') {
        setFormData(prev => ({ ...prev, analysis_type: 'repo_only' }));
      } else {
        setFormData(prev => ({ ...prev, analysis_type: 'profile' }));
      }
    } else {
      setParsedGitHubInput(null);
    }
  }, [formData.github_input]);

  const validateForm = () => {
    const errors: Record<string, string> = {};

    // Validate GitHub input
    if (!formData.github_input.trim()) {
      errors.github_input = 'GitHub username or repository URL is required';
    } else {
      const validation = validateGitHubInput(formData.github_input);
      if (!validation.isValid) {
        errors.github_input = validation.error || 'Invalid GitHub input';
      }
    }

    // Validate repository URL for repo_only mode
    if (
      formData.analysis_type === 'repo_only' &&
      parsedGitHubInput &&
      parsedGitHubInput.type === 'username'
    ) {
      if (!formData.repository_url || !formData.repository_url.trim()) {
        errors.repository_url =
          'Repository URL is required for repository-only analysis';
      } else {
        const repoValidation = validateGitHubInput(formData.repository_url);
        if (!repoValidation.isValid) {
          errors.repository_url =
            repoValidation.error || 'Invalid repository URL';
        } else {
          const repoParsed = parseGitHubInput(formData.repository_url);
          if (repoParsed.type !== 'repo_url') {
            errors.repository_url = 'Please enter a valid repository URL';
          }
        }
      }
    }

    // Validate working relationship
    if (!formData.workingRelationship.trim()) {
      errors.workingRelationship = 'Please describe your working relationship';
    } else if (formData.workingRelationship.trim().length < 10) {
      errors.workingRelationship =
        'Please provide more details about your working relationship (at least 10 characters)';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isLoggedIn && anonRecommendationCount >= ANONYMOUS_LIMIT) {
      setShowLimitExceededMessage(true);
      return;
    }

    if (!validateForm()) {
      return;
    }

    setIsGenerating(true);
    setStep('generating');

    try {
      // Create custom prompt from form data
      const customPrompt = `
Working Relationship: ${formData.workingRelationship}
Notable Skills Observed: ${formData.specificSkills}
Time Period: ${formData.timeWorkedTogether}
Key Achievements: ${formData.notableAchievements}
            `.trim();

      const request: RecommendationRequest = {
        github_username: contributor.username, // Use selected contributor's username
        recommendation_type: formData.recommendation_type,
        tone: formData.tone,
        length: formData.length,
        custom_prompt: customPrompt,
        include_specific_skills: formData.specificSkills
          .split(',')
          .map(s => s.trim())
          .filter(Boolean),
        target_role:
          formData.analysis_type === 'repo_only'
            ? `Repository: ${parsedGitHubInput!.repository || parseGitHubInput(formData.repository_url || '').repository}`
            : undefined,
        analysis_type: formData.analysis_type,
        repository_url: formData.repository_url,
      };

      const optionsResponse = await recommendationApi.generateOptions(request);

      // Increment count only if not logged in and generation was successful
      if (!isLoggedIn) {
        incrementAnonCount();
      }

      // Transform API response to include generation_parameters on each option
      const optionsWithParams = optionsResponse.options.map(option => ({
        ...option,
        generation_parameters: optionsResponse.generation_parameters || {},
      }));
      setRecommendationOptions(optionsWithParams);

      // Track successful recommendation generation
      trackEngagement.recommendationGenerated({
        githubUsername: contributor.username ? 'true' : 'false',
        tone: formData.tone,
        length: formData.length,
        hasKeywords: formData.specificSkills.trim().length > 0,
      });

      toast.success('Recommendation options generated successfully!');
      setStep('options');
    } catch (err: unknown) {
      console.error('Recommendation generation failed:', err);

      // Provide more specific error messages based on error type
      let errorMessage = 'Failed to generate recommendation. Please try again.';

      const error = err as HttpError; // Type assertion for axios error structure
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMessage =
          'Request timed out. The recommendation generation is taking longer than expected. Please try again.';
      } else if (error.response?.status === 429) {
        errorMessage =
          'Too many requests. Please wait a moment before trying again.';
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error. Please try again in a few moments.';
      } else if (error.response?.status === 400) {
        errorMessage =
          error.response?.data?.detail ||
          'Invalid request. Please check your input.';
      } else if (!error.response) {
        errorMessage =
          'Network error. Please check your connection and try again.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }

      toast.error(errorMessage);
      setStep('form');
    } finally {
      setIsGenerating(false);
    }
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
      setShowLimitExceededMessage(true);
      return;
    }
    setIsCreatingFromOption(true);

    try {
      const recommendation = await recommendationApi.createFromOption(
        contributor.username,
        {
          ...option,
          generation_parameters: option.generation_parameters || {},
        },
        recommendationOptions.map(opt => ({
          ...opt,
          generation_parameters: opt.generation_parameters || {},
        })),
        formData.analysis_type,
        formData.repository_url,
        formData.recommendation_type,
        formData.tone,
        formData.length
      );

      // Increment count only if not logged in and creation was successful
      if (!isLoggedIn) {
        incrementAnonCount();
      }

      setGeneratedRecommendation(recommendation);
      setSelectedOption({
        ...option,
        generation_parameters: option.generation_parameters || {},
      });

      // Track completed recommendation
      trackConversion.recommendationCompleted();

      toast.success('Recommendation created successfully!');
      setStep('result');
    } catch (err: unknown) {
      console.error('Failed to create recommendation from option:', err);
      const error = err as HttpError; // Type assertion for axios error structure
      toast.error(
        error.response?.data?.detail ||
          'Failed to create recommendation from selected option'
      );
    } finally {
      setIsCreatingFromOption(false);
    }
  };

  const handleViewMore = (optionId: number) => {
    setViewingFullContent(viewingFullContent === optionId ? null : optionId);
  };

  const handleRegenerate = async () => {
    if (!selectedOption || !regenerateInstructions.trim()) {
      return;
    }

    if (!isLoggedIn && anonRecommendationCount >= ANONYMOUS_LIMIT) {
      setShowLimitExceededMessage(true);
      return;
    }

    setIsRegenerating(true);

    try {
      const request: RegenerateRequest = {
        original_content: selectedOption.content,
        refinement_instructions: regenerateInstructions,
        github_username: contributor.username,
        recommendation_type: formData.recommendation_type,
        tone: formData.tone,
        length: formData.length,
      };

      const regeneratedRecommendation =
        await recommendationApi.regenerate(request);

      // Increment count only if not logged in and regeneration was successful
      if (!isLoggedIn) {
        incrementAnonCount();
      }

      setGeneratedRecommendation(regeneratedRecommendation);
      setRegenerateInstructions('');
      toast.success('Recommendation refined successfully!');
      setIsRegenerating(false);
    } catch (err: unknown) {
      console.error('Regeneration failed:', err);
      const error = err as HttpError; // Type assertion for axios error structure

      toast.error(
        error.response?.data?.detail ||
          'Failed to regenerate recommendation. Please try again.'
      );
      setIsRegenerating(false);
    }
  };

  const handleReset = () => {
    setStep('form');
    setGeneratedRecommendation(null);
    setRecommendationOptions([]);
    setSelectedOption(null);
    setValidationErrors({});
    setRegenerateInstructions('');
    setParsedGitHubInput(null);
    setViewingFullContent(null);
    setIsCreatingFromOption(false);
    setIsRegenerating(false);
    setActiveTab('preview'); // Reset active tab
    setFormData(prev => ({
      ...prev,
      github_input: '',
      analysis_type: 'profile',
      repository_url: undefined,
    }));
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
            {showLimitExceededMessage ? (
              <RecommendationLimitMessage onClose={onClose} />
            ) : step === 'form' ? (
              <RecommendationForm
                contributor={contributor}
                formData={formData}
                setFormData={setFormData}
                validationErrors={validationErrors}
                setValidationErrors={setValidationErrors}
                parsedGitHubInput={parsedGitHubInput}
                isGenerating={isGenerating}
                firstInputRef={firstInputRef}
                onSubmit={handleSubmit}
                onCancel={onClose}
              />
            ) : step === 'generating' ? (
              <RecommendationGeneratingState contributor={contributor} />
            ) : step === 'options' && recommendationOptions.length > 0 ? (
              <RecommendationOptionsDisplay
                recommendationOptions={
                  recommendationOptions as Array<{
                    id: number;
                    name: string;
                    content: string;
                    title: string;
                    word_count: number;
                    focus: string;
                    explanation: string;
                    generation_parameters?: Record<string, unknown>;
                  }>
                }
                contributor={contributor}
                formData={formData}
                parsedGitHubInput={parsedGitHubInput}
                isCreatingFromOption={isCreatingFromOption}
                viewingFullContent={viewingFullContent}
                optionsRef={optionsRef}
                onViewMore={handleViewMore}
                onOptionSelect={handleOptionSelect}
                onEditDetails={() => setStep('form')}
                onStartOver={handleReset}
              />
            ) : step === 'result' &&
              (generatedRecommendation || selectedOption) ? (
              <RecommendationResultDisplay
                generatedRecommendation={generatedRecommendation}
                selectedOption={selectedOption}
                contributor={contributor}
                formData={formData}
                activeTab={activeTab}
                resultRef={resultRef}
                regenerateInstructions={regenerateInstructions}
                setActiveTab={setActiveTab}
                setRegenerateInstructions={setRegenerateInstructions}
                setGeneratedRecommendation={setGeneratedRecommendation}
                isRegenerating={isRegenerating}
                onBackToOptions={() => setStep('options')}
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
