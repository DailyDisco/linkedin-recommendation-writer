import { AdvancedFeatures } from '@/components/AdvancedFeatures';
import { useAuth } from '../hooks/useAuth';
import type { MultiContributorData } from '../types';
import { apiClient } from '@/services/api';
import { PleaseSignInOrRegister } from '../components/PleaseSignInOrRegister';

interface KeywordRefineData {
  keywords: string[];
  exclude_keywords?: string[];
  tone?: string;
  length?: string;
}

interface ReadmeGenerationData {
  repository_full_name: string;
  style: string;
  include_sections?: string[];
  target_audience: string;
}

interface SkillAnalysisData {
  github_username: string;
  target_role: string;
  industry: string;
  experience_level: string;
}

export default function AdvancedPage() {
  const { isLoggedIn } = useAuth();

  if (!isLoggedIn) {
    return <PleaseSignInOrRegister />;
  }

  // API integration functions
  const handleKeywordRefine = async (data: KeywordRefineData) => {
    console.log('Keyword refinement requested:', data);
    // This would be handled by the parent component
  };

  const handleReadmeGeneration = async (data: ReadmeGenerationData) => {
    console.log('README generation requested:', data);
    // This would be handled by the parent component
  };

  const handleSkillAnalysis = async (data: SkillAnalysisData) => {
    console.log('Skill gap analysis requested:', data);
    // This would be handled by the parent component
  };

  const handleVersionHistory = async (recommendationId: number) => {
    try {
      const history = await apiClient.getVersionHistory(recommendationId);
      return history;
    } catch (error) {
      console.error('Failed to get version history:', error);
      throw error;
    }
  };

  const handleVersionComparison = async (
    recommendationId: number,
    versionA: number,
    versionB: number
  ) => {
    try {
      const comparison = await apiClient.compareVersions(
        recommendationId,
        versionA,
        versionB
      );
      return comparison;
    } catch (error) {
      console.error('Failed to compare versions:', error);
      throw error;
    }
  };

  const handleVersionRevert = async (
    recId: number,
    versionId: number,
    reason: string
  ): Promise<void> => {
    try {
      const data = { version_id: versionId, revert_reason: reason };
      await apiClient.revertVersion(recId, data);
    } catch (error) {
      console.error('Failed to revert version:', error);
      throw error;
    }
  };

  const handleMultiContributor = async (data: MultiContributorData) => {
    try {
      const result = await apiClient.generateMultiContributor(data);
      return result;
    } catch (error) {
      console.error(
        'Failed to generate multi-contributor recommendation:',
        error
      );
      throw error;
    }
  };

  return (
    <div className='container mx-auto p-6'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold mb-2'>Advanced Features</h1>
        <p className='text-lg text-muted-foreground'>
          Powerful new capabilities to enhance your LinkedIn recommendation
          workflow
        </p>
      </div>

      <AdvancedFeatures
        onKeywordRefine={handleKeywordRefine}
        onGenerateReadme={handleReadmeGeneration}
        onAnalyzeSkills={handleSkillAnalysis}
        onGetVersionHistory={handleVersionHistory}
        onCompareVersions={handleVersionComparison}
        onRevertVersion={handleVersionRevert}
        onGenerateMultiContributor={handleMultiContributor}
      />
    </div>
  );
}
