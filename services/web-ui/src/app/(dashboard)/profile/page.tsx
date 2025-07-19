"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/auth-store";
import { useState } from "react";
import { User, Mail, Building, Calendar } from "lucide-react";

export default function ProfilePage() {
  const { user } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: user?.name || "",
    email: user?.email || "",
    company: user?.company || "",
  });

  const handleSave = async () => {
    // TODO: API 호출로 프로필 업데이트
    setIsEditing(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">프로필</h1>
        <p className="text-muted-foreground">
          계정 정보를 확인하고 수정할 수 있습니다
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>개인 정보</CardTitle>
            <CardDescription>
              프로필 정보를 관리합니다
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">
                <User className="inline h-4 w-4 mr-1" />
                이름
              </Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                disabled={!isEditing}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">
                <Mail className="inline h-4 w-4 mr-1" />
                이메일
              </Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                disabled
                className="bg-gray-50 dark:bg-gray-800"
              />
              <p className="text-xs text-muted-foreground">
                이메일은 변경할 수 없습니다
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="company">
                <Building className="inline h-4 w-4 mr-1" />
                회사
              </Label>
              <Input
                id="company"
                value={formData.company}
                onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                disabled={!isEditing}
              />
            </div>

            <div className="space-y-2">
              <Label>
                <Calendar className="inline h-4 w-4 mr-1" />
                가입일
              </Label>
              <Input
                value={user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : ""}
                disabled
                className="bg-gray-50 dark:bg-gray-800"
              />
            </div>

            <div className="flex gap-2 pt-4">
              {isEditing ? (
                <>
                  <Button onClick={handleSave}>저장</Button>
                  <Button variant="outline" onClick={() => setIsEditing(false)}>
                    취소
                  </Button>
                </>
              ) : (
                <Button onClick={() => setIsEditing(true)}>수정</Button>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>보안 설정</CardTitle>
            <CardDescription>
              계정 보안을 관리합니다
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="text-sm font-medium mb-2">비밀번호 변경</h4>
              <p className="text-sm text-muted-foreground mb-4">
                정기적으로 비밀번호를 변경하여 계정을 안전하게 보호하세요
              </p>
              <Button variant="outline">비밀번호 변경</Button>
            </div>

            <div className="pt-4">
              <h4 className="text-sm font-medium mb-2">2단계 인증</h4>
              <p className="text-sm text-muted-foreground mb-4">
                2단계 인증을 활성화하여 계정 보안을 강화하세요
              </p>
              <Button variant="outline">2단계 인증 설정</Button>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>계정 권한</CardTitle>
            <CardDescription>
              현재 계정의 권한 정보입니다
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">역할</h4>
                  <p className="text-sm text-muted-foreground">
                    {user?.role === 'admin' ? '관리자' : '일반 사용자'}
                  </p>
                </div>
                <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                  user?.role === 'admin' 
                    ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300'
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                }`}>
                  {user?.role?.toUpperCase()}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}