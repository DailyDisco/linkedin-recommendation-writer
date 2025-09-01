import React from 'react';
import { CheckCircle, Eye, EyeOff, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { RecommendationOption } from '../../types/index';

interface RecommendationOptionsCardProps {
    option: RecommendationOption;
    isViewingFull: boolean;
    onViewMore: () => void;
    onSelect: () => void;
    isCreating: boolean;
}

export const RecommendationOptionsCard: React.FC<RecommendationOptionsCardProps> = ({
    option,
    isViewingFull,
    onViewMore,
    onSelect,
    isCreating
}) => {
    return (
        <div className='border-2 border-gray-200 rounded-lg p-6 hover:border-blue-300 hover:shadow-md transition-all duration-200'>
            <div className='flex items-start justify-between mb-4'>
                <div className='flex-1'>
                    <h4 className='text-lg font-semibold text-gray-900 mb-1'>
                        {option.title || option.name}
                    </h4>
                    <div className='flex items-center space-x-4 text-sm text-gray-600'>
                        <span className='flex items-center space-x-1'>
                            <span className='font-medium'>Focus:</span>
                            <Badge variant='secondary' className='text-xs'>
                                {option.focus?.replace('_', ' ') || 'General'}
                            </Badge>
                        </span>
                        <span className='flex items-center space-x-1'>
                            <span className='font-medium'>Words:</span>
                            <span>{option.word_count}</span>
                        </span>
                    </div>
                </div>
            </div>

            <div className='bg-gray-50 p-4 rounded-md mb-4 border-l-4 border-blue-200'>
                <p className='text-gray-900 leading-relaxed'>
                    {isViewingFull
                        ? option.content
                        : option.content.length > 400
                            ? option.content.substring(0, 400) + '...'
                            : option.content}
                </p>
            </div>

            {option.explanation && (
                <div className='bg-blue-50 p-3 rounded-md mb-4 border border-blue-200'>
                    <p className='text-sm text-blue-800 italic'>
                        {option.explanation}
                    </p>
                </div>
            )}

            <div className='flex space-x-3'>
                <Button
                    variant='outline'
                    size='sm'
                    onClick={onViewMore}
                    className='flex-1'
                >
                    {isViewingFull ? (
                        <>
                            <EyeOff className='w-4 h-4 mr-2' />
                            Show Less
                        </>
                    ) : (
                        <>
                            <Eye className='w-4 h-4 mr-2' />
                            Read Full
                        </>
                    )}
                </Button>
                <Button
                    onClick={onSelect}
                    disabled={isCreating}
                    className='flex-1 bg-blue-600 hover:bg-blue-700'
                >
                    {isCreating ? (
                        <>
                            <Loader2 className='w-4 h-4 mr-2 animate-spin' />
                            Creating...
                        </>
                    ) : (
                        <>
                            <CheckCircle className='w-4 h-4 mr-2' />
                            Select This
                        </>
                    )}
                </Button>
            </div>
        </div>
    );
};
