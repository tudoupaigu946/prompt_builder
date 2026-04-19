import json
import random
import os
import time
from typing import Dict, List, Any

# -------------------------- 配置加载 --------------------------
PLUGIN_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(PLUGIN_DIR, "prompt_categories.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    PROMPT_CATEGORIES = json.load(f)

# -------------------------- 核心提示词构建节点 --------------------------
class ChinesePromptBuilder:
    @classmethod
    def INPUT_TYPES(s):
        input_options = {
            "前置提示词": ("STRING", {"default": "", "multiline": True, "placeholder": "全局前缀：高质量、细节、画风等"}),
            "后置提示词": ("STRING", {"default": "", "multiline": True, "placeholder": "全局后缀：分辨率、光影、画质等"}),
        }

        # 递归构建多级分类
        def build_category_options(categories: Dict, parent_key: str = ""):
            for key, value in categories.items():
                current_key = f"{parent_key}/{key}" if parent_key else key
                if isinstance(value, list):
                    input_options[current_key] = (
                        ["无", "随机"] + value,
                        {"default": "无"}
                    )
                elif isinstance(value, dict):
                    build_category_options(value, current_key)

        build_category_options(PROMPT_CATEGORIES)

        return {"required": input_options}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("最终提示词",)
    FUNCTION = "build_prompt"
    CATEGORY = "提示词工具/中文提示词构建器"
    DESCRIPTION = "中文多级联动提示词插件，支持随机（每次执行自动刷新）"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # 如果有任何分类选择了“随机”，则强制重新执行
        for key, value in kwargs.items():
            if key not in ["前置提示词", "后置提示词"]:
                if value == "随机":
                    return time.time()
        return None

    def get_random_value(self, options: List[str]) -> str:
        actual_options = [opt for opt in options if opt not in ["无", "随机"]]
        if not actual_options:
            return ""
        return random.choice(actual_options)

    def build_prompt(self, **kwargs):
        prompt_parts = []

        for key, value in kwargs.items():
            if key in ["前置提示词", "后置提示词"]:
                continue

            options = self.INPUT_TYPES()["required"][key][0]
            selected = ""

            if value == "随机":
                selected = self.get_random_value(options)
            elif value not in ["无", "", None]:
                selected = value

            if selected:
                prompt_parts.append(selected)

        prefix = kwargs.get("前置提示词", "").strip()
        suffix = kwargs.get("后置提示词", "").strip()
        main_prompt = ", ".join(prompt_parts)

        final_prompt = ""
        if prefix:
            final_prompt += f"{prefix}, "
        final_prompt += main_prompt
        if suffix:
            final_prompt += f", {suffix}"

        final_prompt = final_prompt.strip().strip(",").replace(",,", ",")
        return (final_prompt,)

# -------------------------- 节点注册 --------------------------
NODE_CLASS_MAPPINGS = {
    "ChinesePromptBuilder": ChinesePromptBuilder,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ChinesePromptBuilder": "中文提示词构建器",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
