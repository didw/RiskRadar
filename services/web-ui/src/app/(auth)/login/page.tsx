"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertCircle, CheckCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useAuthStore } from "@/stores/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isLoading, error, clearError } = useAuthStore();
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  useEffect(() => {
    // 회원가입 성공 메시지 표시
    if (searchParams?.get('registered') === 'true') {
      setShowSuccessMessage(true);
      setTimeout(() => setShowSuccessMessage(false), 5000);
    }
    
    // 에러 클리어
    clearError();
  }, [searchParams, clearError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await login(formData);
      router.push("/");
    } catch (err) {
      // 에러는 store에서 처리됨
    }
  };

  return (
    <>
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold">RiskRadar</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          기업 리스크 모니터링 플랫폼
        </p>
      </div>

      <Card>
        <form onSubmit={handleSubmit}>
          <CardHeader>
            <CardTitle>로그인</CardTitle>
            <CardDescription>
              계정에 로그인하여 대시보드에 접속하세요
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {showSuccessMessage && (
              <Alert className="border-green-200 bg-green-50 text-green-800">
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>회원가입이 완료되었습니다. 로그인해주세요.</AlertDescription>
              </Alert>
            )}
            
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="email">이메일</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@company.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                autoComplete="email"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password">비밀번호</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                autoComplete="current-password"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-primary focus:ring-primary"
                />
                <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                  로그인 상태 유지
                </span>
              </label>
              
              <Link 
                href="/forgot-password" 
                className="text-sm text-primary hover:underline"
              >
                비밀번호 찾기
              </Link>
            </div>
          </CardContent>
          
          <CardFooter className="flex flex-col space-y-4">
            <Button 
              type="submit" 
              className="w-full" 
              disabled={isLoading}
            >
              {isLoading ? "로그인 중..." : "로그인"}
            </Button>
            
            <p className="text-center text-sm text-gray-600 dark:text-gray-400">
              계정이 없으신가요?{" "}
              <Link href="/register" className="text-primary hover:underline">
                회원가입
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
      
      <div className="text-center mt-4 text-sm text-gray-500">
        테스트 계정: admin@riskradar.ai / password
      </div>
    </>
  );
}