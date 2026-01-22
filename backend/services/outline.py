import logging
import os
import re
import base64
from typing import Dict, List, Any, Optional
from backend.config import Config
from backend.utils.text_client import get_text_chat_client

logger = logging.getLogger(__name__)


class OutlineService:
    def __init__(self):
        logger.debug("初始化 OutlineService...")
        # 使用全局配置管理器加载文本配置
        try:
            # 加载完整的文本服务商配置
            text_providers_config = Config.load_text_providers_config()
            active_provider_name = text_providers_config.get('active_provider', 'google_gemini')
            
            # 构建简化的配置结构
            self.text_config = {
                'active_provider': active_provider_name,
                'providers': {}
            }
            
            # 获取当前激活的提供商配置
            if active_provider_name in text_providers_config.get('providers', {}):
                provider_config = text_providers_config['providers'][active_provider_name]
                self.text_config['providers'][active_provider_name] = provider_config
            else:
                logger.error(f"文本服务商 [{active_provider_name}] 未找到")
                raise ValueError(
                    f"未找到文本生成服务商配置: {active_provider_name}\n"
                    "解决方案：在系统设置中选择一个可用的服务商"
                )
                
        except Exception as e:
            logger.error(f"获取文本服务商配置失败: {e}")
            raise ValueError(
                f"无法获取文本生成服务配置。\n"
                f"错误详情: {str(e)}\n"
                "解决方案：请检查系统设置中的文本生成服务商配置是否正确"
            )

        self.client = self._get_client()
        self.prompt_template = self._load_prompt_template()
        logger.info(f"OutlineService 初始化完成，使用服务商: {self.text_config.get('active_provider')}")

    def _load_text_config(self) -> dict:
        """加载文本生成配置"""
        config_path = Path(__file__).parent.parent.parent / 'text_providers.yaml'
        logger.debug(f"加载文本配置: {config_path}")

        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                logger.debug(f"文本配置加载成功: active={config.get('active_provider')}")
                return config
            except yaml.YAMLError as e:
                logger.error(f"文本配置 YAML 解析失败: {e}")
                raise ValueError(
                    f"文本配置文件格式错误: text_providers.yaml\n"
                    f"YAML 解析错误: {e}\n"
                    "解决方案：检查 YAML 缩进和语法"
                )

        logger.warning("text_providers.yaml 不存在，使用默认配置")
        # 默认配置
        return {
            'active_provider': 'google_gemini',
            'providers': {
                'google_gemini': {
                    'type': 'google_gemini',
                    'model': 'gemini-2.0-flash-exp',
                    'temperature': 1.0,
                    'max_output_tokens': 8000
                }
            }
        }

    def _get_client(self, needs_image_support: bool = False):
        """根据配置获取客户端
        
        Args:
            needs_image_support: 是否需要图片支持
        """
        active_provider = self.text_config.get('active_provider', 'google_gemini')
        providers = self.text_config.get('providers', {})

        if not providers:
            logger.error("未找到任何文本生成服务商配置")
            raise ValueError(
                "未找到任何文本生成服务商配置。\n"
                "解决方案：\n"
                "1. 在系统设置页面添加文本生成服务商\n"
                "2. 或手动编辑 text_providers.yaml 文件"
            )

        # 如果需要图片支持，优先选择支持图片的模型
        if needs_image_support:
            # 查找支持图片的模型
            image_supported_providers = []
            for name, config in providers.items():
                if config.get('supports_images', True):  # 默认假设支持图片
                    image_supported_providers.append((name, config))
            
            if image_supported_providers:
                # 优先使用当前激活的模型（如果支持图片）
                if active_provider in [p[0] for p in image_supported_providers]:
                    selected_provider = active_provider
                    provider_config = providers[active_provider]
                else:
                    # 选择第一个支持图片的模型
                    selected_provider, provider_config = image_supported_providers[0]
                logger.info(f"需要图片支持，选择服务商: {selected_provider} (支持图片)")
            else:
                # 没有支持图片的模型，使用默认
                logger.warning("没有找到支持图片的文本服务商，使用默认服务商")
                if active_provider not in providers:
                    available = ', '.join(providers.keys())
                    raise ValueError(
                        f"未找到文本生成服务商配置: {active_provider}\n"
                        f"可用的服务商: {available}\n"
                        "解决方案：在系统设置中选择一个可用的服务商"
                    )
                selected_provider = active_provider
                provider_config = providers[active_provider]
        else:
            # 不需要图片支持，使用当前激活的模型
            if active_provider not in providers:
                available = ', '.join(providers.keys())
                logger.error(f"文本服务商 [{active_provider}] 不存在，可用: {available}")
                raise ValueError(
                    f"未找到文本生成服务商配置: {active_provider}\n"
                    f"可用的服务商: {available}\n"
                    "解决方案：在系统设置中选择一个可用的服务商"
                )
            selected_provider = active_provider
            provider_config = providers[active_provider]

        if not provider_config.get('api_key'):
            logger.error(f"文本服务商 [{selected_provider}] 未配置 API Key")
            raise ValueError(
                f"文本服务商 {selected_provider} 未配置 API Key\n"
                "解决方案：在系统设置页面编辑该服务商，填写 API Key"
            )

        logger.info(f"使用文本服务商: {selected_provider} (type={provider_config.get('type')}, 支持图片={provider_config.get('supports_images', True)})")
        return get_text_chat_client(provider_config)

    def _load_prompt_template(self) -> str:
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "outline_prompt.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_outline(self, outline_text: str) -> List[Dict[str, Any]]:
        # 按 <page> 分割页面（兼容旧的 --- 分隔符）
        if '<page>' in outline_text:
            pages_raw = re.split(r'<page>', outline_text, flags=re.IGNORECASE)
        else:
            # 向后兼容：如果没有 <page> 则使用 ---
            pages_raw = outline_text.split("---")

        pages = []

        for index, page_text in enumerate(pages_raw):
            page_text = page_text.strip()
            if not page_text:
                continue

            page_type = "content"
            type_match = re.match(r"\[(\S+)\]", page_text)
            if type_match:
                type_cn = type_match.group(1)
                type_mapping = {
                    "封面": "cover",
                    "内容": "content",
                    "总结": "summary",
                }
                page_type = type_mapping.get(type_cn, "content")

            pages.append({
                "index": index,
                "type": page_type,
                "content": page_text
            })

        return pages

    def generate_outline(
        self,
        topic: str,
        images: Optional[List[bytes]] = None
    ) -> Dict[str, Any]:
        try:
            logger.info(f"开始生成大纲: topic={topic[:50]}..., images={len(images) if images else 0}")
            
            # 根据是否需要图片支持获取客户端
            needs_image_support = images is not None and len(images) > 0
            client = self._get_client(needs_image_support=needs_image_support)
            
            prompt = self.prompt_template.format(topic=topic)

            if images and len(images) > 0:
                prompt += f"\n\n注意：用户提供了 {len(images)} 张参考图片，请在生成大纲时考虑这些图片的内容和风格。这些图片可能是产品图、个人照片或场景图，请根据图片内容来优化大纲，使生成的内容与图片相关联。"
                logger.debug(f"添加了 {len(images)} 张参考图片到提示词")

            # 从当前客户端配置中获取模型参数
            # 注意：这里需要从配置中获取当前选择的provider的配置
            active_provider = self.text_config.get('active_provider', 'google_gemini')
            providers = self.text_config.get('providers', {})
            
            # 由于_get_client可能选择了不同的provider，我们需要重新获取配置
            # 简化处理：使用默认配置，实际模型参数由客户端内部处理
            model = "gpt-4o"  # 默认值，实际由客户端决定
            temperature = 1.0
            max_output_tokens = 8000

            logger.info(f"调用文本生成 API: 需要图片支持={needs_image_support}, temperature={temperature}")
            outline_text = client.generate_text(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                images=images
            )

            logger.debug(f"API 返回文本长度: {len(outline_text)} 字符")
            pages = self._parse_outline(outline_text)
            logger.info(f"大纲解析完成，共 {len(pages)} 页")

            return {
                "success": True,
                "outline": outline_text,
                "pages": pages,
                "has_images": images is not None and len(images) > 0
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"大纲生成失败: {error_msg}")

            # 根据错误类型提供更详细的错误信息
            if "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower() or "401" in error_msg:
                detailed_error = (
                    f"API 认证失败。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. API Key 无效或已过期\n"
                    "2. API Key 没有访问该模型的权限\n"
                    "解决方案：在系统设置页面检查并更新 API Key"
                )
            elif "model" in error_msg.lower() or "404" in error_msg:
                detailed_error = (
                    f"模型访问失败。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. 模型名称不正确\n"
                    "2. 没有访问该模型的权限\n"
                    "解决方案：在系统设置页面检查模型名称配置"
                )
            elif "timeout" in error_msg.lower() or "连接" in error_msg:
                detailed_error = (
                    f"网络连接失败。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. 网络连接不稳定\n"
                    "2. API 服务暂时不可用\n"
                    "3. Base URL 配置错误\n"
                    "解决方案：检查网络连接，稍后重试"
                )
            elif "rate" in error_msg.lower() or "429" in error_msg or "quota" in error_msg.lower():
                detailed_error = (
                    f"API 配额限制。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. API 调用次数超限\n"
                    "2. 账户配额用尽\n"
                    "解决方案：等待配额重置，或升级 API 套餐"
                )
            else:
                detailed_error = (
                    f"大纲生成失败。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. Text API 配置错误或密钥无效\n"
                    "2. 网络连接问题\n"
                    "3. 模型无法访问或不存在\n"
                    "建议：检查配置文件 text_providers.yaml"
                )

            return {
                "success": False,
                "error": detailed_error
            }


def get_outline_service() -> OutlineService:
    """
    获取大纲生成服务实例
    每次调用都创建新实例以确保配置是最新的
    """
    return OutlineService()
