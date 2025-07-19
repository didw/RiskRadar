import { WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function OfflinePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center space-y-6 p-8">
        <WifiOff className="h-16 w-16 text-gray-400 mx-auto" />
        
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-gray-900">
            오프라인 상태입니다
          </h1>
          <p className="text-gray-600">
            인터넷 연결을 확인하고 다시 시도해주세요
          </p>
        </div>
        
        <Button 
          onClick={() => window.location.reload()}
          className="mt-6"
        >
          다시 시도
        </Button>
      </div>
    </div>
  );
}