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
  analysis_context_type: 'profile' | 'repo_only';
  repository_url?: string;
  force_refresh?: boolean;
}

// Define the overall state shape
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
  // New state for real-time progress
  currentStage: string;
  progress: number;
  // New state for dynamic refinement parameters
  dynamicTone: RecommendationFormData['tone'];
  dynamicLength: RecommendationFormData['length'];
  dynamicIncludeKeywords: string[];
  dynamicExcludeKeywords: string[];
}

// Define action types for the reducer
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
  | { type: 'SET_CURRENT_STAGE'; payload: string } // New action
  | { type: 'SET_PROGRESS'; payload: number } // New action
  | {
      // New action to update all dynamic refinement params
      type: 'UPDATE_DYNAMIC_REFINEMENT_PARAMS';
      payload: {
        tone: RecommendationFormData['tone'];
        length: RecommendationFormData['length'];
        include_keywords: string[];
        exclude_keywords: string[];
      };
    }
  | { type: 'RESET' };

const initialFormData: RecommendationFormData = {
  workingRelationship: '',
  specificSkills: '',
  timeWorkedTogether: '',
  notableAchievements: '',
  recommendation_type: 'professional',
  tone: 'professional',
  length: 'medium',
  github_input: '',
  analysis_context_type: 'profile',
  repository_url: '',
  force_refresh: false,
};

const initialState: RecommendationState = {
  step: 'form',
  formData: initialFormData,
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
  currentStage: 'Initializing...', // Default initial stage
  progress: 0, // Default initial progress
  dynamicTone: 'professional',
  dynamicLength: 'medium',
  dynamicIncludeKeywords: [],
  dynamicExcludeKeywords: [],
};

function recommendationReducer(
  state: RecommendationState,
  action: RecommendationAction
): RecommendationState {
  switch (action.type) {
    case 'SET_STEP':
      return { ...state, step: action.payload };
    case 'UPDATE_FORM':
      return { ...state, formData: { ...state.formData, ...action.payload } };
    case 'SET_ERRORS':
      return { ...state, errors: action.payload };
    case 'SET_PARSED_GITHUB_INPUT':
      return { ...state, parsedGitHubInput: action.payload };
    case 'SET_OPTIONS':
      return { ...state, options: action.payload };
    case 'SET_SELECTED_OPTION':
      return { ...state, selectedOption: action.payload };
    case 'SET_RESULT':
      // When a new result is set, update the dynamic refinement parameters to match the new result
      return {
        ...state,
        result: action.payload,
        dynamicTone:
          (action.payload.tone as RecommendationFormData['tone']) ||
          state.dynamicTone,
        dynamicLength:
          (action.payload.length as RecommendationFormData['length']) ||
          state.dynamicLength,
        dynamicIncludeKeywords:
          (action.payload.generation_parameters
            ?.include_keywords as string[]) || state.dynamicIncludeKeywords,
        dynamicExcludeKeywords:
          (action.payload.generation_parameters
            ?.exclude_keywords as string[]) || state.dynamicExcludeKeywords,
      };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_VIEWING_FULL_CONTENT':
      return { ...state, viewingFullContent: action.payload };
    case 'SET_ACTIVE_TAB':
      return { ...state, activeTab: action.payload };
    case 'SET_REGENERATE_INSTRUCTIONS':
      return { ...state, regenerateInstructions: action.payload };
    case 'SET_IS_REGENERATING':
      return { ...state, isRegenerating: action.payload };
    case 'SET_SHOW_LIMIT_EXCEEDED':
      return { ...state, showLimitExceededMessage: action.payload };
    case 'SET_CURRENT_STAGE': // New case
      return { ...state, currentStage: action.payload };
    case 'SET_PROGRESS': // New case
      return { ...state, progress: action.payload };
    case 'UPDATE_DYNAMIC_REFINEMENT_PARAMS': // New case
      return {
        ...state,
        dynamicTone: action.payload.tone,
        dynamicLength: action.payload.length,
        dynamicIncludeKeywords: action.payload.include_keywords,
        dynamicExcludeKeywords: action.payload.exclude_keywords,
      };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

export const useRecommendationState = () => {
  const [state, dispatch] = useReducer(recommendationReducer, initialState);

  const updateFormField = useCallback((field: string, value: string) => {
    dispatch({ type: 'UPDATE_FORM', payload: { [field]: value } });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  return { state, dispatch, updateFormField, reset };
};
