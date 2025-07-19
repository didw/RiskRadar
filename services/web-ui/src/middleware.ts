import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// 공개 경로 목록
const publicPaths = ['/login', '/register', '/forgot-password', '/terms', '/privacy'];

// API 경로 목록
const apiPaths = ['/api'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // API 경로는 별도 처리
  if (apiPaths.some(path => pathname.startsWith(path))) {
    return NextResponse.next();
  }
  
  // 공개 경로는 통과
  if (publicPaths.some(path => pathname.startsWith(path))) {
    return NextResponse.next();
  }
  
  // 토큰 확인 (쿠키 또는 헤더에서)
  const token = request.cookies.get('auth-token')?.value || 
                request.headers.get('authorization')?.replace('Bearer ', '');
  
  // 인증되지 않은 사용자는 로그인 페이지로 리다이렉트
  if (!token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }
  
  // TODO: 토큰 유효성 검증 로직 추가
  // 현재는 토큰 존재 여부만 확인
  
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};