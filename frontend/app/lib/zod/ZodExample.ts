import { z } from 'zod';

/**
 * Example Zod schema for a user profile.
 * Validates name, email, and age fields.
 */
export const userProfileSchema = z.object({
  name: z
    .string()
    .min(2, { message: 'Name must be at least 2 characters long.' })
    .max(50, { message: 'Name must be at most 50 characters long.' }),
  email: z.string().email({ message: 'Invalid email address.' }),
  age: z
    .number()
    .int({ message: 'Age must be an integer.' })
    .min(0, { message: 'Age must be a positive number.' })
    .max(120, { message: 'Age must be less than or equal to 120.' }),
});

// Example usage:
// userProfileSchema.parse({ name: "Alice", email: "alice@example.com", age: 30 });

/**
 * Unit tests for userProfileSchema using Jest.
 * Place in __tests__/ZodExample.test.ts if using Jest.
 */
if (process.env.NODE_ENV === 'test') {
  // These are illustrative; move to a test file in real projects.
  describe('userProfileSchema', () => {
    it('accepts valid data', () => {
      expect(() =>
        userProfileSchema.parse({
          name: 'Alice',
          email: 'alice@example.com',
          age: 30,
        })
      ).not.toThrow();
    });

    it('rejects invalid email', () => {
      expect(() =>
        userProfileSchema.parse({
          name: 'Bob',
          email: 'not-an-email',
          age: 25,
        })
      ).toThrow(/Invalid email address/);
    });

    it('rejects short name', () => {
      expect(() =>
        userProfileSchema.parse({
          name: 'A',
          email: 'a@example.com',
          age: 25,
        })
      ).toThrow(/at least 2 characters/);
    });

    it('rejects negative age', () => {
      expect(() =>
        userProfileSchema.parse({
          name: 'Charlie',
          email: 'charlie@example.com',
          age: -5,
        })
      ).toThrow(/positive number/);
    });
  });
}
