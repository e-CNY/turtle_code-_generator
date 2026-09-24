from openai import OpenAI
import pyperclip
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, font
import webbrowser
import json
import os

URL_HOME = "https://www.bilibili.com/video/BV1bpaN6yEo1"     # 视频演示链接
URL_HELP = "https://github.com/e-CNY/turtle_code-_generator/blob/main/README.md"     # 使用说明链接

# ========== 全局链接打开函数 ==========
def open_home(event):
    webbrowser.open(URL_HOME)

def open_help(event):
    webbrowser.open(URL_HELP)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("海龟编辑器2 AI代码生成器")
        self.root.geometry("800x1000")
        self.root.resizable(True, True)
        self.config_file = "config.json" # 配置文件名称

        # 连接配置变量
        self.base_url_var = tk.StringVar(value="http://localhost:1234/v1")
        self.api_key_var = tk.StringVar(value="lm-studio")
        self.model_name_var = tk.StringVar(value="qwen3.5-9b")
        self.client = None
        self.connected = False
        self.python_code = ""  # 初始化代码存储变量

        # 字体变量
        all_fonts_raw = list(font.families(root=self.root))
        all_fonts_filtered = sorted(set([f for f in all_fonts_raw if not f.startswith("@") and f.strip()]))
        self.font_name = tk.StringVar(value="Consolas")
        self.font_size = tk.IntVar(value=10)
        self.current_font = (self.font_name.get(), self.font_size.get())

        # 加载本地配置
        self.load_config()

        # 主容器
        main_frame = ttk.Frame(root, padding="16")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ========== 连接配置区域 ==========
        conn_frame = ttk.LabelFrame(main_frame, text="API连接配置", padding="10")
        conn_frame.pack(fill=tk.X, pady=(0,12))

        ttk.Label(conn_frame, text="BaseURL:").grid(row=0, column=0, sticky="w", padx=2, pady=4)
        entry_base = ttk.Entry(conn_frame, textvariable=self.base_url_var, width=55)
        entry_base.grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(conn_frame, text="ApiKey:").grid(row=1, column=0, sticky="w", padx=2, pady=4)
        entry_key = ttk.Entry(conn_frame, textvariable=self.api_key_var, width=55)
        entry_key.grid(row=1, column=1, padx=4, pady=4)

        ttk.Label(conn_frame, text="模型名称:").grid(row=2, column=0, sticky="w", padx=2, pady=4)
        entry_model = ttk.Entry(conn_frame, textvariable=self.model_name_var, width=55)
        entry_model.grid(row=2, column=1, padx=4, pady=4)

        btn_test_conn = ttk.Button(conn_frame, text="测试连接", command=self.test_connection)
        btn_test_conn.grid(row=3, column=0, columnspan=2, pady=(6,0))

        # ========== 字体设置行 ==========
        font_frame = ttk.Frame(main_frame)
        font_frame.pack(anchor="w", pady=(0,10))
        ttk.Label(font_frame, text="代码字体：").grid(row=0, column=0, padx=(0,5))
        cb_font = ttk.Combobox(font_frame, textvariable=self.font_name, values=all_fonts_filtered, width=24, state="readonly")
        cb_font.grid(row=0, column=1, padx=(0,10))
        ttk.Label(font_frame, text="字号：").grid(row=0, column=2, padx=(0,5))
        size_list = [str(i) for i in range(8,21)]
        cb_size = ttk.Combobox(font_frame, textvariable=self.font_size, values=size_list, width=6, state="readonly")
        cb_size.grid(row=0, column=3, padx=(0,10))
        btn_apply_font = ttk.Button(font_frame, text="应用字体", command=self.apply_font)
        btn_apply_font.grid(row=0, column=4)

        # 输入区域
        ttk.Label(main_frame, text="请输入编程需求：").pack(anchor="w")
        self.task_input = scrolledtext.ScrolledText(main_frame, height=4, font=self.current_font)
        self.task_input.pack(pady=(4,12), fill=tk.X)

        # 生成按钮
        self.gen_btn = ttk.Button(main_frame, text="生成代码", command=self.on_generate, state="disabled")
        self.gen_btn.pack(pady=(0,12))

        # 结果预览
        ttk.Label(main_frame, text="生成预览：").pack(anchor="w")
        self.result_box = scrolledtext.ScrolledText(main_frame, height=14, font=self.current_font)
        self.result_box.pack(pady=(4,12), fill=tk.BOTH, expand=True)

        # ========== 底部按钮组【已修正缩进，三按钮整体居中】 ==========
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        inner_btn = ttk.Frame(btn_frame)
        inner_btn.pack()
        self.btn_copy_code = ttk.Button(inner_btn, text="复制代码", command=self.copy_code)
        self.btn_save = ttk.Button(inner_btn, text="保存py文件", command=self.save_py_file)
        self.btn_clear = ttk.Button(inner_btn, text="清空", command=self.clear_all)
        self.btn_copy_code.grid(row=0, column=0, padx=8)
        self.btn_save.grid(row=0, column=1, padx=8)
        self.btn_clear.grid(row=0, column=2, padx=8)

        # ========== 底部链接（视频演示、使用说明） ==========
        frame_bottom = ttk.Frame(main_frame)
        frame_bottom.pack(pady=4, fill="x")
        link_home = ttk.Label(frame_bottom, text="视频演示", foreground="blue", cursor="hand2")
        link_home.pack(side=tk.LEFT)
        link_home.bind("<Button-1>", open_home)
        link_help = ttk.Label(frame_bottom, text="使用说明", foreground="blue", cursor="hand2")
        link_help.pack(side=tk.RIGHT)
        link_help.bind("<Button-1>", open_help)

        # 窗口关闭事件，自动保存配置
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_config(self):
        """读取json配置文件，不存在则跳过"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.base_url_var.set(cfg.get("base_url", "http://localhost:1234/v1"))
                self.api_key_var.set(cfg.get("api_key", "lm-studio"))
                self.model_name_var.set(cfg.get("model_name", "qwen3.5-9b"))
                self.font_name.set(cfg.get("font_name", "Consolas"))
                self.font_size.set(cfg.get("font_size", 10))
                self.current_font = (self.font_name.get(), self.font_size.get())
            except Exception:
                pass

    def save_config(self):
        """保存配置"""
        cfg = {
            "base_url": self.base_url_var.get(),
            "api_key": self.api_key_var.get(),
            "model_name": self.model_name_var.get(),
            "font_name": self.font_name.get(),
            "font_size": self.font_size.get()
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

    def on_close(self):
        """关闭窗口"""
        self.save_config()
        self.root.destroy()

    def test_connection(self):
        """测试API连接"""
        try:
            self.client = OpenAI(
                base_url=self.base_url_var.get().strip(),
                api_key=self.api_key_var.get().strip()
            )
            # 简单调用验证
            self.client.models.list()
            self.connected = True
            self.gen_btn.config(state="normal")
            messagebox.showinfo("连接成功", "API连通正常，可以生成代码！")
        except Exception as e:
            self.connected = False
            self.gen_btn.config(state="disabled")
            messagebox.showerror("连接失败", f"无法连接API：\n{str(e)}")

    def apply_font(self):
        new_font = (self.font_name.get(), self.font_size.get())
        self.task_input.config(font=new_font)
        self.result_box.config(font=new_font)
        self.current_font = new_font

    def ai_generate(self, task):
        sys_prompt = """
