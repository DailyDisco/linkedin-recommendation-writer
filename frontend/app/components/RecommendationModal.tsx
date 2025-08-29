import { useState, useEffect, useRef } from 'react';
import {
  X,
  Loader2,
  FileText,
  CheckCircle,
  AlertCircle,
  Eye,
  EyeOff,
} from 'lucide-react';
import { toast } from 'sonner';
import { recommendationApi } from '../services/api';
import type {
  ContributorInfo,
  HttpError,
  Recommendation,
  RecommendationOption,
  RegenerateRequest,
  RecommendationRequest,
} from '../types';
import ErrorBoundary from './ui/error-boundary';
import { parseGitHubInput, validateGitHubInput } from '@/lib/utils';
import { useRecommendationCount } from '../hooks/useLocalStorage';

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
  const ANONYMOUS_LIMIT = 1;

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
  const [generatedRecommendation, setGeneratedRecommendation] =
    useState<Recommendation | null>(null);
  const [recommendationOptions, setRecommendationOptions] = useState<
    RecommendationOption[]
  >([]);
  const [selectedOption, setSelectedOption] =
    useState<RecommendationOption | null>(null);
  const [isCreatingFromOption, setIsCreatingFromOption] = useState(false);

  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenerateInstructions, setRegenerateInstructions] = useState('');
  const [viewingFullContent, setViewingFullContent] = useState<number | null>(
    null
  );

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

      setRecommendationOptions(optionsResponse.options);
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

  const handleOptionSelect = async (option: RecommendationOption) => {
    if (!isLoggedIn && anonRecommendationCount >= ANONYMOUS_LIMIT) {
      setShowLimitExceededMessage(true);
      return;
    }
    setIsCreatingFromOption(true);

    try {
      const recommendation = await recommendationApi.createFromOption(
        contributor.username,
        option,
        recommendationOptions,
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
      setSelectedOption(option);
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
          <div className='flex items-center justify-between p-6 border-b'>
            <div className='flex items-center space-x-3'>
              <img
                src={contributor.avatar_url}
                alt={contributor.username}
                className='w-10 h-10 rounded-full'
              />
              <div>
                <h2
                  id='modal-title'
                  className='text-xl font-semibold text-gray-900'
                >
                  Write LinkedIn Recommendation
                </h2>
                <p className='text-gray-600'>
                  for {contributor.full_name || contributor.username} (@
                  {contributor.username})
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className='text-gray-400 hover:text-gray-600'
              aria-label='Close modal'
            >
              <X className='w-6 h-6' />
            </button>
          </div>

          {/* Content */}
          <div className='p-6'>
            {showLimitExceededMessage ? (
              <div className='text-center py-12'>
                <AlertCircle className='w-16 h-16 text-red-500 mx-auto mb-4' />
                <h3 className='text-2xl font-bold text-gray-900 mb-2'>
                  Recommendation Limit Reached
                </h3>
                <p className='text-lg text-gray-700 mb-6'>
                  You have used your one free recommendation for today.
                </p>
                <p className='text-gray-600 mb-6'>
                  Please create an account to generate up to 3 recommendations
                  per day.
                </p>
                <button
                  onClick={onClose}
                  className='px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-lg font-semibold'
                >
                  Create Account
                </button>
              </div>
            ) : step === 'form' ? (
              <form onSubmit={handleSubmit} className='space-y-6'>
                {/* GitHub Input Section */}
                <div>
                  <label
                    htmlFor='github-input'
                    className='block text-sm font-medium text-gray-700 mb-2'
                  >
                    GitHub Username or Repository URL *
                  </label>
                  <input
                    id='github-input'
                    type='text'
                    required
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${
                      validationErrors.github_input
                        ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                        : 'border-gray-300'
                    }`}
                    placeholder='e.g., johnsmith or https://github.com/johnsmith/myproject'
                    value={formData.github_input}
                    onChange={e => {
                      setFormData(prev => ({
                        ...prev,
                        github_input: e.target.value,
                      }));
                      if (validationErrors.github_input) {
                        setValidationErrors(prev => ({
                          ...prev,
                          github_input: '',
                        }));
                      }
                    }}
                    aria-describedby={
                      validationErrors.github_input
                        ? 'github-input-error'
                        : undefined
                    }
                  />
                  {validationErrors.github_input && (
                    <div
                      id='github-input-error'
                      className='mt-1 flex items-center space-x-1 text-sm text-red-600'
                    >
                      <AlertCircle className='w-4 h-4 flex-shrink-0' />
                      <p>{validationErrors.github_input}</p>
                    </div>
                  )}
                  {parsedGitHubInput && (
                    <div className='mt-2 p-2 bg-gray-50 rounded-md'>
                      <p className='text-sm text-gray-600'>
                        {parsedGitHubInput.type === 'repo_url' ? (
                          <>
                            📁 Repository:{' '}
                            <strong>
                              {parsedGitHubInput.username}/
                              {parsedGitHubInput.repository}
                            </strong>
                          </>
                        ) : (
                          <>
                            👤 User:{' '}
                            <strong>{parsedGitHubInput.username}</strong>
                          </>
                        )}
                      </p>
                    </div>
                  )}
                </div>

                {/* Analysis Type Selection */}
                {parsedGitHubInput && parsedGitHubInput.type === 'username' && (
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-2'>
                      Analysis Type
                    </label>
                    <div className='space-y-2'>
                      <label className='flex items-center'>
                        <input
                          type='radio'
                          name='analysis_type'
                          value='profile'
                          checked={formData.analysis_type === 'profile'}
                          onChange={e =>
                            setFormData(prev => ({
                              ...prev,
                              analysis_type: e.target.value as
                                | 'profile'
                                | 'repo_only',
                            }))
                          }
                          className='mr-2'
                        />
                        <span className='text-sm'>
                          <strong>Full Profile Analysis</strong> - Use all
                          repositories and profile information
                        </span>
                      </label>
                      <label className='flex items-center'>
                        <input
                          type='radio'
                          name='analysis_type'
                          value='repo_only'
                          checked={formData.analysis_type === 'repo_only'}
                          onChange={e =>
                            setFormData(prev => ({
                              ...prev,
                              analysis_type: e.target.value as
                                | 'profile'
                                | 'repo_only',
                            }))
                          }
                          className='mr-2'
                        />
                        <span className='text-sm text-gray-600'>
                          <strong>Repository Only</strong> - Focus on specific
                          repository (you&apos;ll be asked to provide one)
                        </span>
                      </label>
                    </div>
                  </div>
                )}

                {/* Repository Selection for repo_only mode */}
                {formData.analysis_type === 'repo_only' &&
                  parsedGitHubInput &&
                  parsedGitHubInput.type === 'username' && (
                    <div>
                      <label
                        htmlFor='repository-url'
                        className='block text-sm font-medium text-gray-700 mb-2'
                      >
                        Repository URL *
                      </label>
                      <input
                        id='repository-url'
                        type='text'
                        required
                        className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
                        placeholder='e.g., https://github.com/username/repository or username/repository'
                        value={formData.repository_url || ''}
                        onChange={e =>
                          setFormData(prev => ({
                            ...prev,
                            repository_url: e.target.value,
                          }))
                        }
                      />
                      <p className='text-xs text-gray-500 mt-1'>
                        Enter the specific repository URL you want to focus on
                        for the recommendation.
                      </p>
                      {validationErrors.repository_url && (
                        <div className='mt-1 flex items-center space-x-1 text-sm text-red-600'>
                          <AlertCircle className='w-4 h-4 flex-shrink-0' />
                          <p>{validationErrors.repository_url}</p>
                        </div>
                      )}
                    </div>
                  )}

                <div>
                  <label
                    htmlFor='working-relationship'
                    className='block text-sm font-medium text-gray-700 mb-2'
                  >
                    How did you work together? *
                  </label>
                  <textarea
                    id='working-relationship'
                    ref={firstInputRef}
                    required
                    className={`w-full h-20 px-3 py-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${
                      validationErrors.workingRelationship
                        ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                        : 'border-gray-300'
                    }`}
                    placeholder='e.g., We collaborated on the frontend development team for 8 months...'
                    value={formData.workingRelationship}
                    onChange={e => {
                      setFormData(prev => ({
                        ...prev,
                        workingRelationship: e.target.value,
                      }));
                      if (validationErrors.workingRelationship) {
                        setValidationErrors(prev => ({
                          ...prev,
                          workingRelationship: '',
                        }));
                      }
                    }}
                    aria-describedby={
                      validationErrors.workingRelationship
                        ? 'working-relationship-error'
                        : undefined
                    }
                  />
                  {validationErrors.workingRelationship && (
                    <div
                      id='working-relationship-error'
                      className='mt-1 flex items-center space-x-1 text-sm text-red-600'
                    >
                      <AlertCircle className='w-4 h-4 flex-shrink-0' />
                      <p>{validationErrors.workingRelationship}</p>
                    </div>
                  )}
                </div>

                <div>
                  <label
                    htmlFor='specific-skills'
                    className='block text-sm font-medium text-gray-700 mb-2'
                  >
                    What specific skills did you observe?
                  </label>
                  <textarea
                    id='specific-skills'
                    className='w-full h-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
                    placeholder='e.g., Excellent React skills, great at debugging, strong problem-solving...'
                    value={formData.specificSkills}
                    onChange={e =>
                      setFormData(prev => ({
                        ...prev,
                        specificSkills: e.target.value,
                      }))
                    }
                  />
                </div>

                <div>
                  <label
                    htmlFor='time-worked'
                    className='block text-sm font-medium text-gray-700 mb-2'
                  >
                    How long did you work together?
                  </label>
                  <input
                    id='time-worked'
                    type='text'
                    className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
                    placeholder='e.g., 8 months, 2 years...'
                    value={formData.timeWorkedTogether}
                    onChange={e =>
                      setFormData(prev => ({
                        ...prev,
                        timeWorkedTogether: e.target.value,
                      }))
                    }
                  />
                </div>

                <div>
                  <label
                    htmlFor='achievements'
                    className='block text-sm font-medium text-gray-700 mb-2'
                  >
                    Notable achievements or impact? (optional)
                  </label>
                  <textarea
                    id='achievements'
                    className='w-full h-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
                    placeholder='e.g., Reduced load times by 40%, mentored junior developers...'
                    value={formData.notableAchievements}
                    onChange={e =>
                      setFormData(prev => ({
                        ...prev,
                        notableAchievements: e.target.value,
                      }))
                    }
                  />
                </div>

                {/* Recommendation Settings */}
                <div className='bg-gray-50 p-4 rounded-lg space-y-4'>
                  <h3 className='font-medium text-gray-900'>
                    Recommendation Settings
                  </h3>

                  <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
                    <div>
                      <label
                        htmlFor='rec-type'
                        className='block text-sm font-medium text-gray-700 mb-1'
                      >
                        Type
                      </label>
                      <p className='text-xs text-gray-500 mb-2'>
                        Focus area of the recommendation
                      </p>
                      <select
                        id='rec-type'
                        className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
                        value={formData.recommendation_type}
                        onChange={e =>
                          setFormData(prev => ({
                            ...prev,
                            recommendation_type: e.target.value as
                              | 'professional'
                              | 'technical'
                              | 'leadership'
                              | 'academic'
                              | 'personal',
                          }))
                        }
                      >
                        <option value='professional'>Professional</option>
                        <option value='technical'>Technical</option>
                        <option value='leadership'>Leadership</option>
                        <option value='academic'>Academic</option>
                        <option value='personal'>Personal</option>
                      </select>
                    </div>

                    <div>
                      <label
                        htmlFor='rec-tone'
                        className='block text-sm font-medium text-gray-700 mb-1'
                      >
                        Tone
                      </label>
                      <p className='text-xs text-gray-500 mb-2'>
                        Writing style and voice
                      </p>
                      <select
                        id='rec-tone'
                        className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
                        value={formData.tone}
                        onChange={e =>
                          setFormData(prev => ({
                            ...prev,
                            tone: e.target.value as
                              | 'professional'
                              | 'friendly'
                              | 'formal'
                              | 'casual',
                          }))
                        }
                      >
                        <option value='professional'>Professional</option>
                        <option value='friendly'>Friendly</option>
                        <option value='formal'>Formal</option>
                        <option value='casual'>Casual</option>
                      </select>
                    </div>

                    <div>
                      <label
                        htmlFor='rec-length'
                        className='block text-sm font-medium text-gray-700 mb-1'
                      >
                        Length
                      </label>
                      <p className='text-xs text-gray-500 mb-2'>
                        Word count of the recommendation
                      </p>
                      <select
                        id='rec-length'
                        className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
                        value={formData.length}
                        onChange={e =>
                          setFormData(prev => ({
                            ...prev,
                            length: e.target.value as
                              | 'short'
                              | 'medium'
                              | 'long',
                          }))
                        }
                      >
                        <option value='short'>Short</option>
                        <option value='medium'>Medium</option>
                        <option value='long'>Long</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className='flex justify-end space-x-3'>
                  <button
                    type='button'
                    onClick={onClose}
                    className='px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors'
                  >
                    Cancel
                  </button>
                  <button
                    type='submit'
                    disabled={isGenerating}
                    className='px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2'
                  >
                    <FileText className='w-4 h-4' />
                    <span>Generate Recommendation</span>
                  </button>
                </div>
              </form>
            ) : step === 'generating' ? (
              <div className='text-center py-12'>
                <Loader2 className='w-12 h-12 animate-spin text-blue-600 mx-auto mb-4' />
                <h3 className='text-lg font-medium text-gray-900 mb-2'>
                  Generating Recommendation Options
                </h3>
                <p className='text-gray-600 mb-4'>
                  Analyzing {contributor.username}&apos;s GitHub profile and
                  creating multiple options...
                </p>
                <div className='bg-gray-200 rounded-full h-2 w-64 mx-auto mb-4'>
                  <div
                    className='bg-blue-600 h-2 rounded-full animate-pulse'
                    style={{ width: '60%' }}
                  ></div>
                </div>
                <p className='text-sm text-gray-500'>
                  This may take up to 60 seconds...
                </p>
              </div>
            ) : step === 'options' && recommendationOptions.length > 0 ? (
              <div ref={optionsRef} className='space-y-6'>
                {/* Header with navigation */}
                <div className='flex items-center justify-between'>
                  <div className='flex items-center space-x-3'>
                    <CheckCircle className='w-6 h-6 text-green-600' />
                    <div>
                      <h3 className='text-xl font-semibold text-gray-900'>
                        Choose Your Recommendation
                      </h3>
                      <p className='text-sm text-gray-600'>
                        for {contributor.full_name || contributor.username}
                      </p>
                    </div>
                  </div>
                  <div className='flex space-x-2'>
                    <button
                      onClick={() => setStep('form')}
                      className='px-3 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors text-sm'
                    >
                      ← Edit Details
                    </button>
                    <button
                      onClick={handleReset}
                      className='px-3 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors text-sm'
                    >
                      Start Over
                    </button>
                  </div>
                </div>

                {/* Generation summary */}
                <div className='bg-blue-50 border border-blue-200 rounded-lg p-4'>
                  <div className='flex items-center space-x-2 mb-2'>
                    <div className='w-2 h-2 bg-blue-600 rounded-full'></div>
                    <span className='text-sm font-medium text-blue-900'>
                      Generated based on your inputs
                    </span>
                  </div>
                  <p className='text-sm text-blue-800'>
                    {parsedGitHubInput?.type === 'repo_url'
                      ? `Repository: ${parsedGitHubInput.username}/${parsedGitHubInput.repository}`
                      : `GitHub Profile: ${parsedGitHubInput?.username || contributor.username}`}{' '}
                    • {formData.recommendation_type} • {formData.tone} tone •{' '}
                    {formData.length}
                  </p>
                </div>

                <p className='text-gray-600'>
                  Here are 3 different recommendation options based on the
                  GitHub analysis. Each option has a different focus area.
                  Choose the one that best fits your needs.
                </p>

                <div className='space-y-4'>
                  {recommendationOptions.map(option => (
                    <div
                      key={option.id}
                      className='border-2 border-gray-200 rounded-lg p-6 hover:border-blue-300 hover:shadow-md transition-all duration-200'
                    >
                      <div className='flex items-start justify-between mb-4'>
                        <div className='flex-1'>
                          <h4 className='text-lg font-semibold text-gray-900 mb-1'>
                            {option.name}
                          </h4>
                          <div className='flex items-center space-x-4 text-sm text-gray-600'>
                            <span className='flex items-center space-x-1'>
                              <span className='font-medium'>Focus:</span>
                              <span className='capitalize'>
                                {option.focus.replace('_', ' ')}
                              </span>
                            </span>
                            <span className='flex items-center space-x-1'>
                              <span className='font-medium'>Words:</span>
                              <span>{option.word_count}</span>
                            </span>
                            <span className='flex items-center space-x-1'>
                              <span className='font-medium'>Confidence:</span>
                              <span
                                className={`font-semibold ${
                                  option.confidence_score >= 80
                                    ? 'text-green-600'
                                    : option.confidence_score >= 60
                                      ? 'text-yellow-600'
                                      : 'text-red-600'
                                }`}
                              >
                                {option.confidence_score}%
                              </span>
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className='bg-gray-50 p-4 rounded-md mb-4 border-l-4 border-blue-200'>
                        <p className='text-gray-900 leading-relaxed'>
                          {viewingFullContent === option.id
                            ? option.content
                            : option.content.length > 400
                              ? option.content.substring(0, 400) + '...'
                              : option.content}
                        </p>
                      </div>

                      <div className='flex space-x-3'>
                        <button
                          onClick={() => handleViewMore(option.id)}
                          className='flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm flex items-center justify-center space-x-2'
                        >
                          {viewingFullContent === option.id ? (
                            <>
                              <EyeOff className='w-4 h-4' />
                              <span>Show Less</span>
                            </>
                          ) : (
                            <>
                              <Eye className='w-4 h-4' />
                              <span>Read Full</span>
                            </>
                          )}
                        </button>
                        <button
                          onClick={() => handleOptionSelect(option)}
                          disabled={isCreatingFromOption}
                          className='flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm flex items-center justify-center space-x-2 font-medium'
                        >
                          {isCreatingFromOption ? (
                            <>
                              <Loader2 className='w-4 h-4 animate-spin' />
                              <span>Creating...</span>
                            </>
                          ) : (
                            <>
                              <CheckCircle className='w-4 h-4' />
                              <span>Select This</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : step === 'result' &&
              (generatedRecommendation || selectedOption) ? (
              <div ref={resultRef} className='space-y-6'>
                <div className='flex items-center justify-between'>
                  <div className='flex items-center space-x-3'>
                    <CheckCircle className='w-6 h-6 text-green-600' />
                    <div>
                      <h3 className='text-xl font-semibold text-gray-900'>
                        Recommendation Ready
                      </h3>
                      <p className='text-sm text-gray-600'>
                        for {contributor.full_name || contributor.username}
                      </p>
                    </div>
                  </div>
                  <div className='flex space-x-2'>
                    <button
                      onClick={() => setStep('options')}
                      className='px-3 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors text-sm'
                    >
                      ← Back to Options
                    </button>
                    <button
                      onClick={handleReset}
                      className='px-3 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors text-sm'
                    >
                      Generate Another
                    </button>
                  </div>
                </div>

                <div className='bg-gray-50 p-6 rounded-lg'>
                  <div className='mb-4 flex items-center justify-between text-sm text-gray-600'>
                    <div className='flex items-center space-x-4'>
                      <span>
                        Type:{' '}
                        {generatedRecommendation?.recommendation_type ||
                          formData.recommendation_type}
                      </span>
                      <span>
                        Tone: {generatedRecommendation?.tone || formData.tone}
                      </span>
                      <span>
                        Length:{' '}
                        {generatedRecommendation?.length || formData.length}
                      </span>
                    </div>
                    <span>
                      {generatedRecommendation?.word_count ||
                        selectedOption?.word_count}{' '}
                      words
                    </span>
                  </div>
                  <div className='prose max-w-none'>
                    <p className='text-gray-900 leading-relaxed whitespace-pre-wrap'>
                      {generatedRecommendation?.content ||
                        selectedOption?.content}
                    </p>
                  </div>
                </div>

                {/* Regeneration Section */}
                <div className='bg-blue-50 p-4 rounded-lg'>
                  <h4 className='font-medium text-gray-900 mb-2'>
                    Want to refine this recommendation?
                  </h4>
                  <p className='text-sm text-gray-600 mb-3'>
                    Provide specific instructions for how you&apos;d like the
                    recommendation modified.
                  </p>
                  <textarea
                    className='w-full h-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 mb-3'
                    placeholder='e.g., Make it more specific about their React skills, focus less on teamwork, emphasize their problem-solving abilities...'
                    value={regenerateInstructions}
                    onChange={e => setRegenerateInstructions(e.target.value)}
                  />
                  <button
                    onClick={handleRegenerate}
                    disabled={!regenerateInstructions.trim() || isRegenerating}
                    className='px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2'
                  >
                    {isRegenerating ? (
                      <Loader2 className='w-4 h-4 animate-spin' />
                    ) : (
                      <FileText className='w-4 h-4' />
                    )}
                    <span>
                      {isRegenerating ? 'Refining...' : 'Refine Recommendation'}
                    </span>
                  </button>
                </div>

                <div className='flex justify-end space-x-3'>
                  <button
                    onClick={onClose}
                    className='px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors'
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </ErrorBoundary>
    </div>
  );
}
