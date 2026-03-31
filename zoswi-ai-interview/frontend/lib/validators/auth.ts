import { z } from "zod";

const roles = ["candidate", "student", "recruiter"] as const;

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters")
});

export const signupSchema = loginSchema.extend({
  full_name: z.string().min(2, "Enter your full name"),
  role: z.enum(roles).default("candidate"),
  years_experience: z.union([z.literal(""), z.coerce.number().min(0).max(50)]).optional(),
  role_contact_email: z.string().email("Enter a valid role contact email").optional().or(z.literal("")),
  target_role: z.string().max(120).optional().or(z.literal("")),
  university_name: z.string().max(120).optional().or(z.literal("")),
  graduation_year: z.string().regex(/^\d{4}$/, "Graduation year must be 4 digits").optional().or(z.literal("")),
  degree_program: z.string().max(120).optional().or(z.literal("")),
  organization_name: z.string().max(120).optional().or(z.literal("")),
  recruiter_title: z.string().max(120).optional().or(z.literal("")),
  hiring_focus: z.string().max(160).optional().or(z.literal(""))
}).superRefine((value, ctx) => {
  if (value.role === "candidate") {
    if (value.years_experience === undefined || value.years_experience === "") {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["years_experience"],
        message: "Years of experience is required for candidate accounts"
      });
    }
  }

  if (value.role === "student") {
    if (!value.role_contact_email) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["role_contact_email"],
        message: "University email is required for student accounts"
      });
    }
    if (!value.university_name?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["university_name"],
        message: "University name is required for student accounts"
      });
    }
    if (!value.graduation_year?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["graduation_year"],
        message: "Graduation year is required for student accounts"
      });
    }
  }

  if (value.role === "recruiter") {
    if (!value.role_contact_email) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["role_contact_email"],
        message: "Recruiter email is required for recruiter accounts"
      });
    }
    if (!value.organization_name?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["organization_name"],
        message: "Organization name is required for recruiter accounts"
      });
    }
  }
});

export type LoginInput = z.infer<typeof loginSchema>;
export type SignupInput = z.infer<typeof signupSchema>;
