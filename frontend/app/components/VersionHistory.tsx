import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Clock, RotateCcw, Eye, GitBranch } from 'lucide-react';
import { format } from 'date-fns';

interface VersionDifference {
  changed: boolean;
  version_a: string | number;
  version_b: string | number;
}

interface Version {
  id: number;
  version_number: number;
  change_type: string;
  change_description: string | null;
  confidence_score: number;
  word_count: number;
  created_at: string;
  created_by: string | null;
}

interface VersionHistoryProps {
  recommendationId: number;
  onGetHistory: (id: number) => Promise<{
    recommendation_id: number;
    total_versions: number;
    current_version: number;
    versions: Array<{
      id: number;
      version_number: number;
      change_type: string;
      change_description: string | null;
      confidence_score: number;
      word_count: number;
      created_at: string;
      created_by: string | null;
    }>;
  }>;
  onCompareVersions: (
    recId: number,
    versionA: number,
    versionB: number
  ) => Promise<{
    version_a: Record<string, unknown>;
    version_b: Record<string, unknown>;
    differences: Record<string, unknown>;
  }>;
  onRevertToVersion: (
    recId: number,
    versionId: number,
    reason: string
  ) => Promise<void>;
}

const getChangeTypeColor = (type: string) => {
  switch (type.toLowerCase()) {
    case 'created':
      return 'bg-green-500';
    case 'refined':
      return 'bg-blue-500';
    case 'keyword_refinement':
      return 'bg-purple-500';
    case 'reverted':
      return 'bg-orange-500';
    case 'manual_edit':
      return 'bg-gray-500';
    default:
      return 'bg-gray-500';
  }
};

const getChangeTypeLabel = (type: string) => {
  switch (type.toLowerCase()) {
    case 'created':
      return 'Created';
    case 'refined':
      return 'Refined';
    case 'keyword_refinement':
      return 'Keyword Refined';
    case 'reverted':
      return 'Reverted';
    case 'manual_edit':
      return 'Manual Edit';
    default:
      return type;
  }
};

