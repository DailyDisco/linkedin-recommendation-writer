import { useReducer, useCallback } from 'react';
import type {
  Recommendation,
  RecommendationOption,
  ParsedGitHubInput,
} from '../types/index';

// Form data type
export interface RecommendationFormData {
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
}

// State interface
export interface RecommendationState {
  step: 'form' | 'generating' | 'options' | 'result';
  formData: RecommendationFormData;
  errors: Record<string, string>;
  parsedGitHubInput: ParsedGitHubInput | null;
  options: RecommendationOption[];
  selectedOption: RecommendationOption | null;
  result: Recommendation | null;
  isLoading: boolean;
  viewingFullContent: number | null;
  activeTab: 'preview' | 'refine';
  regenerateInstructions: string;
  isRegenerating: boolean;
  showLimitExceededMessage: boolean;
}

// Action types
export type RecommendationAction =
  | { type: 'SET_STEP'; payload: RecommendationState['step'] }
  | { type: 'UPDATE_FORM'; payload: Partial<RecommendationFormData> }
  | { type: 'SET_ERRORS'; payload: Record<string, string> }
  | { type: 'SET_PARSED_GITHUB_INPUT'; payload: ParsedGitHubInput | null }
  | { type: 'SET_OPTIONS'; payload: RecommendationOption[] }
  | { type: 'SET_SELECTED_OPTION'; payload: RecommendationOption }
  | { type: 'SET_RESULT'; payload: Recommendation }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_VIEWING_FULL_CONTENT'; payload: number | null }
  | { type: 'SET_ACTIVE_TAB'; payload: RecommendationState['activeTab'] }
  | { type: 'SET_REGENERATE_INSTRUCTIONS'; payload: string }
  | { type: 'SET_IS_REGENERATING'; payload: boolean }
  | { type: 'SET_SHOW_LIMIT_EXCEEDED'; payload: boolean }
  | { type: 'RESET' };

// Initial state
const initialState: RecommendationState = {
  step: 'form',
  formData: {
    workingRelationship: '',
    specificSkills: '',
    timeWorkedTogether: '',
    notableAchievements: '',
    recommendation_type: 'professional',
    tone: 'professional',
    length: 'medium',
    github_input: '',
    analysis_type: 'profile',
  },
  errors: {},
  parsedGitHubInput: null,
  options: [],
  selectedOption: null,
  result: null,
  isLoading: false,
  viewingFullContent: null,
  activeTab: 'preview',
  regenerateInstructions: '',
  isRegenerating: false,
  showLimitExceededMessage: false,
};

// Reducer function
function recommendationReducer(
  state: RecommendationState,
  action: RecommendationAction
): RecommendationState {
  switch (action.type) {
    case 'SET_STEP':
      return { ...state, step: action.payload };

    case 'UPDATE_FORM':
      return {
        ...state,
        formData: { ...state.formData, ...action.payload },
        errors: {}, // Clear errors when form changes
      };

    case 'SET_ERRORS':
      return { ...state, errors: action.payload };

    case 'SET_PARSED_GITHUB_INPUT':
      return { ...state, parsedGitHubInput: action.payload };

    case 'SET_OPTIONS':
      return { ...state, options: action.payload };

    case 'SET_SELECTED_OPTION':
      return { ...state, selectedOption: action.payload };

    case 'SET_RESULT':
      return { ...state, result: action.payload };

    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };

    case 'SET_VIEWING_FULL_CONTENT':
      return {
        ...state,
        viewingFullContent:
          state.viewingFullContent === action.payload ? null : action.payload,
      };

    case 'SET_ACTIVE_TAB':
      return { ...state, activeTab: action.payload };

    case 'SET_REGENERATE_INSTRUCTIONS':
      return { ...state, regenerateInstructions: action.payload };

    case 'SET_IS_REGENERATING':
      return { ...state, isRegenerating: action.payload };

    case 'SET_SHOW_LIMIT_EXCEEDED':
      return { ...state, showLimitExceededMessage: action.payload };

    case 'RESET':
      return initialState;

    default:
      return state;
  }
}

// Custom hook
export const useRecommendationState = () => {
  const [state, dispatch] = useReducer(recommendationReducer, initialState);

  // Helper functions for common operations
  const updateFormField = useCallback((field: string, value: string) => {
    dispatch({ type: 'UPDATE_FORM', payload: { [field]: value } });
  }, []);

  const setFormData = useCallback((data: Partial<RecommendationFormData>) => {
    dispatch({ type: 'UPDATE_FORM', payload: data });
  }, []);

  const setStep = useCallback((step: RecommendationState['step']) => {
    dispatch({ type: 'SET_STEP', payload: step });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  return {
    state,
    dispatch,
    // Helper functions
    updateFormField,
    setFormData,
    setStep,
    reset,
  };
};
