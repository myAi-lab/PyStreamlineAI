import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const protectedPrefix = "/dashboard";

export function middleware(request: NextRequest) {
  if (!request.nextUrl.pathname.startsWith(protectedPrefix)) {
    return NextResponse.next();
  }

  const token = request.cookies.get("zoswi_access_token")?.value;
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"]
};

