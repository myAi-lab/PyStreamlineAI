import { z } from "zod";

export const profileSchema = z.object({
  headline: z.string().max(255).optional().nullable(),
  years_experience: z.coerce.number().min(0).max(50).optional().nullable(),
  target_roles: z.array(z.string().min(2).max(80)),
  location: z.string().max(255).optional().nullable(),
  role_contact_email: z.string().email().optional().nullable(),
  role_profile: z.record(z.string()).default({})
});

export type ProfileInput = z.infer<typeof profileSchema>;