export const VersionHistory: React.FC<VersionHistoryProps> = ({
  recommendationId,
  onGetHistory,
  onCompareVersions,
  onRevertToVersion,
}) => {
  const [history, setHistory] = useState<Awaited<
    ReturnType<VersionHistoryProps['onGetHistory']>
  > | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedVersions, setSelectedVersions] = useState<number[]>([]);
  const [comparison, setComparison] = useState<Awaited<
    ReturnType<VersionHistoryProps['onCompareVersions']>
  > | null>(null);
  const [revertVersion, setRevertVersion] = useState<number | null>(null);
  const [revertReason, setRevertReason] = useState('');

  const loadHistory = useCallback(async () => {
    try {
      const result = await onGetHistory(recommendationId);
      setHistory(result);
    } catch (error) {
      console.error('Failed to load version history:', error);
    } finally {
      setLoading(false);
    }
  }, [onGetHistory, recommendationId]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleCompare = async () => {
    if (selectedVersions.length !== 2) return;

    try {
      const result = await onCompareVersions(
        recommendationId,
        selectedVersions[0],
        selectedVersions[1]
      );
      setComparison(result);
    } catch (error) {
      console.error('Failed to compare versions:', error);
    }
  };

  const handleRevert = async () => {
    if (!revertVersion || !revertReason.trim()) return;

    try {
      await onRevertToVersion(recommendationId, revertVersion, revertReason);
      setRevertVersion(null);
      setRevertReason('');
      await loadHistory(); // Reload history
    } catch (error) {
      console.error('Failed to revert version:', error);
    }
  };

  const toggleVersionSelection = (versionId: number) => {
    setSelectedVersions(prev => {
      if (prev.includes(versionId)) {
        return prev.filter(id => id !== versionId);
      } else if (prev.length < 2) {
        return [...prev, versionId];
      } else {
        return [prev[1], versionId]; // Replace first with new, keep second
      }
    });
  };

  if (loading) {
    return (
      <Card>
        <CardContent className='p-6'>
          <div className='text-center'>Loading version history...</div>
        </CardContent>
      </Card>
    );
  }

  if (!history) {
    return (
      <Card>
        <CardContent className='p-6'>
          <div className='text-center text-muted-foreground'>
            Failed to load version history
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className='space-y-6'>
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <Clock className='w-5 h-5' />
            Version History
          </CardTitle>
          <CardDescription>
            Track changes and manage versions of your recommendation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className='flex items-center justify-between mb-4'>
            <div className='text-sm text-muted-foreground'>
              {history.total_versions} versions • Current: v
              {history.current_version}
            </div>
            <div className='flex gap-2'>
              {selectedVersions.length === 2 && (
                <Button variant='outline' size='sm' onClick={handleCompare}>
                  <Eye className='w-4 h-4 mr-2' />
                  Compare Selected
                </Button>
              )}
            </div>
          </div>

          <div className='space-y-3'>
            {history.versions.map((version: Version) => (
              <div key={version.id} className='border rounded-lg p-4'>
                <div className='flex items-center justify-between'>
                  <div className='flex items-center gap-3'>
                    <input
                      type='checkbox'
                      checked={selectedVersions.includes(version.id)}
                      onChange={() => toggleVersionSelection(version.id)}
                      className='rounded'
                    />
                    <div>
                      <div className='flex items-center gap-2'>
                        <span className='font-semibold'>
                          v{version.version_number}
                        </span>
                        <Badge
                          className={getChangeTypeColor(version.change_type)}
                        >
                          {getChangeTypeLabel(version.change_type)}
                        </Badge>
                        {version.version_number === history.current_version && (
                          <Badge variant='outline'>Current</Badge>
                        )}
                      </div>
                      {version.change_description && (
                        <p className='text-sm text-muted-foreground mt-1'>
                          {version.change_description}
                        </p>
                      )}
                      <div className='flex items-center gap-4 text-xs text-muted-foreground mt-2'>
                        <span>
                          {format(
                            new Date(version.created_at),
                            'MMM dd, yyyy HH:mm'
                          )}
                        </span>
                        <span>Confidence: {version.confidence_score}%</span>
                        <span>{version.word_count} words</span>
                        {version.created_by && (
                          <span>by {version.created_by}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {version.version_number !== history.current_version && (
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button
                          variant='outline'
                          size='sm'
                          onClick={() => {
                            setRevertVersion(version.id);
                            setRevertReason('');
                          }}
                        >
                          <RotateCcw className='w-4 h-4 mr-2' />
                          Revert
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>
                            Revert to Version {version.version_number}
                          </DialogTitle>
                          <DialogDescription>
                            This will create a new version based on v
                            {version.version_number} and make it the current
                            version.
                          </DialogDescription>
                        </DialogHeader>
                        <div className='space-y-4'>
                          <div>
                            <Label htmlFor='revert-reason'>
                              Reason for reverting
                            </Label>
                            <Textarea
                              id='revert-reason'
                              value={revertReason}
                              onChange={e => setRevertReason(e.target.value)}
                              placeholder="Explain why you're reverting to this version..."
                              rows={3}
                            />
                          </div>
                          <div className='flex justify-end gap-2'>
                            <Button variant='outline' onClick={() => {}}>
                              Cancel
                            </Button>
                            <Button
                              onClick={handleRevert}
                              disabled={!revertReason.trim()}
                            >
                              Revert
                            </Button>
                          </div>
                        </div>
                      </DialogContent>
                    </Dialog>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Version Comparison */}
      {comparison && (
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <GitBranch className='w-5 h-5' />
              Version Comparison
            </CardTitle>
            <CardDescription>
              Comparing v{comparison.version_a.version_number} ↔ v
              {comparison.version_b.version_number}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className='grid grid-cols-2 gap-6'>
              {/* Version A */}
              <div className='space-y-3'>
                <h3 className='font-semibold'>
                  Version {comparison.version_a.version_number}
                </h3>
                <div className='text-sm space-y-2'>
                  <div>
                    Confidence: {comparison.version_a.confidence_score}%
                  </div>
                  <div>Words: {comparison.version_a.word_count}</div>
                  <div>Type: {comparison.version_a.change_type}</div>
                </div>
              </div>

              {/* Version B */}
              <div className='space-y-3'>
                <h3 className='font-semibold'>
                  Version {comparison.version_b.version_number}
                </h3>
                <div className='text-sm space-y-2'>
                  <div>
                    Confidence: {comparison.version_b.confidence_score}%
                  </div>
                  <div>Words: {comparison.version_b.word_count}</div>
                  <div>Type: {comparison.version_b.change_type}</div>
                </div>
              </div>
            </div>

            {/* Differences */}
            {Object.keys(comparison.differences).length > 0 && (
              <div className='mt-6'>
                <h4 className='font-semibold mb-3'>Key Differences</h4>
                <div className='space-y-2'>
                  {Object.entries(comparison.differences).map(
                    ([key, diff]: [string, VersionDifference]) => (
                      <div
                        key={key}
                        className='flex items-center gap-2 p-2 bg-muted rounded'
                      >
                        <Badge variant='outline'>
                          {key.replace(/_/g, ' ')}
                        </Badge>
                        <span className='text-sm'>
                          {diff.changed
                            ? 'Changed'
                            : `${diff.version_a} → ${diff.version_b}`}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};
