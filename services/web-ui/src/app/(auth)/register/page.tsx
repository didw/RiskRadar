"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertCircle, Check } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useAuthStore } from "@/stores/auth-store";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading, error, clearError } = useAuthStore();
  
  useEffect(() => {
    clearError();
  }, [clearError]);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    password: "",
    confirmPassword: "",
  });

  const passwordRequirements = [
    { regex: /.{8,}/, text: "최소 8자 이상" },
    { regex: /[A-Z]/, text: "대문자 포함" },
    { regex: /[a-z]/, text: "소문자 포함" },
    { regex: /[0-9]/, text: "숫자 포함" },
  ];

  const checkPasswordStrength = (password: string) => {
    return passwordRequirements.map(req => ({
      ...req,
      isValid: req.regex.test(password)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 비밀번호 확인
    if (formData.password !== formData.confirmPassword) {
      alert("비밀번호가 일치하지 않습니다.");
      return;
    }

    // 비밀번호 강도 체크
    const passwordChecks = checkPasswordStrength(formData.password);
    if (!passwordChecks.every(check => check.isValid)) {
      alert("비밀번호가 보안 요구사항을 충족하지 않습니다.");
      return;
    }

    try {
      await register({
        name: formData.name,
        email: formData.email,
        company: formData.company,
        password: formData.password,
      });
      
      // 회원가입 성공 시 로그인 페이지로 이동
      router.push("/login?registered=true");
    } catch (err) {
      // 에러는 store에서 처리됨
    }
  };

  return (
    <>
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold">RiskRadar</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          새 계정을 만들어 시작하세요
        </p>
      </div>

      <Card>
        <form onSubmit={handleSubmit}>
          <CardHeader>
            <CardTitle>회원가입</CardTitle>
            <CardDescription>
              RiskRadar 계정을 생성하여 기업 리스크를 모니터링하세요
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="name">이름</Label>
              <Input
                id="name"
                type="text"
                placeholder="홍길동"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                autoComplete="name"
              />
            </div>
            
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
              <Label htmlFor="company">회사명</Label>
              <Input
                id="company"
                type="text"
                placeholder="회사명을 입력하세요"
                value={formData.company}
                onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                required
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
                autoComplete="new-password"
              />
              
              {formData.password && (
                <div className="mt-2 space-y-1">
                  {checkPasswordStrength(formData.password).map((req, idx) => (
                    <div key={idx} className={`flex items-center text-xs ${req.isValid ? 'text-green-600' : 'text-gray-400'}`}>
                      {req.isValid ? <Check className="h-3 w-3 mr-1" /> : <div className="h-3 w-3 mr-1" />}
                      {req.text}
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">비밀번호 확인</Label>
              <Input
                id="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                required
                autoComplete="new-password"
              />
            </div>
            
            <div className="flex items-start">
              <input
                id="terms"
                type="checkbox"
                className="mt-1 rounded border-gray-300 text-primary focus:ring-primary"
                required
              />
              <label htmlFor="terms" className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                <Link href="/terms" className="text-primary hover:underline">이용약관</Link> 및{" "}
                <Link href="/privacy" className="text-primary hover:underline">개인정보처리방침</Link>에
                동의합니다
              </label>
            </div>
          </CardContent>
          
          <CardFooter className="flex flex-col space-y-4">
            <Button 
              type="submit" 
              className="w-full" 
              disabled={isLoading}
            >
              {isLoading ? "계정 생성 중..." : "계정 생성"}
            </Button>
            
            <p className="text-center text-sm text-gray-600 dark:text-gray-400">
              이미 계정이 있으신가요?{" "}
              <Link href="/login" className="text-primary hover:underline">
                로그인
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </>
  );
}