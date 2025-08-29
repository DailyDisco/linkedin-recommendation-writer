import React from 'react';
import { AdvancedFeatures } from './AdvancedFeatures';
import { apiClient } from '../../lib/api';

// Example of how to use the AdvancedFeatures component
export const AdvancedFeaturesExample: React.FC = () => {
  // API integration functions
  const handleKeywordRefine = async (data: any) => {
    console.log('Keyword refinement requested:', data);
    // This would be handled by the parent component
  };

  const handleReadmeGeneration = async (data: any) => {
    console.log('README generation requested:', data);
    // This would be handled by the parent component
  };

  const handleSkillAnalysis = async (data: any) => {
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
    recommendationId: number,
    data: { version_id: number; revert_reason?: string }
  ) => {
    try {
      const result = await apiClient.revertVersion(recommendationId, data);
      return result;
    } catch (error) {
      console.error('Failed to revert version:', error);
      throw error;
    }
  };

  const handleMultiContributor = async (data: any) => {
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
      <h1 className='text-3xl font-bold mb-6'>Advanced Features Dashboard</h1>

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
};
