import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import font as tkfont
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import os
import matplotlib as mpl

# ==========================================
# บังคับตั้งค่าฟอนต์ภาษาไทยสำหรับกราฟ
# ==========================================
mpl.rcParams['font.family'] = 'Tahoma'
mpl.rcParams['axes.unicode_minus'] = False 

class AdvancedLotteryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ระบบวิเคราะห์และพยากรณ์สลากกินแบ่งรัฐบาล (AI-Enhanced v3.0)")
        self.root.geometry("1150x780")
        self.root.configure(bg="#f0f2f5")
        
        # บังคับฟอนต์ภาษาไทยสำหรับหน้าต่างโปรแกรม
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Tahoma", size=10)
        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(family="Tahoma", size=10)
        self.root.option_add("*Font", "Tahoma 10")
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(".", font=("Tahoma", 10))
        style.configure("TFrame", background="#f0f2f5")
        style.configure("TLabel", background="#f0f2f5", font=("Tahoma", 10))
        style.configure("TButton", font=("Tahoma", 10, "bold"), padding=5)
        style.configure("Header.TLabel", font=("Tahoma", 12, "bold"), foreground="#333333")
        
        self.df = None
        self.feedback_scores = {str(i).zfill(2): 0.0 for i in range(100)}
        self.total_feedback_records = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        # ---------------- ส่วนซ้าย: แผงควบคุม ----------------
        control_frame = ttk.Frame(self.root, width=320, relief=tk.RAISED, borderwidth=1)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        control_frame.pack_propagate(False) 
        
        ttk.Label(control_frame, text="⚙️ แผงควบคุม (Control Panel)", style="Header.TLabel").pack(pady=15)
        
        # 1. โหลดข้อมูล
        ttk.Label(control_frame, text="1. นำเข้าข้อมูลสลากย้อนหลัง (CSV)").pack(anchor=tk.W, padx=15, pady=(5, 0))
        tk.Button(control_frame, text="📂 เลือกไฟล์ & วิเคราะห์", command=self.load_data, bg="#4A90E2", fg="white", font=("Tahoma", 10, "bold"), relief=tk.FLAT).pack(fill=tk.X, padx=15, pady=5)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10, padx=10)
        
        # 2. ระบบ AI Feedback
        ttk.Label(control_frame, text="2. โหลดไฟล์รายงานเพื่อบวกคะแนน AI").pack(anchor=tk.W, padx=15)
        self.feedback_label = ttk.Label(control_frame, text="สถานะ: ยังไม่มีข้อมูลเรียนรู้ (0 Records)", foreground="#D0021B", font=("Tahoma", 9))
        self.feedback_label.pack(anchor=tk.W, padx=15, pady=2)
        tk.Button(control_frame, text="🧠 โหลดไฟล์พยากรณ์ย้อนหลัง", command=self.load_feedback_file, bg="#8B572A", fg="white", font=("Tahoma", 10, "bold"), relief=tk.FLAT).pack(fill=tk.X, padx=15, pady=5)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10, padx=10)
        
        # 3. ตั้งค่าการพยากรณ์
        ttk.Label(control_frame, text="3. ตั้งค่าโมเดลพยากรณ์").pack(anchor=tk.W, padx=15)
        ttk.Label(control_frame, text="เลือกโมเดล (Algorithm):").pack(anchor=tk.W, padx=15, pady=(5, 2))
        self.model_var = tk.StringVar(value="Recency Weighting")
        models = ["Recency Weighting", "Historical Frequency", "Overdue Numbers", "Short-Term Trend (Last 50)", "Hybrid (Freq + Recency)"]
        ttk.Combobox(control_frame, textvariable=self.model_var, values=models, state="readonly").pack(fill=tk.X, padx=15, pady=2)
        
        ttk.Label(control_frame, text="จำนวนตัวเลขที่พยากรณ์ (K):").pack(anchor=tk.W, padx=15, pady=(5, 2))
        self.k_var = tk.IntVar(value=5)
        ttk.Spinbox(control_frame, from_=1, to=20, textvariable=self.k_var).pack(fill=tk.X, padx=15, pady=2)
        
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10, padx=10)
        
        # 4. ดำเนินการพยากรณ์
        ttk.Label(control_frame, text="4. ประมวลผล").pack(anchor=tk.W, padx=15)
        tk.Button(control_frame, text="🔮 พยากรณ์งวดถัดไป", command=self.predict_next, bg="#50E3C2", fg="#000000", font=("Tahoma", 10, "bold"), relief=tk.FLAT).pack(fill=tk.X, padx=15, pady=5)
        tk.Button(control_frame, text="📊 ทดสอบความแม่นยำ (Backtest)", command=self.run_backtest, bg="#F5A623", fg="white", font=("Tahoma", 10, "bold"), relief=tk.FLAT).pack(fill=tk.X, padx=15, pady=5)
        
        self.progress = ttk.Progressbar(control_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, padx=15, pady=10)

        # ---------------- ส่วนขวา: หน้าต่างแสดงผล ----------------
        display_frame = ttk.Frame(self.root)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        
        self.notebook = ttk.Notebook(display_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: กราฟ Top 30
        self.tab_chart_top = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_chart_top, text="📈 กราฟ Top 30")
        self.fig_top, self.ax_top = plt.subplots(figsize=(8, 4))
        self.canvas_top = FigureCanvasTkAgg(self.fig_top, master=self.tab_chart_top)
        self.canvas_top.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 2: กราฟ 00-99
        self.tab_chart_all = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_chart_all, text="📊 กราฟทั้งหมด (00-99)")
        self.fig_all, self.ax_all = plt.subplots(figsize=(8, 4))
        self.canvas_all = FigureCanvasTkAgg(self.fig_all, master=self.tab_chart_all)
        self.canvas_all.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 3: ตารางข้อมูล
        self.tab_data = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_data, text="🗂️ ข้อมูลดิบ")
        columns = ("draw_id", "draw_date", "last2digit")
        self.tree = ttk.Treeview(self.tab_data, columns=columns, show="headings")
        self.tree.heading("draw_id", text="ลำดับ (ID)")
        self.tree.heading("draw_date", text="วันที่ออกรางวัล")
        self.tree.heading("last2digit", text="เลขท้าย 2 ตัว")
        self.tree.column("draw_id", width=100, anchor=tk.CENTER)
        self.tree.column("draw_date", width=200, anchor=tk.CENTER)
        self.tree.column("last2digit", width=150, anchor=tk.CENTER)
        scrollbar = ttk.Scrollbar(self.tab_data, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 4: Logs
        self.tab_log = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_log, text="📝 บันทึกผลลัพธ์")
        self.log_text = tk.Text(self.tab_log, font=("Consolas", 11), bg="#282C34", fg="#50E3C2", padx=10, pady=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_message(">> ยินดีต้อนรับสู่ระบบพยากรณ์สลากกินแบ่งรัฐบาล")

    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def load_data(self):
        try:
            file_path = filedialog.askopenfilename(title="เลือกไฟล์ CSV", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
            if not file_path: return
                
            self.log_message(f"\n[System] กำลังโหลดข้อมูลจาก: {file_path}")
            try: df = pd.read_csv(file_path, encoding='utf-8-sig')
            except: df = pd.read_csv(file_path, encoding='cp874')
            
            df['year_ce'] = df['ปี'] - 543
            date_strs = df['year_ce'].astype(str) + '-' + df['เดือน'].astype(str) + '-' + df['วัน'].astype(str)
            df['draw_date'] = pd.to_datetime(date_strs, errors='coerce')
            df = df.dropna(subset=['draw_date'])
            df['last2digit'] = df['เลขท้าย2ตัว'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(2)
            
            self.df = df.sort_values('draw_date').reset_index(drop=True)
            self.log_message(f"[System] โหลดข้อมูลสำเร็จ! พบข้อมูลทั้งหมด {len(self.df)} งวด")
            
            self.update_charts()
            self.update_table()
            self.notebook.select(self.tab_chart_top)
            
        except Exception as e:
            messagebox.showerror("Error", f"เกิดข้อผิดพลาดในการอ่านไฟล์:\n{e}")

    def load_feedback_file(self):
        try:
            file_path = filedialog.askopenfilename(
                title="เลือกไฟล์รายงาน (.txt)", 
                filetypes=(("Result Files", "*.txt"), ("All files", "*.*"))
            )
            if not file_path: return
            
            filename = os.path.basename(file_path)
            if not (filename.startswith("result_") or filename.startswith("forecast_result")):
                messagebox.showerror("แจ้งเตือน", "ระบบปฏิเสธการอ่านไฟล์!\nต้องเลือกไฟล์ชื่อที่ขึ้นต้นด้วย 'result_' หรือ 'forecast_result' ถึงจะคำนวณ +1 -1 ได้")
                return
            
            # --- แก้ไขระบบอ่านไฟล์ Text ภาษาไทยที่นี่ ---
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='cp874') as f:
                    lines = f.readlines()
            # -----------------------------------------
                
            total_draws = 0
            hit_count = 0
            
            for line in lines:
                if '|' in line and 'งวดวันที่' not in line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        total_draws += 1
                        actual = parts[1].strip()
                        preds = [x.strip() for x in parts[2].split(',')]
                        
                        is_hit = False
                        for p in preds:
                            if p == actual:
                                self.feedback_scores[p] += 1.0 
                                is_hit = True
                            else:
                                self.feedback_scores[p] -= 1.0 
                                
                        if is_hit:
                            hit_count += 1
                            
            miss_count = total_draws - hit_count
            
            self.total_feedback_records += 1
            self.feedback_label.config(text=f"สถานะ: เรียนรู้แล้ว ({self.total_feedback_records} ไฟล์)", foreground="#417505")
            
            self.notebook.select(self.tab_log)
            self.log_message(f"\n[AI Learning] อ่านข้อมูลจากไฟล์: {filename} สำเร็จ!")
            self.log_message(f">> จำนวนงวดที่พยากรณ์ทั้งหมด: {total_draws} งวด")
            self.log_message(f">> จำนวนงวดที่ตอบถูก (Hit): {hit_count} งวด")
            self.log_message(f">> จำนวนงวดที่ตอบผิด (Miss): {miss_count} งวด")
            self.log_message(">> นำคะแนนไปคำนวณปรับน้ำหนักในโมเดลเรียบร้อยแล้ว")
            
        except Exception as e:
            messagebox.showerror("Error", f"เกิดข้อผิดพลาด:\n{e}")

    def update_charts(self):
        # 1. กราฟ Top 30
        self.ax_top.clear()
        freq_top = self.df['last2digit'].value_counts().head(30) 
        bars1 = self.ax_top.bar(freq_top.index, freq_top.values, color='#3498DB', edgecolor='#2980B9', linewidth=1)
        self.ax_top.set_title("Top 30 Most Frequent Two-Digit Numbers (ความถี่สูงสุด 30 อันดับ)", fontsize=13, fontweight='bold')
        self.ax_top.set_ylabel("จำนวนครั้ง", fontsize=10)
        self.ax_top.tick_params(axis='x', rotation=45, labelsize=9)
        for bar in bars1:
            yval = bar.get_height()
            self.ax_top.text(bar.get_x() + bar.get_width()/2.0, yval + 0.3, int(yval), va='bottom', ha='center', fontsize=8, color='#333333')
        self.ax_top.grid(axis='y', linestyle='--', alpha=0.4)
        self.fig_top.tight_layout()
        self.canvas_top.draw()
        
        # 2. กราฟ 00-99 (ทั้งหมด)
        self.ax_all.clear()
        freq_all = self.df['last2digit'].value_counts().sort_index()
        bars2 = self.ax_all.bar(freq_all.index, freq_all.values, color='#9B59B6', edgecolor='#8E44AD', linewidth=0.5)
        self.ax_all.set_title("Distribution of All Two-Digit Numbers (ความถี่ของเลข 00-99)", fontsize=13, fontweight='bold')
        self.ax_all.set_ylabel("จำนวนครั้ง", fontsize=10)
        self.ax_all.tick_params(axis='x', rotation=90, labelsize=6)
        self.ax_all.grid(axis='y', linestyle='--', alpha=0.4)
        self.fig_all.tight_layout()
        self.canvas_all.draw()

    def update_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, row in self.df.iterrows():
            date_str = row['draw_date'].strftime('%Y-%m-%d')
            self.tree.insert("", tk.END, values=(idx + 1, date_str, row['last2digit']))

    # ================= โมเดลพยากรณ์ =================
    
    def model_recency_weighting(self, history_df, k):
        scores = {str(i).zfill(2): 0.0 for i in range(100)}
        n = len(history_df)
        for i in range(n):
            number = history_df.iloc[i]['last2digit']
            scores[number] += (i + 1) / n 
        return scores

    def model_historical_frequency(self, history_df, k):
        freq = history_df['last2digit'].value_counts()
        scores = {str(i).zfill(2): 0.0 for i in range(100)}
        for num, count in freq.items(): scores[num] = float(count)
        return scores

    def model_overdue_numbers(self, history_df, k):
        last_seen = {str(i).zfill(2): -1 for i in range(100)}
        for i in range(len(history_df)):
            number = history_df.iloc[i]['last2digit']
            last_seen[number] = i 
        scores = {num: float(-idx) for num, idx in last_seen.items()}
        return scores

    def model_short_term_trend(self, history_df, k):
        recent_df = history_df.tail(50)
        freq = recent_df['last2digit'].value_counts()
        scores = {str(i).zfill(2): 0.0 for i in range(100)}
        for num, count in freq.items(): scores[num] = float(count)
        return scores

    def model_hybrid(self, history_df, k):
        freq_scores = history_df['last2digit'].value_counts(normalize=True).to_dict()
        n = len(history_df)
        recency_scores = {str(i).zfill(2): 0.0 for i in range(100)}
        for i in range(n):
            number = history_df.iloc[i]['last2digit']
            recency_scores[number] += (i + 1) / n 
        max_rec = max(recency_scores.values()) if recency_scores.values() else 1
        scores = {str(i).zfill(2): 0.0 for i in range(100)}
        for i in range(100):
            num_str = str(i).zfill(2)
            f_score = freq_scores.get(num_str, 0)
            r_score = recency_scores.get(num_str, 0) / max_rec
            scores[num_str] = (f_score * 0.5) + (r_score * 0.5) 
        return scores

    def get_predictions(self, history_df, model_name, k):
        if model_name == "Recency Weighting": raw_scores = self.model_recency_weighting(history_df, k)
        elif model_name == "Historical Frequency": raw_scores = self.model_historical_frequency(history_df, k)
        elif model_name == "Overdue Numbers": raw_scores = self.model_overdue_numbers(history_df, k)
        elif model_name == "Short-Term Trend (Last 50)": raw_scores = self.model_short_term_trend(history_df, k)
        elif model_name == "Hybrid (Freq + Recency)": raw_scores = self.model_hybrid(history_df, k)
        else: raw_scores = {str(i).zfill(2): 0.0 for i in range(100)}
            
        min_s, max_s = min(raw_scores.values()), max(raw_scores.values())
        final_scores = {}
        for num, score in raw_scores.items():
            norm = ((score - min_s) / (max_s - min_s)) * 100.0 if max_s > min_s else 0.0
            final_scores[num] = norm + (self.feedback_scores[num] * 5.0)

        sorted_scores = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_scores[:k]]

    def safe_get_k(self):
        try: return self.k_var.get()
        except:
            self.k_var.set(5)
            return 5

    def predict_next(self):
        if self.df is None: return messagebox.showwarning("แจ้งเตือน", "กรุณานำเข้าข้อมูลก่อนครับ!")
        k = self.safe_get_k()
        model_name = self.model_var.get()
        predictions = self.get_predictions(self.df, model_name, k)
        
        self.notebook.select(self.tab_log)
        self.log_message(f"\n{'='*55}")
        self.log_message(f"✨ ผลการพยากรณ์งวดถัดไป ✨")
        self.log_message(f"โมเดล: {model_name} (พยากรณ์ {k} ชุด)")
        self.log_message(f"เลขแนะนำ: {', '.join(predictions)}")
        self.log_message(f"{'='*55}")
        
        today_str = datetime.datetime.now().strftime('%d%m%Y')
        default_filename = f"result_{model_name.replace(' ', '_').replace('+', 'and').replace('(', '').replace(')', '')}_{today_str}.txt"
        
        save_path = filedialog.asksaveasfilename(
            title="บันทึกผลการพยากรณ์",
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not save_path:
            self.log_message("[System] ยกเลิกการบันทึกไฟล์")
            return
            
        try:
            with open(save_path, "w", encoding="utf-8-sig") as f:
                f.write("="*55 + "\n")
                f.write(" รายงานผลการพยากรณ์สลากกินแบ่งรัฐบาล (งวดถัดไป)\n")
                f.write("="*55 + "\n")
                f.write(f"วันที่ประมวลผล:   {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"จำนวนฐานข้อมูล:   {len(self.df)} งวด\n")
                f.write(f"อัลกอริทึมที่ใช้:   {model_name}\n")
                f.write("-" * 55 + "\n")
                f.write(f">> เลขที่ระบบแนะนำ (Top {k}): {', '.join(predictions)} <<\n")
                f.write("="*55 + "\n")
            self.log_message(f"[System] บันทึกไฟล์สำเร็จ: {os.path.basename(save_path)}")
        except Exception as e:
            self.log_message(f"[Error] ไม่สามารถสร้างไฟล์ได้: {e}")

    def run_backtest(self):
        if self.df is None: return messagebox.showwarning("แจ้งเตือน", "กรุณานำเข้าข้อมูลก่อนครับ!")
        test_size = 24 
        k = self.safe_get_k()
        model_name = self.model_var.get()
        
        if len(self.df) < test_size + 10:
            return messagebox.showwarning("แจ้งเตือน", "ข้อมูลมีน้อยเกินไปสำหรับการทำ Backtest")
            
        self.notebook.select(self.tab_log)
        self.log_message(f"\n[System] เริ่มการทดสอบย้อนหลัง (Backtesting) ด้วยโมเดล {model_name}...")
        self.progress['maximum'] = test_size
        self.progress['value'] = 0
        self.root.update()
        
        hits = 0
        results = []
        start_idx = len(self.df) - test_size
        
        for idx, i in enumerate(range(start_idx, len(self.df))):
            train_df = self.df.iloc[:i]
            actual_number = self.df.iloc[i]['last2digit']
            draw_date = self.df.iloc[i]['draw_date'].strftime('%Y-%m-%d')
            
            predictions = self.get_predictions(train_df, model_name, k)
            is_hit = actual_number in predictions
            if is_hit: hits += 1
                
            results.append({
                'draw_date': draw_date, 'actual_number': actual_number,
                'predict_list': ", ".join(predictions), 'hit': is_hit
            })
            self.progress['value'] = idx + 1
            self.root.update()
            
        accuracy_percent = (hits / test_size) * 100
        
        # ==========================================
        # การคำนวณจุดคุ้มทุน (ROI & Expected Value)
        # ==========================================
        cost_per_ticket = 80 # ต้นทุนสลากใบละ 80 บาท
        prize_per_hit = 2000 # รางวัลเลขท้าย 2 ตัว 2,000 บาท
        total_investment = test_size * k * cost_per_ticket
        total_return = hits * prize_per_hit
        net_profit = total_return - total_investment
        profit_status = "กำไร (Profit)" if net_profit >= 0 else "ขาดทุน (Loss)"
        
        today_str = datetime.datetime.now().strftime('%d%m%Y')
        default_filename = f"result_{model_name.replace(' ', '_').replace('+', 'and').replace('(', '').replace(')', '')}_{today_str}.txt"
        
        save_path = filedialog.asksaveasfilename(
            title="บันทึกผลการทดสอบ",
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not save_path:
            self.log_message("[System] ทดสอบเสร็จสิ้น (ไม่ได้บันทึกไฟล์รายงาน)")
            return
            
        try:
            with open(save_path, "w", encoding="utf-8-sig") as f:
                f.write("="*80 + "\n")
                f.write(f" รายงานผลการทดสอบความแม่นยำและการวิเคราะห์จุดคุ้มทุน (Walk-forward Backtest)\n")
                f.write(f" โมเดล: {model_name} | พยากรณ์งวดละ: {k} ตัว\n")
                f.write("="*80 + "\n\n")
                
                f.write(f"{'งวดวันที่':<15} | {'ผลจริง':<8} | {'เลขที่พยากรณ์':<25} | {'ผลลัพธ์'}\n")
                f.write("-" * 80 + "\n")
                
                for res in results:
                    status = "[ ทายถูก ]" if res['hit'] else "[ ทายผิด ]"
                    f.write(f"{res['draw_date']:<15} | {res['actual_number']:<8} | {res['predict_list']:<25} | {status}\n")
                
                f.write("\n" + "="*80 + "\n")
                f.write(" สรุปผลการทดสอบเชิงสถิติ (Summary)\n")
                f.write("="*80 + "\n")
                f.write(f"ทดสอบย้อนหลัง:      {test_size} งวด\n")
                f.write(f"จำนวนงวดที่ทายถูก:   {hits} งวด\n")
                f.write(f"ค่าความแม่นยำ (Acc): {accuracy_percent:.2f}%\n")
                
                # เขียนส่วนสรุปผลกำไร/ขาดทุนลงไปใน Text File
                f.write("\n" + "="*80 + "\n")
                f.write(" วิเคราะห์จุดคุ้มทุน (Financial & ROI Analysis)\n")
                f.write("="*80 + "\n")
                f.write(f"ต้นทุนรวมการซื้อสลาก:   {total_investment:,.2f} บาท (งวดที่ทดสอบ {test_size} งวด x ซื้อ {k} ใบ x {cost_per_ticket} บาท)\n")
                f.write(f"เงินรางวัลที่ได้รับรวม:   {total_return:,.2f} บาท (ทายถูก {hits} งวด x {prize_per_hit} บาท)\n")
                f.write(f"ผลกำไร/ขาดทุนสุทธิ:    {net_profit:,.2f} บาท -> [{profit_status}]\n")
                f.write("="*80 + "\n")
                
            self.log_message(f"[System] ทดสอบเสร็จสิ้น! ทายถูก {hits}/{test_size} งวด (ความแม่นยำ {accuracy_percent:.2f}%)")
            self.log_message(f"[System] ผลประกอบการ (ROI): {profit_status} {net_profit:,.2f} บาท")
            self.log_message(f"[System] บันทึกผลทดสอบลงไฟล์: {os.path.basename(save_path)}")
        except Exception as e:
            self.log_message(f"[Error] ไม่สามารถบันทึกไฟล์ Text ได้: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedLotteryApp(root)
    root.mainloop()