import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { apiClient } from '../../services/api';
import { Loader2 } from 'lucide-react';

const changePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Current password is required'),
    newPassword: z
      .string()
      .min(8, 'New password must be at least 8 characters long')
      .regex(/[a-z]/, 'New password must contain at least one lowercase letter')
      .regex(/[A-Z]/, 'New password must contain at least one uppercase letter')
      .regex(/[0-9]/, 'New password must contain at least one number')
      .regex(
        /[^a-zA-Z0-9]/,
        'New password must contain at least one special character'
      ),
    confirmNewPassword: z.string().min(1, 'Confirm new password is required'),
  })
  .refine(data => data.newPassword === data.confirmNewPassword, {
    message: 'New passwords do not match',
    path: ['confirmNewPassword'],
  });

type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;

interface ChangePasswordFormProps {
  onSave: () => void;
  onCancel: () => void;
}

export const ChangePasswordForm: React.FC<ChangePasswordFormProps> = ({
  onSave,
  onCancel,
}) => {
  const [isLoading, setIsLoading] = React.useState(false);

  const form = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      currentPassword: '',
      newPassword: '',
      confirmNewPassword: '',
    },
  });

  const onSubmit = async (values: ChangePasswordFormValues) => {
    setIsLoading(true);
    try {
      await apiClient.changePassword({
        current_password: values.currentPassword,
        new_password: values.newPassword,
      });
      toast.success('Password updated successfully!');
      onSave();
    } catch (error) {
      console.error('Failed to change password:', error);
      toast.error('Failed to update password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className='space-y-4'>
        <FormField
          control={form.control}
          name='currentPassword'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Current Password</FormLabel>
              <FormControl>
                <Input type='password' {...field} disabled={isLoading} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name='newPassword'
          render={({ field }) => (
            <FormItem>
              <FormLabel>New Password</FormLabel>
              <FormControl>
                <Input type='password' {...field} disabled={isLoading} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name='confirmNewPassword'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Confirm New Password</FormLabel>
              <FormControl>
                <Input type='password' {...field} disabled={isLoading} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <div className='flex justify-end gap-2'>
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
            Change Password
          </Button>
        </div>
      </form>
    </Form>
  );
};
