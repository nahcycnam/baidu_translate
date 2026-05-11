import sys
import requests
import random
import json
from hashlib import md5
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
							 QHBoxLayout, QTextEdit, QPushButton, QLabel,
							 QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
import ctypes  # 添加这个导入


# 翻译线程
class TranslateThread(QThread):
	finished = pyqtSignal(dict)
	error = pyqtSignal(str)

	def __init__(self, appid, appkey, query, from_lang, to_lang):
		super().__init__()
		self.appid = appid
		self.appkey = appkey
		self.query = query
		self.from_lang = from_lang
		self.to_lang = to_lang

	def make_md5(self, s, encoding='utf-8'):
		return md5(s.encode(encoding)).hexdigest()

	def run(self):
		try:
			endpoint = 'http://api.fanyi.baidu.com'
			path = '/api/trans/vip/translate'
			url = endpoint + path

			# 生成salt和sign
			salt = random.randint(32768, 65536)
			sign = self.make_md5(self.appid + self.query + str(salt) + self.appkey)

			# 构建请求
			headers = {'Content-Type': 'application/x-www-form-urlencoded'}
			payload = {
				'appid': self.appid,
				'q': self.query,
				'from': self.from_lang,
				'to': self.to_lang,
				'salt': salt,
				'sign': sign
			}

			# 发送请求
			r = requests.post(url, params=payload, headers=headers, timeout=10)
			result = r.json()

			# 检查是否有错误
			if 'error_code' in result:
				self.error.emit(f"错误代码: {result['error_code']}\n错误信息: {result.get('error_msg', '未知错误')}")
			else:
				self.finished.emit(result)

		except requests.exceptions.RequestException as e:
			self.error.emit(f"网络错误: {str(e)}")
		except Exception as e:
			self.error.emit(f"翻译错误: {str(e)}")


