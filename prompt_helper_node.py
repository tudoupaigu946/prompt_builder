# prompt_helper_node.py
# -*- coding: utf-8 -*-

import json
import os
import random
from typing import List, Dict

import folder_paths

from PySide6 import QtWidgets, QtCore, QtGui

# ------------------- 常量定义 -------------------
PLUGIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
CONFIG_PATH = os.path.join(PLUGIN_DIR, "prompt_helper_config.json")  # 自动保存配置

# ------------------- 数据加载 -------------------
def load_prompt_data() -> Dict:
    """加载 JSON 数据库"""
    json_path = os.path.join(PLUGIN_DIR, "prompt_categories.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Prompt data file not found: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def load_config() -> Dict:
    """加载自动保存的配置"""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config: Dict):
    """保存自动保存的配置"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# ------------------- UI 主体 -------------------
class PromptHelperWidget(QtWidgets.QWidget):
    def __init__(self, node):
        super().__init__()
        self.node = node
        self.setWindowTitle("ComfyUI Prompt Helper")
        self.setMinimumWidth(500)
        self.setStyleSheet("font-size: 14px;")
        self.history = []  # 本地历史记录
        self._init_ui()
        self._load_data()
        self._load_config()  # 加载自动保存内容

    # ------------------- UI 初始化 -------------------
    def _init_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)

        # ------------------- 前置/后置提示词 -------------------
        self.group_prefix = QtWidgets.QGroupBox("🔮 前置提示词 (Prefix)")
        self.layout.addWidget(self.group_prefix)
        self.prefix_edit = QtWidgets.QLineEdit()
        self.prefix_edit.setPlaceholderText("如：masterpiece, best quality, (8k, RAW)")
        self.group_prefix.layout = QtWidgets.QVBoxLayout(self.group_prefix)
        self.group_prefix.layout.addWidget(self.prefix_edit)

        self.group_suffix = QtWidgets.QGroupBox("⚙️ 后置提示词 (Suffix)")
        self.layout.addWidget(self.group_suffix)
        self.suffix_edit = QtWidgets.QLineEdit()
        self.suffix_edit.setPlaceholderText("如：-2.0 (negative prompt)")
        self.group_suffix.layout = QtWidgets.QVBoxLayout(self.group_suffix)
        self.group_suffix.layout.addWidget(self.suffix_edit)

        # ------------------- 分类选择区 -------------------
        self.group_category = QtWidgets.QGroupBox("1️⃣ 选择分类")
        self.layout.addWidget(self.group_category)
        self.layout_category = QtWidgets.QVBoxLayout(self.group_category)

        self.combo_top = QtWidgets.QComboBox()
        self.combo_top.setPlaceholderText("请选择顶层分类")
        self.layout_category.addWidget(self.combo_top)

        self.combo_sub = QtWidgets.QComboBox()
        self.combo_sub.setPlaceholderText("请选择二级分类")
        self.layout_category.addWidget(self.combo_sub)

        # ------------------- 常见值选择区 -------------------
        self.group_values = QtWidgets.QGroupBox("2️⃣ 选择常见值 (随机默认)")
        self.layout.addWidget(self.group_values)
        self.layout_values = QtWidgets.QVBoxLayout(self.group_values)

        self.list_values = QtWidgets.QListWidget()
        self.list_values.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.layout_values.addWidget(self.list_values)

        # ------------------- 自定义输入区 -------------------
        self.group_custom = QtWidgets.QGroupBox("3️⃣ 自定义输入 (可选)")
        self.layout.addWidget(self.group_custom)
        self.layout_custom = QtWidgets.QVBoxLayout(self.group_custom)

        self.edit_custom = QtWidgets.QLineEdit()
        self.edit_custom.setPlaceholderText("输入自定义描述，例如：'金发', '夜晚', '柔光'")
        self.layout_custom.addWidget(self.edit_custom)

        # ------------------- 结果预览区 -------------------
        self.group_result = QtWidgets.QGroupBox("🔎 结果预览")
        self.layout.addWidget(self.group_result)
        self.layout_result = QtWidgets.QVBoxLayout(self.group_result)

        self.edit_result = QtWidgets.QLineEdit()
        self.edit_result.setReadOnly(True)
        self.layout_result.addWidget(self.edit_result)

        # ------------------- 操作按钮区 -------------------
        self.btn_add = QtWidgets.QPushButton("✅ 添加到 Prompt")
        self.btn_add.setStyleSheet("background-color: #4CAF50; color: white;")
        self.layout.addWidget(self.btn_add)

        # ------------------- 历史记录区 -------------------
        self.group_history = QtWidgets.QGroupBox("📜 历史记录")
        self.layout.addWidget(self.group_history)
        self.layout_history = QtWidgets.QVBoxLayout(self.group_history)

        self.list_history = QtWidgets.QListWidget()
        self.layout_history.addWidget(self.list_history)

        self.btn_history_use = QtWidgets.QPushButton("📋 使用选中历史记录")
        self.layout_history.addWidget(self.btn_history_use)

        # ------------------- 导入/导出/重置区 -------------------
        self.group_io = QtWidgets.QGroupBox("⚡ 导入/导出/重置")
        self.layout.addWidget(self.group_io)
        self.layout_io = QtWidgets.QHBoxLayout(self.group_io)

        self.btn_import = QtWidgets.QPushButton("导入 JSON")
        self.btn_export = QtWidgets.QPushButton("导出 JSON")
        self.btn_reset = QtWidgets.QPushButton("重置默认值")
        self.layout_io.addWidget(self.btn_import)
        self.layout_io.addWidget(self.btn_export)
        self.layout_io.addWidget(self.btn_reset)

        # ------------------- 信号槽绑定 -------------------
        self.combo_top.currentIndexChanged.connect(self.on_top_changed)
        self.combo_sub.currentIndexChanged.connect(self.on_sub_changed)
        self.list_values.itemSelectionChanged.connect(self.update_result)
        self.edit_custom.textChanged.connect(self.update_result)
        self.prefix_edit.textChanged.connect(self.update_result)
        self.suffix_edit.textChanged.connect(self.update_result)
        self.btn_add.clicked.connect(self.on_add_clicked)
        self.btn_history_use.clicked.connect(self.use_history_item)
        self.btn_import.clicked.connect(self.import_json)
        self.btn_export.clicked.connect(self.export_json)
        self.btn_reset.clicked.connect(self.reset_to_random)

    # ------------------- 数据加载 -------------------
    def _load_data(self):
        """读取 JSON 数据库"""
        self.data = load_prompt_data()
        self.combo_top.clear()
        self.combo_top.addItems(self.data.keys())
        self.combo_sub.clear()
        self.list_values.clear()
        self.update_result()

    def _load_config(self):
        """加载自动保存的内容"""
        config = load_config()
        # 加载历史记录
        self.history = config.get("history", [])
        self.refresh_history()
        # 加载前置/后置词
        self.prefix_edit.setText(config.get("prefix", ""))
        self.suffix_edit.setText(config.get("suffix", ""))
        # 加载上一次的选择
        top = config.get("top_category")
        sub = config.get("sub_category")
        if top and top in self.data:
            self.combo_top.setCurrentText(top)
            if sub and sub in self.data[top]:
                self.combo_sub.setCurrentText(sub)

    def closeEvent(self, event):
        """窗口关闭时自动保存"""
        config = {
            "history": self.history[-100:],  # 只保留最近 100 条
            "prefix": self.prefix_edit.text(),
            "suffix": self.suffix_edit.text(),
            "top_category": self.combo_top.currentText(),
            "sub_category": self.combo_sub.currentText()
        }
        save_config(config)
        event.accept()

    # ------------------- 交互逻辑 -------------------
    def on_top_changed(self, index):
        """顶层分类变化时更新二级分类"""
        if index < 0:
            return
        top_key = self.combo_top.currentText()
        sub_dict = self.data.get(top_key, {})
        self.combo_sub.clear()
        self.combo_sub.addItems(sub_dict.keys())
        self.list_values.clear()
        self.update_result()

    def on_sub_changed(self, index):
        """二级分类变化时更新常见值并随机选择"""
        if index < 0:
            return
        top_key = self.combo_top.currentText()
        sub_key = self.combo_sub.currentText()
        values = self.data.get(top_key, {}).get(sub_key, [])
        self.list_values.clear()
        self.list_values.addItems(values)

        # ------------------- 随机默认选择 -------------------
        # 逻辑：随机选中 30%~70% 的条目
        if values:
            count = len(values)
            # 随机决定选中的数量（至少1个，最多80%）
            select_num = random.randint(max(1, int(count * 0.3)), int(count * 0.7)
            indices = random.sample(range(count), select_num)
            for i in indices:
                item = self.list_values.item(i)
                item.setSelected(True)

        self.update_result()

    def update_result(self):
        """实时生成最终 Prompt"""
        selected = [i.text() for i in self.list_values.selectedItems()]
        custom = self.edit_custom.text().strip()
        prefix = self.prefix_edit.text().strip()
        suffix = self.suffix_edit.text().strip()

        # 组装顺序：前置词 + 选中值 + 自定义值 + 后置词
        parts = []
        if prefix:
            parts.append(prefix)
        if selected:
            parts.append(", ".join(selected))
        if custom:
            parts.append(custom)
        if suffix:
            parts.append(suffix)

        final_prompt = ", ".join(parts)
        self.edit_result.setText(final_prompt)

    def on_add_clicked(self):
        """点击按钮后将 Prompt 保存到节点输出"""
        final_prompt = self.edit_result.text().strip()
        if final_prompt:
            # 保存到历史记录
            if final_prompt not in self.history:
                self.history.append(final_prompt)
                self.refresh_history()
                # 自动保存历史（实时）
                config = load_config()
                config["history"] = self.history[-100:]
                save_config(config)

            # 写入节点输出
            self.node.set_output_prompt(final_prompt)
            QtWidgets.QMessageBox.information(self, "提示", "Prompt 已添加到节点输出！")
        else:
            QtWidgets.QMessageBox.warning(self, "警告", "请先生成 Prompt！")

    # ------------------- 历史记录功能 -------------------
    def refresh_history(self):
        """刷新历史记录列表"""
        self.list_history.clear()
        # 逆序显示最新的在最上面
        for item in reversed(self.history[-100:]):
            self.list_history.addItem(item)

    def use_history_item(self):
        """使用选中的历史记录"""
        selected_items = self.list_history.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "提示", "请先选择一条历史记录！")
            return
        history_prompt = selected_items[0].text()
        # 解析历史记录，尝试还原到 UI
        # 这里简单处理：直接填入预览框，用户可以手动微调
        self.edit_result.setText(history_prompt)
        self.update_result()

    # ------------------- 导入/导出功能 -------------------
    def import_json(self):
        """导入新的分类库"""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "导入 JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                # 保存为默认库
                with open(os.path.join(PLUGIN_DIR, "prompt_categories.json"), "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
                self._load_data()
                QtWidgets.QMessageBox.information(self, "成功", "导入成功！")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")

    def export_json(self):
        """导出当前分类库"""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "导出 JSON", "prompt_categories.json", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
                QtWidgets.QMessageBox.information(self, "成功", f"已导出到 {path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def reset_to_random(self):
        """重置所有选择为随机（保留前置/后置词）"""
        self.combo_top.setCurrentIndex(0)
        self.on_top_changed(0)  # 触发二级分类更新
        # 清空自定义输入
        self.edit_custom.clear()
        QtWidgets.QMessageBox.information(self, "提示", "已重置为随机默认值！")

# ------------------- 节点定义 -------------------
class PromptHelperNode:
    """
    Prompt Helper Node
    输出：Prompt（字符串）
    """

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "process"
    CATEGORY = "utils"

    INPUT_TYPES = {}

    def __init__(self):
        self.current_prompt = ""

    @classmethod
    def UI(cls):
        """返回自定义 UI 窗口"""
        return PromptHelperWidget(cls())

    def set_output_prompt(self, prompt: str):
        """UI 调用，更新节点的输出值"""
        self.current_prompt = prompt

    def process(self):
        """工作流执行时返回当前 Prompt"""
        return (self.current_prompt,)

