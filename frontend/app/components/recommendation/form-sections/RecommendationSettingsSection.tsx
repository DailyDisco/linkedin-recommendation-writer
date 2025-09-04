import React from 'react';
import { Label } from '@/components/ui/label';

interface RecommendationSettingsSectionProps {
  recommendationType:
    | 'professional'
    | 'technical'
    | 'leadership'
    | 'academic'
    | 'personal';
  tone: 'professional' | 'friendly' | 'formal' | 'casual';
  length: 'short' | 'medium' | 'long';
  forceRefresh?: boolean;
  onChange: (field: string, value: string | boolean) => void;
}

export const RecommendationSettingsSection: React.FC<
  RecommendationSettingsSectionProps
> = ({ recommendationType, tone, length, forceRefresh = false, onChange }) => {
  return (
    <div className='bg-gray-50 p-4 rounded-lg space-y-4'>
      <h3 className='font-medium text-gray-900'>Recommendation Settings</h3>

      <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
        <div>
          <Label
            htmlFor='rec-type'
            className='block text-sm font-medium text-gray-700 mb-1'
          >
            Type
          </Label>
          <p className='text-xs text-gray-500 mb-2'>
            Focus area of the recommendation
          </p>
          <select
            id='rec-type'
            className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
            value={recommendationType}
            onChange={e =>
              onChange(
                'recommendation_type',
                e.target
                  .value as RecommendationSettingsSectionProps['recommendationType']
              )
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
          <Label
            htmlFor='rec-tone'
            className='block text-sm font-medium text-gray-700 mb-1'
          >
            Tone
          </Label>
          <p className='text-xs text-gray-500 mb-2'>Writing style and voice</p>
          <select
            id='rec-tone'
            className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
            value={tone}
            onChange={e =>
              onChange(
                'tone',
                e.target.value as RecommendationSettingsSectionProps['tone']
              )
            }
          >
            <option value='professional'>Professional</option>
            <option value='friendly'>Friendly</option>
            <option value='formal'>Formal</option>
            <option value='casual'>Casual</option>
          </select>
        </div>

        <div>
          <Label
            htmlFor='rec-length'
            className='block text-sm font-medium text-gray-700 mb-1'
          >
            Length
          </Label>
          <p className='text-xs text-gray-500 mb-2'>
            Word count of the recommendation
          </p>
          <select
            id='rec-length'
            className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
            value={length}
            onChange={e =>
              onChange(
                'length',
                e.target.value as RecommendationSettingsSectionProps['length']
              )
            }
          >
            <option value='short'>Short</option>
            <option value='medium'>Medium</option>
            <option value='long'>Long</option>
          </select>
        </div>
      </div>

      {/* Force Refresh Option */}
      <div className='border-t pt-4'>
        <div className='flex items-center space-x-2'>
          <input
            type='checkbox'
            id='force-refresh'
            checked={forceRefresh}
            onChange={e => onChange('force_refresh', e.target.checked)}
            className='h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
          />
          <Label
            htmlFor='force-refresh'
            className='text-sm font-medium text-gray-700'
          >
            Force fresh generation
          </Label>
        </div>
        <p className='text-xs text-gray-500 mt-1'>
          Bypass cached results and generate a completely new recommendation
        </p>
      </div>
    </div>
  );
};
