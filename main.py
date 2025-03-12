from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                              QMessageBox)
import pandas as pd
import numpy as np
from pykrige.ok import OrdinaryKriging

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("地理高程插值系統")
        self.setGeometry(100, 100, 400, 200)
        
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # 原始高程文件选择
        self.original_label = QLabel("尚未選擇原始高程檔案")
        btn_original = QPushButton("選擇原始高程檔案")
        btn_original.clicked.connect(self.select_original_file)
        
        # 需求高程文件选择
        self.demand_label = QLabel("尚未選擇需求高程檔案")
        btn_demand = QPushButton("選擇需求高程檔案")
        btn_demand.clicked.connect(self.select_demand_file)
        
        # 处理按钮
        btn_process = QPushButton("開始處理")
        btn_process.clicked.connect(self.process_data)
        
        # 布局设置
        layout.addWidget(self.original_label)
        layout.addWidget(btn_original)
        layout.addWidget(self.demand_label)
        layout.addWidget(btn_demand)
        layout.addWidget(btn_process)
        
        main_widget.setLayout(layout)
        
        # 文件路径存储
        self.original_path = None
        self.demand_path = None
        
    def select_original_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇原始高程檔案",
            "",
            "CSV Files (*.csv)",
            options=options
        )
        if file_path:
            self.original_path = file_path
            self.original_label.setText(f"已選擇：{file_path}")
            
    def select_demand_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇需求高程檔案",
            "",
            "CSV Files (*.csv)",
            options=options
        )
        if file_path:
            self.demand_path = file_path
            self.demand_label.setText(f"已選擇：{file_path}")
            
    def process_data(self):
        try:
            if not self.original_path or not self.demand_path:
                QMessageBox.warning(self, "警告", "請先選擇所有必要的檔案")
                return
                
            # 讀取檔案
            df_original = pd.read_csv(self.original_path)
            df_demand = pd.read_csv(self.demand_path)
            
            # 處理原始高程數據
            df_known = self.preprocess_data(df_original.copy())
            if df_known.empty:
                raise ValueError("原始高程資料中無有效數據。")
            
            # 處理需求高程數據
            df_unknown = df_demand.copy()
            df_unknown["X (m)"] = df_unknown["X (m)"].str.replace(",", "").astype(float)
            df_unknown["Y (m)"] = df_unknown["Y (m)"].str.replace(",", "").astype(float)
            if df_unknown.empty:
                raise ValueError("需求高程資料中無有效數據。")
            
            # 執行克里金插值
            elevations = self.kriging_interpolation(df_known, df_unknown)
            
            # 格式化插值結果
            df_unknown["Ground Elevation (m)"] = np.round(elevations, 2)
            
            # 保存结果
            options = QFileDialog.Options()
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存結果",
                "",
                "CSV Files (*.csv)",
                options=options
            )
            if save_path:
                df_unknown.to_csv(save_path, index=False, encoding='utf-8-sig')
                QMessageBox.information(self, "完成", f"檔案已成功保存至：{save_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "錯誤", str(e))
            
    @staticmethod
    def preprocess_data(df):
        """處理座標格式與缺失值"""
        df["X (m)"] = df["X (m)"].str.replace(",", "").astype(float)
        df["Y (m)"] = df["Y (m)"].str.replace(",", "").astype(float)
        return df.dropna(subset=["Ground Elevation (m)"])

    @staticmethod
    def kriging_interpolation(known_points, unknown_points):
        """執行克里金插值"""
        if known_points.empty:
            raise ValueError("已知點數據為空，無法執行克里金插值。")
        
        OK = OrdinaryKriging(
            known_points["X (m)"],
            known_points["Y (m)"],
            known_points["Ground Elevation (m)"],
            variogram_model='linear',  # 可改用 'spherical' 或 'gaussian'
            verbose=False,
            enable_plotting=False
        )
        z, _ = OK.execute('points', 
                         unknown_points["X (m)"], 
                         unknown_points["Y (m)"])
        return z

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()