# 主窗口
class BaiduTranslateWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		# 设置应用ID和密钥
		self.appid = '20240107001933624'
		self.appkey = '88AC7jG7azxIXecOY6n0'

		self.initUI()

	def initUI(self):
		self.setWindowTitle('百度翻译助手')
		self.setGeometry(300, 200, 800, 600)

		# 设置窗口图标（标题栏图标）
		self.setWindowIcon(QIcon('logo.ico'))

		# 设置窗口样式
		self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTextEdit {
                border: 2px solid #dcdcdc;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #4CAF50;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QComboBox {
                border: 2px solid #dcdcdc;
                border-radius: 5px;
                padding: 5px;
                font-size: 13px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #4CAF50;
            }
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #333333;
            }
        """)

		# 创建中心部件
		central_widget = QWidget()
		self.setCentralWidget(central_widget)

		# 主布局
		main_layout = QVBoxLayout()
		central_widget.setLayout(main_layout)

		# 顶部控制栏
		control_layout = QHBoxLayout()

		# 源语言选择
		from_label = QLabel("源语言:")
		self.from_combo = QComboBox()
		self.from_combo.addItems(["自动检测", "中文", "英语", "日语", "韩语", "法语", "德语", "西班牙语", "俄语"])
		self.from_combo.setCurrentIndex(0)

		# 目标语言选择
		to_label = QLabel("目标语言:")
		self.to_combo = QComboBox()
		self.to_combo.addItems(["中文", "英语", "日语", "韩语", "法语", "德语", "西班牙语", "俄语"])
		self.to_combo.setCurrentIndex(1)

		control_layout.addWidget(from_label)
		control_layout.addWidget(self.from_combo)
		control_layout.addSpacing(20)
		control_layout.addWidget(to_label)
		control_layout.addWidget(self.to_combo)
		control_layout.addStretch()

		# 翻译按钮
		self.translate_btn = QPushButton("开始翻译")
		self.translate_btn.clicked.connect(self.start_translate)
		control_layout.addWidget(self.translate_btn)

		main_layout.addLayout(control_layout)

		# 文本输入区域
		input_label = QLabel("输入文本:")
		main_layout.addWidget(input_label)

		self.input_text = QTextEdit()
		self.input_text.setPlaceholderText("请输入要翻译的文本...")
		self.input_text.setMinimumHeight(200)
		main_layout.addWidget(self.input_text)

		# 翻译结果显示区域
		output_label = QLabel("翻译结果:")
		main_layout.addWidget(output_label)

		self.output_text = QTextEdit()
		self.output_text.setPlaceholderText("翻译结果将在这里显示...")
		self.output_text.setReadOnly(True)
		self.output_text.setMinimumHeight(200)
		main_layout.addWidget(self.output_text)

		# 状态栏
		self.statusBar().showMessage("就绪")

		# 设置快捷键
		self.translate_btn.setShortcut("Ctrl+Return")

	def get_lang_code(self, lang_name):
		"""将语言名称转换为百度API的语言代码"""
		lang_map = {
			"自动检测": "auto",
			"中文": "zh",
			"英语": "en",
			"日语": "jp",
			"韩语": "kor",
			"法语": "fra",
			"德语": "de",
			"西班牙语": "spa",
			"俄语": "ru"
		}
		return lang_map.get(lang_name, "auto")

	def start_translate(self):
		"""开始翻译"""
		query = self.input_text.toPlainText().strip()

		if not query:
			QMessageBox.warning(self, "警告", "请输入要翻译的文本")
			return

		# 禁用按钮，显示加载状态
		self.translate_btn.setEnabled(False)
		self.translate_btn.setText("翻译中...")
		self.statusBar().showMessage("正在翻译...")

		# 清空显示
		self.output_text.clear()

		# 获取语言代码
		from_lang = self.get_lang_code(self.from_combo.currentText())
		to_lang = self.get_lang_code(self.to_combo.currentText())

		# 启动翻译线程
		self.translate_thread = TranslateThread(
			self.appid, self.appkey, query, from_lang, to_lang
		)
		self.translate_thread.finished.connect(self.on_translate_finished)
		self.translate_thread.error.connect(self.on_translate_error)
		self.translate_thread.start()

	def on_translate_finished(self, result):
		"""翻译完成回调"""
		try:
			# 解析翻译结果
			if 'trans_result' in result:
				trans_result = result['trans_result']
				translated_text = ""
				for item in trans_result:
					translated_text += item['dst'] + "\n"

				self.output_text.setText(translated_text.strip())
				self.statusBar().showMessage("翻译完成")

				# 在控制台打印详细信息
				print(json.dumps(result, indent=4, ensure_ascii=False))
			else:
				self.output_text.setText("解析翻译结果失败")
				self.statusBar().showMessage("翻译失败")

		except Exception as e:
			self.output_text.setText(f"处理结果时出错: {str(e)}")
			self.statusBar().showMessage("处理结果失败")

		# 恢复按钮状态
		self.translate_btn.setEnabled(True)
		self.translate_btn.setText("开始翻译")

	def on_translate_error(self, error_msg):
		"""翻译错误回调"""
		self.output_text.setText(f"翻译出错:\n{error_msg}")
		self.statusBar().showMessage("翻译出错")

		# 恢复按钮状态
		self.translate_btn.setEnabled(True)
		self.translate_btn.setText("开始翻译")


def main():
	app = QApplication(sys.argv)

	# Windows任务栏图标设置的多种方法

	# 方法1：设置应用程序图标
	app.setWindowIcon(QIcon('logo.ico'))

	# 方法2：使用ctypes设置任务栏图标（Windows专用）
	try:
		# 获取应用程序窗口句柄
		hwnd = int(app.activeWindow().winId()) if app.activeWindow() else 0
		# 设置任务栏图标
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('mycompany.myproduct.translator')
	except:
		pass

	# 设置应用程序字体
	font = QFont("Microsoft YaHei", 9)
	app.setFont(font)

	window = BaiduTranslateWindow()
	window.show()

	# 方法3：显示窗口后再次尝试设置任务栏图标
	try:
		hwnd = int(window.winId())
		# 这个ID可以自定义，确保唯一性
		app_id = 'BaiduTranslator.v1.0'
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
	except:
		pass

	sys.exit(app.exec())


if __name__ == '__main__':
	main()