你是【海龟编辑器2.0】专用Python代码生成助手。你需要根据用户需求编写Python代码，严格遵守下面规则：
===== 支持库说明 =====
类型1：TURTLE海龟绘图
适用场景：几何绘图、画图、五角星、螺旋、彩色图案等。生成代码粘贴到海龟编辑器2.0可以一键切换积木模式。
类型2：CODEMAO库（编程猫官方库）
适用场景：摄像头、人脸识别、录音、AI图像识别。支持积木转换。
类型3：REQUESTS网络爬虫
适用场景：简单网页抓取。支持积木转换。
类型4：PYGAME游戏
适用场景：小游戏、角色移动、碰撞检测、动画。代码可以运行，但**不支持转积木**。
类型5：PYGAME ZERO
适用场景：简易小游戏，简化版pygame。代码可运行，**不支持转积木**。
类型6：WOODAI库
适用场景：图像识别、语音合成。代码可运行，**不支持转积木**。
类型7：原生Python标准库
适用场景：数学、随机数、文本处理、json、csv、时间等。代码能运行，**不支持积木转换**。

===== 代码强制规范 =====
1. 代码粘贴到海龟编辑器2.0可以直接运行，只用海龟编辑器内置库，不要写不存在的第三方库。
2. 类型1/2/3的代码风格要适配积木转换，不要用装饰器、生成器、复杂类等阻碍积木解析的高级语法。
3. pygame/pygamezero代码要写完整，保证可以直接运行，处理窗口关闭防止闪退。
4. 只返回完整代码，不要markdown ```标记，不要额外解释文字，只输出代码。
"""
        resp = self.client.chat.completions.create(
            model=self.model_name_var.get().strip(),
            messages=[
                {"role":"system", "content": sys_prompt},
                {"role":"user", "content": task}
            ],
            temperature=0.3
        )
        return resp.choices[0].message.content.strip()

    def on_generate(self):
        task = self.task_input.get("1.0", tk.END).strip()
        if not task:
            messagebox.showwarning("提示", "请输入编程需求！")
            return
        if not self.connected or self.client is None:
            messagebox.showerror("错误", "请先测试API连接！")
            return
        try:
            self.gen_btn.config(state="disabled", text="生成中...")
            self.root.update()
            self.python_code = self.ai_generate(task)
            self.result_box.delete("1.0", tk.END)
            self.result_box.insert("1.0", self.python_code)
            messagebox.showinfo("完成", "代码生成成功！")
        except Exception as e:
            messagebox.showerror("生成失败", f"生成代码出错：\n{str(e)}")
        finally:
            self.gen_btn.config(state="normal", text="生成代码")

    def copy_code(self):
        if not self.python_code:
            messagebox.showwarning("提示", "请先生成内容！")
            return
        pyperclip.copy(self.python_code)
        messagebox.showinfo("成功", "代码已复制到剪贴板！")

    def save_py_file(self):
        if not self.python_code:
            messagebox.showwarning("提示", "请先生成内容！")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python文件", "*.py"), ("所有文件", "*.*")],
            title="保存py文件"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.python_code)
            messagebox.showinfo("保存成功", f"文件保存至：\n{path}")

    def clear_all(self):
        self.task_input.delete("1.0", tk.END)
        self.result_box.delete("1.0", tk.END)
        self.python_code = ""

if __name__ == "__main__":
    win = tk.Tk()
    app = App(win)
    win.mainloop()
