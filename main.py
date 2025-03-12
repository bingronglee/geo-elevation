import pandas as pd
import numpy as np
from tkinter import Tk, filedialog, messagebox
from pykrige.ok import OrdinaryKriging

def load_csv(title):
    """透過GUI選擇CSV檔案"""
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title=title,
        filetypes=[("CSV files", "*.csv")]
    )
    return pd.read_csv(file_path) if file_path else None

def save_csv(df, title):
    """透過GUI選擇儲存路徑"""
    root = Tk()
    root.withdraw()
    save_path = filedialog.asksaveasfilename(
        title=title,
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")]
    )
    if save_path:
        df.to_csv(save_path, index=False, encoding='utf-8-sig')
        messagebox.showinfo("完成", f"檔案已儲存至：{save_path}")

def preprocess_data(df):
    """處理座標格式與缺失值"""
    df["X (m)"] = df["X (m)"].str.replace(",", "").astype(float)
    df["Y (m)"] = df["Y (m)"].str.replace(",", "").astype(float)
    return df.dropna(subset=["Ground Elevation (m)"])

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

def main():
    try:
        # 提示用戶選擇原始高程檔案
        messagebox.showinfo("提示", "請選擇原始高程資料檔案")
        df_original = load_csv("選擇原始高程資料CSV")
        if df_original is None:
            raise ValueError("未選擇原始高程資料檔案。")

        # 提示用戶選擇需求高程檔案
        messagebox.showinfo("提示", "請選擇需求高程資料檔案")
        df_demand = load_csv("選擇需求高程資料CSV")
        if df_demand is None:
            raise ValueError("未選擇需求高程資料檔案。")

        # 處理原始高程數據
        df_known = preprocess_data(df_original.copy())
        if df_known.empty:
            raise ValueError("原始高程資料中無有效數據。")

        # 處理需求高程數據
        df_unknown = df_demand.copy()
        df_unknown["X (m)"] = df_unknown["X (m)"].str.replace(",", "").astype(float)
        df_unknown["Y (m)"] = df_unknown["Y (m)"].str.replace(",", "").astype(float)
        if df_unknown.empty:
            raise ValueError("需求高程資料中無有效數據。")

        # 執行克里金插值
        elevations = kriging_interpolation(df_known, df_unknown)

        # 格式化插值結果，保留小數點後兩位
        df_unknown["Ground Elevation (m)"] = np.round(elevations, 2)

        # 提示用戶選擇儲存位置
        messagebox.showinfo("提示", "請選擇插值結果儲存位置")
        save_csv(df_unknown, "另存插值結果CSV")

    except Exception as e:
        messagebox.showerror("錯誤", str(e))

if __name__ == "__main__":
    main()