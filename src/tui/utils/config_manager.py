"""설정 관리자"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

from ...config import Config


class ConfigManager:
    """TUI 설정 관리자"""
    
    def __init__(self):
        self.config_file = Config.BASE_PATH / "tui_config.json"
        self.env_file = Path(".env")
    
    def get_api_keys(self) -> List[Dict[str, Any]]:
        """저장된 API 키 목록 조회 (.env 파일 기반)"""
        try:
            keys = []
            
            # .env 파일에서 현재 키 읽기
            current_openai_key = Config.OPENAI_API_KEY
            if current_openai_key:
                keys.append({
                    "name": "OpenAI API Key",
                    "value": current_openai_key,
                    "env_key": "OPENAI_API_KEY",
                    "status": "활성",
                    "last_validated": self._get_last_validation("OPENAI_API_KEY")
                })
            
            # JSON 파일에서 추가 키 정보 읽기 (메타데이터)
            config_data = self.load_config_file()
            additional_keys = config_data.get("api_keys", [])
            
            for key_info in additional_keys:
                # 중복 방지 (OPENAI_API_KEY는 이미 추가됨)
                if key_info.get("env_key") != "OPENAI_API_KEY":
                    keys.append(key_info)
            
            return keys
        except Exception:
            return []
    
    def save_api_key(self, name: str, value: str) -> bool:
        """API 키 저장 (.env 파일 기반)"""
        try:
            # 키 이름을 환경변수명으로 변환
            if name == "OpenAI API Key":
                env_key = "OPENAI_API_KEY"
            else:
                env_key = name.upper().replace(" ", "_").replace("-", "_")
            
            # .env 파일 업데이트
            self.update_env_file(env_key, value)
            
            # 메타데이터만 JSON에 저장 (실제 키값은 저장하지 않음)
            config_data = self.load_config_file()
            api_keys = config_data.get("api_keys", [])
            
            # 기존 키 정보 업데이트
            key_updated = False
            for key_info in api_keys:
                if key_info.get("env_key") == env_key:
                    key_info.update({
                        "name": name,
                        "env_key": env_key,
                        "updated_at": datetime.now().isoformat(),
                        "status": "미검증"
                    })
                    key_updated = True
                    break
            
            # 새 키 추가 (OPENAI_API_KEY가 아닌 경우만)
            if not key_updated and env_key != "OPENAI_API_KEY":
                api_keys.append({
                    "name": name,
                    "env_key": env_key,
                    "created_at": datetime.now().isoformat(),
                    "status": "미검증"
                })
            
            config_data["api_keys"] = api_keys
            self.save_config_file(config_data)
            
            # .env 변경 후 config 다시 로드
            from dotenv import load_dotenv
            load_dotenv(override=True)
            
            return True
            
        except Exception as e:
            print(f"Error saving API key: {e}")
            return False
    
    async def validate_api_key_async(self, api_key: str, env_key: str = "OPENAI_API_KEY") -> bool:
        """비동기 API 키 검증"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            
            # 간단한 API 호출로 키 유효성 검증
            await client.models.list()
            
            # 검증 성공 시 시간 저장
            self._save_validation_time(env_key)
            return True
            
        except Exception:
            return False
    
    def update_env_file(self, key: str, value: str) -> None:
        """환경 변수 파일 업데이트"""
        lines = []
        key_found = False
        
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # 기존 키 업데이트
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                key_found = True
                break
        
        # 새 키 추가
        if not key_found:
            lines.append(f"{key}={value}\n")
        
        # 파일 저장
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def load_config_file(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    def save_config_file(self, data: Dict[str, Any]) -> None:
        """설정 파일 저장"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _get_last_validation(self, env_key: str) -> str:
        """마지막 검증 시간 조회"""
        try:
            config_data = self.load_config_file()
            validations = config_data.get("validations", {})
            return validations.get(env_key, "없음")
        except Exception:
            return "없음"
    
    def _save_validation_time(self, env_key: str) -> None:
        """검증 시간 저장"""
        try:
            config_data = self.load_config_file()
            validations = config_data.get("validations", {})
            validations[env_key] = datetime.now().strftime("%Y-%m-%d %H:%M")
            config_data["validations"] = validations
            self.save_config_file(config_data)
        except Exception:
            pass