/**
 * Centralized Zod Validation Schemas
 *
 * This file contains all form validation schemas used across the application.
 * Import from here instead of defining schemas inline in components.
 *
 * @example
 * import { loginSchema, type LoginFormValues } from '~/lib/zod/schemas';
 */

import { z } from 'zod';

// ========== Auth Schemas ==========

/**
 * Login form validation schema
 */
export const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

/**
 * Registration form validation schema
 */
export const registerSchema = z
  .object({
    username: z
      .string()
      .min(3, 'Username must be at least 3 characters')
      .max(50, 'Username must be less than 50 characters')
      .regex(
        /^[a-zA-Z0-9_-]+$/,
        'Username can only contain letters, numbers, underscores, and hyphens'
      ),
    email: z.string().email('Please enter a valid email address'),
    password: z
      .string()
      .min(6, 'Password must be at least 6 characters')
      .max(100, 'Password must be less than 100 characters'),
    confirmPassword: z.string().min(1, 'Please confirm your password'),
  })
  .refine(data => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

export type RegisterFormValues = z.infer<typeof registerSchema>;

/**
 * Change password form validation schema
 */
export const changePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Current password is required'),
    newPassword: z
      .string()
      .min(6, 'New password must be at least 6 characters')
      .max(100, 'Password must be less than 100 characters'),
    confirmNewPassword: z.string().min(1, 'Please confirm your new password'),
  })
  .refine(data => data.newPassword === data.confirmNewPassword, {
    message: "Passwords don't match",
    path: ['confirmNewPassword'],
  })
  .refine(data => data.currentPassword !== data.newPassword, {
    message: 'New password must be different from current password',
    path: ['newPassword'],
  });

export type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;

// ========== Profile Schemas ==========

/**
 * Edit profile form validation schema
 */
export const editProfileSchema = z.object({
  fullName: z
    .string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name must be less than 100 characters')
    .optional()
    .or(z.literal('')),
  username: z
    .string()
    .min(3, 'Username must be at least 3 characters')
    .max(50, 'Username must be less than 50 characters')
    .regex(
      /^[a-zA-Z0-9_-]+$/,
      'Username can only contain letters, numbers, underscores, and hyphens'
    )
    .optional(),
  bio: z
    .string()
    .max(500, 'Bio must be less than 500 characters')
    .optional()
    .or(z.literal('')),
});

export type EditProfileFormValues = z.infer<typeof editProfileSchema>;

// ========== Recommendation Schemas ==========

/**
 * GitHub input validation (username or repository URL)
 */
export const githubInputSchema = z.object({
  input: z
    .string()
    .min(1, 'GitHub input is required')
    .refine(
      val => {
        // Valid formats: username, owner/repo, or GitHub URL
        const trimmed = val.trim();
        if (!trimmed) return false;

        // Username format
        if (/^[a-zA-Z0-9](?:[a-zA-Z0-9-]){0,38}$/.test(trimmed)) return true;

        // owner/repo format
        if (/^[a-zA-Z0-9-]+\/[a-zA-Z0-9._-]+$/.test(trimmed)) return true;

        // GitHub URL
        if (/^https?:\/\/(www\.)?github\.com\/[a-zA-Z0-9-]+/.test(trimmed))
          return true;

        return false;
      },
      {
        message:
          'Please enter a valid GitHub username, repository (owner/repo), or URL',
      }
    ),
});

export type GitHubInputFormValues = z.infer<typeof githubInputSchema>;

/**
 * Recommendation form validation schema
 */
export const recommendationFormSchema = z.object({
  githubInput: z.string().min(1, 'GitHub username or repository is required'),
  workingRelationship: z
    .string()
    .min(
      10,
      'Please describe your working relationship (at least 10 characters)'
    )
    .max(1000, 'Working relationship description is too long'),
  specificSkills: z
    .string()
    .max(500, 'Skills description is too long')
    .optional()
    .or(z.literal('')),
  timeWorkedTogether: z
    .string()
    .max(100, 'Time worked together is too long')
    .optional()
    .or(z.literal('')),
  notableAchievements: z
    .string()
    .max(1000, 'Achievements description is too long')
    .optional()
    .or(z.literal('')),
  recommendationType: z
    .enum(['professional', 'academic', 'personal'])
    .default('professional'),
  tone: z
    .enum(['professional', 'friendly', 'enthusiastic', 'formal'])
    .default('professional'),
  length: z.enum(['short', 'medium', 'long']).default('medium'),
});

export type RecommendationFormValues = z.infer<typeof recommendationFormSchema>;

// ========== API Key Schemas ==========

/**
 * Create API key form validation schema
 */
export const createApiKeySchema = z.object({
  name: z
    .string()
    .min(1, 'API key name is required')
    .max(100, 'Name must be less than 100 characters'),
  expiresInDays: z
    .number()
    .min(1, 'Expiry must be at least 1 day')
    .max(365, 'Expiry cannot exceed 365 days')
    .optional(),
});

export type CreateApiKeyFormValues = z.infer<typeof createApiKeySchema>;

// ========== Contact/Feedback Schemas ==========

/**
 * Contact form validation schema
 */
export const contactFormSchema = z.object({
  name: z
    .string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name is too long'),
  email: z.string().email('Please enter a valid email address'),
  subject: z
    .string()
    .min(5, 'Subject must be at least 5 characters')
    .max(200, 'Subject is too long'),
  message: z
    .string()
    .min(20, 'Message must be at least 20 characters')
    .max(5000, 'Message is too long'),
});

export type ContactFormValues = z.infer<typeof contactFormSchema>;
