import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Lock, Mail, Loader2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import ErrorBoundary from '../../components/ui/error-boundary';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../../components/ui/card';
import { apiClient } from '../../services/api';
import { useAuth } from '../../hooks/useAuth';
import { Link, useNavigate } from 'react-router';

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  const onSubmit = async (values: LoginFormValues) => {
    setLoading(true);
    try {
      const response = await apiClient.login({
        username: values.username,
        password: values.password,
      });
      await login(response.access_token);
      toast.success('Welcome back! You have been logged in successfully.');
      navigate('/generate'); // Redirect to generate page after successful login
    } catch (err: unknown) {
      console.error('Login failed:', err);
      const errorMessage =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response
              ?.data?.detail
          : 'Invalid username or password';
      toast.error(
        errorMessage ||
          'Login failed. Please check your credentials and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <ErrorBoundary>
      <div className='flex min-h-full flex-1 flex-col justify-center px-6 py-12 lg:px-8'>
        <div className='sm:mx-auto sm:w-full sm:max-w-sm'>
          <Card className='w-full max-w-sm mx-auto'>
            <CardHeader>
              <CardTitle className='text-center text-2xl font-bold leading-9 tracking-tight text-gray-900'>
                Sign in to your account
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className='space-y-6'
              >
                <div>
                  <label
                    htmlFor='username'
                    className='block text-sm font-medium leading-6 text-gray-900'
                  >
                    Username
                  </label>
                  <div className='relative mt-2 rounded-md shadow-sm'>
                    <div className='pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3'>
                      <Mail
                        className='h-5 w-5 text-gray-400'
                        aria-hidden='true'
                      />
                    </div>
                    <Input
                      id='username'
                      type='text'
                      autoComplete='username'
                      {...form.register('username')}
                      className='block w-full rounded-md border-0 py-1.5 pl-10 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6'
                    />
                  </div>
                  {form.formState.errors.username && (
                    <p className='mt-2 text-sm text-red-600'>
                      {form.formState.errors.username.message}
                    </p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor='password'
                    className='block text-sm font-medium leading-6 text-gray-900'
                  >
                    Password
                  </label>
                  <div className='relative mt-2 rounded-md shadow-sm'>
                    <div className='pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3'>
                      <Lock
                        className='h-5 w-5 text-gray-400'
                        aria-hidden='true'
                      />
                    </div>
                    <Input
                      id='password'
                      type='password'
                      autoComplete='current-password'
                      {...form.register('password')}
                      className='block w-full rounded-md border-0 py-1.5 pl-10 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6'
                    />
                  </div>
                  {form.formState.errors.password && (
                    <p className='mt-2 text-sm text-red-600'>
                      {form.formState.errors.password.message}
                    </p>
                  )}
                </div>



                <div>
                  <Button
                    type='submit'
                    className='flex w-full justify-center rounded-md bg-blue-600 px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-blue-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600'
                    disabled={loading}
                  >
                    {loading ? (
                      <Loader2 className='mr-2 h-4 w-4 animate-spin' />
                    ) : null}
                    Sign in
                  </Button>
                </div>
              </form>

              <p className='mt-10 text-center text-sm text-gray-500'>
                Not a member?{' '}
                <Link
                  to='/register'
                  className='font-semibold leading-6 text-blue-600 hover:text-blue-500'
                >
                  Sign up for free
                </Link>
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </ErrorBoundary>
  );
}
