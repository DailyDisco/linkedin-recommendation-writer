import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';
import { apiClient } from '../../services/api';
import * as z from 'zod';
import { FieldError } from '@/components/ui/form-error';

const profileSchema = z.object({
  full_name: z
    .string()
    .min(1, 'Full name is required')
    .max(100, 'Full name must not exceed 100 characters'),
  username: z
    .string()
    .min(3, 'Username must be at least 3 characters')
    .max(50, 'Username must not exceed 50 characters')
    .regex(
      /^[a-zA-Z0-9_]+$/,
      'Username can only contain letters, numbers, and underscores'
    ),
  email: z.string().email('Invalid email format'), // Display-only, not editable for now
  bio: z
    .string()
    .max(500, 'Bio must not exceed 500 characters')
    .optional()
    .or(z.literal('')), // Allow empty string for optional
});

type ProfileFormValues = z.infer<typeof profileSchema>;

interface EditProfileFormProps {
  onSave: () => void;
  onCancel: () => void;
}

export const EditProfileForm: React.FC<EditProfileFormProps> = ({
  onSave,
  onCancel,
}) => {
  const { userDetails, fetchUserDetails } = useAuth();
  const [formData, setFormData] = useState<Partial<ProfileFormValues>>({
    full_name: '',
    username: '',
    email: '',
    bio: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (userDetails) {
      setFormData({
        full_name: userDetails.full_name || '',
        username: userDetails.username || '',
        email: userDetails.email || '',
        bio: userDetails.bio || '', // Assuming bio is part of userDetails
      });
    }
  }, [userDetails]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { id, value } = e.target;
    setFormData(prev => ({ ...prev, [id]: value }));
    if (errors[id]) {
      setErrors(prev => {
        delete prev[id];
        return { ...prev };
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors({});

    if (!userDetails?.id) {
      toast.error('User not authenticated. Please log in again.');
      setIsLoading(false);
      return;
    }

    // Check if we have a valid access token
    const authStorage = localStorage.getItem('auth-storage');
    if (!authStorage) {
      toast.error('Authentication session expired. Please log in again.');
      setIsLoading(false);
      return;
    }

    try {
      const parsed = JSON.parse(authStorage);
      const accessToken = parsed?.state?.accessToken;
      if (!accessToken) {
        toast.error('Authentication token not found. Please log in again.');
        setIsLoading(false);
        return;
      }
    } catch (error) {
      console.error('Failed to parse auth storage:', error);
      toast.error('Authentication session corrupted. Please log in again.');
      setIsLoading(false);
      return;
    }

    try {
      profileSchema.parse(formData);

      // Only send fields that have values and are different from current values
      const updateData: Partial<
        Pick<ProfileFormValues, 'full_name' | 'username' | 'bio'>
      > = {};
      if (formData.full_name && formData.full_name !== userDetails.full_name) {
        updateData.full_name = formData.full_name;
      }
      if (formData.username && formData.username !== userDetails.username) {
        updateData.username = formData.username;
      }
      if (formData.bio !== undefined && formData.bio !== userDetails.bio) {
        updateData.bio = formData.bio;
      }

      if (Object.keys(updateData).length === 0) {
        toast.info('No changes to update');
        return;
      }

      await apiClient.updateUserProfile(userDetails.id, updateData);

      toast.success('Profile updated successfully!');
      await fetchUserDetails(true); // Refresh user details in auth context
      onSave();
    } catch (err) {
      if (err instanceof z.ZodError) {
        const newErrors: Record<string, string> = {};
        for (const issue of err.errors) {
          if (issue.path.length > 0) {
            newErrors[issue.path[0]] = issue.message;
          }
        }
        setErrors(newErrors);
      } else {
        console.error('Profile update failed:', err);
        // Try to get more specific error message from the API response
        const error = err as {
          response?: { data?: { detail?: string; message?: string } };
          message?: string;
        };
        const errorMessage =
          error?.response?.data?.detail ||
          error?.response?.data?.message ||
          error?.message ||
          'Failed to update profile. Please try again.';
        toast.error(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className='space-y-6 p-4'>
      <div className='grid gap-2'>
        <Label htmlFor='full_name'>Full Name</Label>
        <Input
          id='full_name'
          value={formData.full_name || ''}
          onChange={handleChange}
          placeholder='Your full name'
        />
        <FieldError error={errors.full_name} touched={!!errors.full_name} />
      </div>

      <div className='grid gap-2'>
        <Label htmlFor='username'>Username</Label>
        <Input
          id='username'
          value={formData.username || ''}
          onChange={handleChange}
          placeholder='Your unique username'
        />
        <FieldError error={errors.username} touched={!!errors.username} />
      </div>

      <div className='grid gap-2'>
        <Label htmlFor='email'>Email</Label>
        <Input
          id='email'
          value={formData.email || ''}
          disabled // Email is typically not changed via profile edit form
        />
        <p className='text-xs text-muted-foreground'>
          Email cannot be changed directly from here.
        </p>
      </div>

      <div className='grid gap-2'>
        <Label htmlFor='bio'>Bio</Label>
        <Textarea
          id='bio'
          value={formData.bio || ''}
          onChange={handleChange}
          placeholder='A short bio about yourself (optional)'
          rows={3}
        />
        <FieldError error={errors.bio} touched={!!errors.bio} />
      </div>

      <div className='flex justify-end gap-3'>
        <Button
          type='button'
          variant='outline'
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button type='submit' disabled={isLoading}>
          {isLoading && <Loader2 className='mr-2 h-4 w-4 animate-spin' />}
          Save Changes
        </Button>
      </div>
    </form>
  );
};
