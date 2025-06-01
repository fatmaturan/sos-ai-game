import tkinter as tk                      # Tkinter GUI kütüphanesi, arayüz oluşturmak için
from tkinter import ttk, messagebox       # Gelişmiş widgetlar (ttk) ve ileti kutuları (messagebox)
import random                            # Rastgele sayı ve seçim işlemleri için
import pickle                            # Nesneleri dosyaya kaydetme ve yükleme için (serileştirme)
import os                                # Dosya/dizin işlemleri ve işletim sistemi etkileşimi için
import threading                        # Çoklu iş parçacığı (thread) ile eşzamanlı işlemler için


class SOSGame:
    def __init__(self, master):
        # Ana pencereyi başlat ve temel ayarları yap
        self.master = master
        self.master.title("SOS Oyunu ve AI")  # Pencere başlığı
        self.master.geometry("800x700")  # Pencere boyutu
        self.master.resizable(False, False)  # Yeniden boyutlandırmayı kapat
        self.master.configure(bg="#f0f0f0")  # Arka plan rengi

        # Temel oyun değişkenleri
        self.size = 5  # Oyun tahtası boyutu (5x5 sabit)
        self.board = []  # Oyun tahtası durumu
        self.buttons = []  # Tahta üzerindeki butonlar
        self.current_player = 1  # 1 = Oyuncu, 2 = Yapay Zeka
        self.difficulty = "orta"  # Zorluk seviyesi: kolay, orta, zor, imkansız
        self.ai_type = "dt"  # Yapay Zeka tipi: dt (Decision Tree), rf (Random Forest)
        self.scores = {1: 0, 2: 0}  # Oyuncuların skorları
        self.last_move = None  # Son yapılan hamle bilgisi
        self.last_sos_formed = False  # Son hamlede SOS oluştu mu
        self.game_started = False  # Oyun başlatıldı mı
        self.selected_letter = tk.StringVar(value="S")  # Seçilen harf ("S" veya "O")
        self.total_cells = self.size * self.size  # Toplam hücre sayısı
        self.filled_cells = 0  # Doldurulmuş hücre sayısı

        # Makine öğrenmesi modelleri
        self.dt_model = None  # Decision Tree modeli
        self.rf_model = None  # Random Forest modeli
        self.load_models()  # Eğitimli modelleri yükle

        self.show_main_menu()  # Ana menüyü göster

    def load_models(self):
        """Eğitilmiş modelleri yükle"""
        models_dir = "models"  # Modellerin bulunduğu klasör

        # Eğer klasör yoksa oluştur ve kullanıcıya uyarı ver
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
            print("'models' klasörü oluşturuldu. Lütfen eğitilmiş modelleri buraya yerleştirin.")
            return

        # Decision Tree model dosyalarını al
        dt_models = [f for f in os.listdir(models_dir) if f.startswith("sos_dt_") and f.endswith(".pkl")]
        # Random Forest model dosyalarını al
        rf_models = [f for f in os.listdir(models_dir) if f.startswith("sos_rf_") and f.endswith(".pkl")]

        # Decision Tree modelini yükle
        if dt_models:
            dt_models.sort(reverse=True)  # En yeni modeli seç
            dt_model_path = os.path.join(models_dir, dt_models[0])
            try:
                with open(dt_model_path, 'rb') as f:
                    self.dt_model = pickle.load(f)
                print(f"Decision Tree modeli yüklendi: {dt_model_path}")
            except Exception as e:
                print(f"Decision Tree modeli yüklenemedi: {str(e)}")

        # Random Forest modelini yükle
        if rf_models:
            rf_models.sort(reverse=True)  # En yeni modeli seç
            rf_model_path = os.path.join(models_dir, rf_models[0])
            try:
                with open(rf_model_path, 'rb') as f:
                    self.rf_model = pickle.load(f)
                print(f"Random Forest modeli yüklendi: {rf_model_path}")
            except Exception as e:
                print(f"Random Forest modeli yüklenemedi: {str(e)}")

    def show_main_menu(self):

        for widget in self.master.winfo_children():
            widget.destroy()

        menu_frame = tk.Frame(self.master, bg="#f0f0f0", padx=20, pady=20)
        menu_frame.pack(expand=True, fill="both")

        title_label = tk.Label(menu_frame, text="SOS OYUNU", font=("Arial", 36, "bold"),
                              fg="#3a7ebf", bg="#f0f0f0")
        title_label.pack(pady=30)
        desc_text = """
SOS oyununda amaç, yatay, dikey veya çapraz olarak S-O-S harflerini yan yana getirmektir. 
Her SOS oluşturduğunuzda 1 puan kazanır ve tekrar hamle yapma hakkı elde edersiniz.
En çok puan toplayan oyuncu kazanır.
    """

        desc_label = tk.Label(menu_frame, text=desc_text, font=("Arial", 12),
                             justify="left", fg="#555555", bg="#f0f0f0")
        desc_label.pack(pady=10)

        diff_frame = tk.Frame(menu_frame, bg="#f0f0f0")
        diff_frame.pack(pady=15)

        diff_label = tk.Label(diff_frame, text="Zorluk Seviyesi:", font=("Arial", 12),
                             fg="#333333", bg="#f0f0f0")
        diff_label.pack(side="top", pady=5)

        self.diff_var = tk.StringVar(value="orta")

        diff_styles = {
            "kolay": {"bg": "#a8e6cf", "text": "Kolay", "desc": "Yapay Zeka, rastgele ve zayıf hamleler yapar"},
            "orta": {"bg": "#fdffab", "text": "Orta", "desc": "Yapay Zeka, karışık seviyede hamleler yapar"},
            "zor": {"bg": "#ffaaa5", "text": "Zor", "desc": "Yapay Zeka, güçlü ve stratejik hamleler yapar"},
            "imkansız": {"bg": "#ff8b94", "text": "İmkansız", "desc": "Tam kural bazlı, mükemmele yakın hamleler yapar"}
        }

        diff_buttons_frame = tk.Frame(diff_frame, bg="#f0f0f0")
        diff_buttons_frame.pack(pady=10)

        for i, diff in enumerate(["kolay", "orta", "zor", "imkansız"]):
            style = diff_styles[diff]
            diff_btn = tk.Radiobutton(diff_buttons_frame, text=style["text"], variable=self.diff_var,
                                     value=diff, font=("Arial", 12, "bold"), bg=style["bg"],
                                     selectcolor=style["bg"], indicatoron=0, width=10, height=2,
                                     command=lambda d=diff: self.update_diff_desc(d))
            diff_btn.grid(row=0, column=i, padx=5)

        self.diff_desc = tk.Label(diff_frame, text=diff_styles["orta"]["desc"],
                                font=("Arial", 10, "italic"), fg="#555555", bg="#f0f0f0")
        self.diff_desc.pack(pady=5)

        ai_frame = tk.Frame(menu_frame, bg="#f0f0f0")
        ai_frame.pack(pady=15)

        ai_label = tk.Label(ai_frame, text="AI Algoritması:", font=("Arial", 12),
                           fg="#333333", bg="#f0f0f0")
        ai_label.pack(side="top", pady=5)

        self.ai_var = tk.StringVar(value="dt")

        ai_styles = {
            "dt": {"bg": "#bae1ff", "text": "Decision Tree", "desc": "Karar ağacı algoritması"},
            "rf": {"bg": "#b2fab4", "text": "Random Forest", "desc": "Rastgele orman algoritması"}
        }

        ai_buttons_frame = tk.Frame(ai_frame, bg="#f0f0f0")
        ai_buttons_frame.pack(pady=10)

        for i, ai_type in enumerate(["dt", "rf"]):
            style = ai_styles[ai_type]

            state = "normal"
            if ai_type == "dt" and self.dt_model is None:
                state = "disabled"
            elif ai_type == "rf" and self.rf_model is None:
                state = "disabled"

            ai_btn = tk.Radiobutton(ai_buttons_frame, text=style["text"], variable=self.ai_var,
                                   value=ai_type, font=("Arial", 12, "bold"), bg=style["bg"],
                                   selectcolor=style["bg"], indicatoron=0, width=12, height=2,
                                   command=lambda a=ai_type: self.update_ai_desc(a),
                                   state=state)
            ai_btn.grid(row=0, column=i, padx=5)

        self.ai_desc = tk.Label(ai_frame, text=ai_styles["dt"]["desc"],
                              font=("Arial", 10, "italic"), fg="#555555", bg="#f0f0f0")
        self.ai_desc.pack(pady=5)

        # Model durumu
        model_frame = tk.Frame(menu_frame, bg="#f0f0f0")
        model_frame.pack(pady=5)

        dt_status = "Yüklendi" if self.dt_model else "Yüklenemedi"
        dt_color = "#007700" if self.dt_model else "#cc0000"

        rf_status = "Yüklendi" if self.rf_model else "Yüklenemedi"
        rf_color = "#007700" if self.rf_model else "#cc0000"

        model_status_text = f"Decision Tree: {dt_status} | Random Forest: {rf_status}"
        model_status = tk.Label(model_frame, text=model_status_text,
                              font=("Arial", 10), fg="#555555", bg="#f0f0f0")
        model_status.pack(pady=5)

        start_button = tk.Button(menu_frame, text="OYUNU BAŞLAT", font=("Arial", 16, "bold"),
                               bg="#3a7ebf", fg="white", padx=20, pady=10, width=20, height=2,
                               command=self.start_game)
        start_button.pack(pady=20)

        train_button = tk.Button(menu_frame, text="Modelleri Yeniden Eğit", font=("Arial", 12),
                               bg="#bf3a3a", fg="white", padx=10, pady=5,
                               command=self.show_training_options)
        train_button.pack(pady=10)

        creator_label = tk.Label(menu_frame, text="© 2025 SOS Oyunu",
                               font=("Arial", 8), fg="#999999", bg="#f0f0f0")
        creator_label.pack(side="bottom", pady=10)

    def update_diff_desc(self, difficulty):
        """Zorluk seviyesi açıklamasını güncelle"""
        diff_styles = {
            "kolay": {"bg": "#a8e6cf", "text": "Kolay", "desc": "Yapay Zeka, rastgele ve zayıf hamleler yapar"},
            "orta": {"bg": "#fdffab", "text": "Orta", "desc": "Yapay Zeka, karışık seviyede hamleler yapar"},
            "zor": {"bg": "#ffaaa5", "text": "Zor", "desc": "Yapay Zeka, güçlü ve stratejik hamleler yapar"},
            "imkansız": {"bg": "#ff8b94", "text": "İmkansız", "desc": "Tam kural bazlı, mükemmele yakın hamleler yapar"}
        }

        self.diff_desc.config(text=diff_styles[difficulty]["desc"])

    def update_ai_desc(self, ai_type):
        """AI algoritması açıklamasını güncelle"""
        ai_styles = {
            "dt": {"bg": "#bae1ff", "text": "Decision Tree", "desc": "Karar ağacı algoritması"},
            "rf": {"bg": "#b2fab4", "text": "Random Forest", "desc": "Rastgele orman algoritması"}
        }

        self.ai_desc.config(text=ai_styles[ai_type]["desc"])

    def show_training_options(self):
        """Eğitim seçeneklerini göster"""
        train_window = tk.Toplevel(self.master)
        train_window.title("Modelleri Yeniden Eğit")
        train_window.geometry("400x300")
        train_window.transient(self.master)
        train_window.grab_set()

        train_frame = tk.Frame(train_window, bg="#f0f0f0", padx=20, pady=20)
        train_frame.pack(expand=True, fill="both")

        title_label = tk.Label(train_frame, text="MODEL EĞİTİMİ", font=("Arial", 20, "bold"),
                              fg="#bf3a3a", bg="#f0f0f0")
        title_label.pack(pady=10)

        desc_text = """
Bu işlem modelleri yeniden eğitmek için arka planda çok sayıda oyun oynatacak 
ve yapay zeka modellerini eğitecektir. Bu işlem birkaç dakika sürebilir.
        """
        desc_label = tk.Label(train_frame, text=desc_text, font=("Arial", 12),
                             justify="left", fg="#555555", bg="#f0f0f0")
        desc_label.pack(pady=10)

        games_frame = tk.Frame(train_frame, bg="#f0f0f0")
        games_frame.pack(pady=10)

        games_label = tk.Label(games_frame, text="Oyun Sayısı:", font=("Arial", 12),
                              fg="#333333", bg="#f0f0f0")
        games_label.grid(row=0, column=0, padx=5, sticky="w")

        self.train_games_var = tk.IntVar(value=1000)
        games_entry = tk.Entry(games_frame, textvariable=self.train_games_var, font=("Arial", 12),
                              width=10)
        games_entry.grid(row=0, column=1, padx=5)

        buttons_frame = tk.Frame(train_frame, bg="#f0f0f0")
        buttons_frame.pack(pady=20)

        cancel_button = tk.Button(buttons_frame, text="İptal", font=("Arial", 12),
                                bg="#cccccc", fg="#333333", padx=10, pady=5,
                                command=train_window.destroy)
        cancel_button.grid(row=0, column=0, padx=10)

        train_button = tk.Button(buttons_frame, text="Eğitimi Başlat", font=("Arial", 12, "bold"),
                               bg="#bf3a3a", fg="white", padx=10, pady=5,
                               command=lambda: self.start_training(train_window))
        train_button.grid(row=0, column=1, padx=10)

    def start_training(self, train_window):
        """Eğitimi başlat"""
        num_games = self.train_games_var.get()

        train_window.destroy()

        progress_window = tk.Toplevel(self.master)
        progress_window.title("Model Eğitimi")
        progress_window.geometry("400x200")
        progress_window.transient(self.master)
        progress_window.grab_set()

        progress_frame = tk.Frame(progress_window, bg="#f0f0f0", padx=20, pady=20)
        progress_frame.pack(expand=True, fill="both")


        title_label = tk.Label(progress_frame, text="MODEL EĞİTİMİ DEVAM EDİYOR",
                              font=("Arial", 14, "bold"), fg="#bf3a3a", bg="#f0f0f0")
        title_label.pack(pady=10)

        desc_label = tk.Label(progress_frame,
                             text=f"5x5 tahta için {num_games} oyun oluşturuluyor...",
                             font=("Arial", 10), fg="#555555", bg="#f0f0f0")
        desc_label.pack(pady=5)

        progress_var = tk.DoubleVar(value=0)
        progress_bar = ttk.Progressbar(progress_frame, variable=progress_var,
                                      orient="horizontal", length=300, mode="indeterminate")
        progress_bar.pack(pady=10)
        progress_bar.start(10)

        info_label = tk.Label(progress_frame, text="Bu işlem birkaç dakika sürebilir...",
                             font=("Arial", 10, "italic"), fg="#555555", bg="#f0f0f0")
        info_label.pack(pady=5)


        self.master.update()

        def training_thread():
            try:
                from ai_trainer import train_and_save_models
                model_paths = train_and_save_models(5, num_games)
                
                # Eğitim tamamlandı penceresi
                progress_window.destroy()
                
                # Modelleri yükle
                self.load_models()
                
                messagebox.showinfo("Eğitim Tamamlandı", 
                                  f"Modeller başarıyla eğitildi ve kaydedildi!\n\n"
                                  f"Decision Tree: {model_paths['dt_model']}\n"
                                  f"Random Forest: {model_paths['rf_model']}")
                
                # Ana menüyü yenile
                self.show_main_menu()
                
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("Eğitim Hatası", f"Eğitim sırasında bir hata oluştu:\n{str(e)}")
        
        thread = threading.Thread(target=training_thread)
        thread.daemon = True
        thread.start()
    
    def start_game(self):
        """Oyunu başlat"""
        self.difficulty = self.diff_var.get()
        self.ai_type = self.ai_var.get()
        self.total_cells = self.size * self.size
        self.filled_cells = 0
        
        # Bazı AI tipleri için model kontrolleri
        if self.ai_type == "dt" and self.dt_model is None:
            messagebox.showwarning("Model Eksik", 
                                 "Decision Tree modeli yüklenemedi! Lütfen başka bir AI tipi seçin.")
            return
        
        if self.ai_type == "rf" and self.rf_model is None:
            messagebox.showwarning("Model Eksik", 
                                 "Random Forest modeli yüklenemedi! Lütfen başka bir AI tipi seçin.")
            return
        
        self.board = [[' ' for _ in range(self.size)] for _ in range(self.size)]
        self.current_player = 1  # İnsan her zaman başlar
        self.scores = {1: 0, 2: 0}
        self.last_move = None
        self.last_sos_formed = False
        self.game_started = True
        
        # Temizle
        for widget in self.master.winfo_children():
            widget.destroy()
        
        # Oyun arayüzünü oluştur
        self.create_game_interface()
    
    def create_game_interface(self):
        """Oyun arayüzünü oluştur"""
        main_frame = tk.Frame(self.master, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Üst bilgi çerçevesi
        info_frame = tk.Frame(main_frame, bg="#f0f0f0")
        info_frame.pack(fill="x", pady=10)
        
        # Oyun başlığı
        title_label = tk.Label(info_frame, text="SOS OYUNU", font=("Arial", 20, "bold"), 
                              fg="#3a7ebf", bg="#f0f0f0")
        title_label.pack(side="left", padx=10)
        
        # Ayarlar bilgisi
        ai_desc = {
            "dt": "Decision Tree",
            "rf": "Random Forest"
        }
        
        settings_text = f"Tahta: 5x5 | Zorluk: {self.difficulty.title()} | AI: {ai_desc[self.ai_type]}"
        settings_label = tk.Label(info_frame, text=settings_text, font=("Arial", 10), 
                                 fg="#555555", bg="#f0f0f0")
        settings_label.pack(side="left", padx=10)
        
        # Skor çerçevesi
        score_frame = tk.Frame(main_frame, bg="#f0f0f0")
        score_frame.pack(fill="x", pady=10)
        
        # Oyuncu skoru
        player_frame = tk.Frame(score_frame, bg="#e6f2ff", padx=15, pady=10)
        player_frame.pack(side="left", expand=True, fill="x", padx=5)
        
        player_label = tk.Label(player_frame, text="Oyuncu (İnsan)", font=("Arial", 12, "bold"), 
                              fg="#3a7ebf", bg="#e6f2ff")
        player_label.pack()
        
        self.player_score_label = tk.Label(player_frame, text="0", font=("Arial", 24, "bold"), 
                                         fg="#3a7ebf", bg="#e6f2ff")
        self.player_score_label.pack()
        
        # AI skoru
        ai_frame = tk.Frame(score_frame, bg="#ffe6e6", padx=15, pady=10)
        ai_frame.pack(side="right", expand=True, fill="x", padx=5)
        
        ai_label = tk.Label(ai_frame, text=f"Oyuncu (AI - {ai_desc[self.ai_type]})", 
                           font=("Arial", 12, "bold"), fg="#bf3a3a", bg="#ffe6e6")
        ai_label.pack()
        
        self.ai_score_label = tk.Label(ai_frame, text="0", font=("Arial", 24, "bold"), 
                                     fg="#bf3a3a", bg="#ffe6e6")
        self.ai_score_label.pack()
        
        # Son hamle bilgisi
        self.move_info_label = tk.Label(main_frame, text="Oyun başladı! Hamle yapın.", 
                                      font=("Arial", 10, "italic"), fg="#555555", bg="#f0f0f0")
        self.move_info_label.pack(pady=10)
        
        # Tahta çerçevesi
        board_outer_frame = tk.Frame(main_frame, bg="#cccccc", padx=3, pady=3)
        board_outer_frame.pack(padx=10, pady=10)
        
        board_frame = tk.Frame(board_outer_frame, bg="white")
        board_frame.pack()
        
        # Tahta düğmelerini oluştur
        self.buttons = []
        button_size = 60  # Sabit düğme boyutu
        
        for i in range(self.size):
            row_buttons = []
            for j in range(self.size):
                btn = tk.Button(board_frame, text="", font=("Arial", 16, "bold"),
                              width=2, height=1, padx=10, pady=5,
                              relief="raised", bg="white",
                              command=lambda r=i, c=j: self.make_move(r, c))
                # Düğme boyutlarını sabit yap
                btn.config(width=3, height=1)
                btn.grid(row=i, column=j, padx=2, pady=2)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)
        
        # Harf seçimi çerçevesi
        letter_frame = tk.Frame(main_frame, bg="#f0f0f0")
        letter_frame.pack(pady=15)
        
        letter_label = tk.Label(letter_frame, text="Harf Seçin:", font=("Arial", 12), 
                              fg="#333333", bg="#f0f0f0")
        letter_label.pack(side="left", padx=10)
        
        s_radio = tk.Radiobutton(letter_frame, text="S", variable=self.selected_letter, 
                                value="S", font=("Arial", 14, "bold"))
        s_radio.pack(side="left", padx=10)
        
        o_radio = tk.Radiobutton(letter_frame, text="O", variable=self.selected_letter, 
                                value="O", font=("Arial", 14, "bold"))
        o_radio.pack(side="left", padx=10)
        
        # Kazanma ihtimali çerçevesi
        prob_frame = tk.Frame(main_frame, bg="#f0f0f0")
        prob_frame.pack(fill="x", pady=15)
        
        prob_label = tk.Label(prob_frame, text="Kazanma İhtimali:", font=("Arial", 12, "bold"), 
                             fg="#333333", bg="#f0f0f0")
        prob_label.pack(pady=5)
        
        # Oyuncu ihtimali
        player_prob_frame = tk.Frame(prob_frame, bg="#f0f0f0")
        player_prob_frame.pack(fill="x", pady=2)
        
        player_prob_label = tk.Label(player_prob_frame, text="İnsan:", font=("Arial", 10), 
                                    fg="#3a7ebf", bg="#f0f0f0", width=8, anchor="e")
        player_prob_label.pack(side="left", padx=5)
        
        self.player_prob_canvas = tk.Canvas(player_prob_frame, height=20, bg="white", 
                                          highlightthickness=1, highlightbackground="#cccccc")
        self.player_prob_canvas.pack(side="left", fill="x", expand=True, padx=5)
        
        self.player_prob_value = tk.Label(player_prob_frame, text="50.0%", font=("Arial", 10), 
                                        fg="#3a7ebf", bg="#f0f0f0", width=8, anchor="w")
        self.player_prob_value.pack(side="left", padx=5)
        
        # AI ihtimali
        ai_prob_frame = tk.Frame(prob_frame, bg="#f0f0f0")
        ai_prob_frame.pack(fill="x", pady=2)
        
        ai_prob_label = tk.Label(ai_prob_frame, text="AI:", font=("Arial", 10), 
                               fg="#bf3a3a", bg="#f0f0f0", width=8, anchor="e")
        ai_prob_label.pack(side="left", padx=5)
        
        self.ai_prob_canvas = tk.Canvas(ai_prob_frame, height=20, bg="white", 
                                      highlightthickness=1, highlightbackground="#cccccc")
        self.ai_prob_canvas.pack(side="left", fill="x", expand=True, padx=5)
        
        self.ai_prob_value = tk.Label(ai_prob_frame, text="50.0%", font=("Arial", 10), 
                                    fg="#bf3a3a", bg="#f0f0f0", width=8, anchor="w")
        self.ai_prob_value.pack(side="left", padx=5)
        
        # Menüye dön düğmesi
        menu_button = tk.Button(main_frame, text="Ana Menüye Dön", font=("Arial", 10),
                              bg="#cccccc", fg="#333333", 
                              command=self.show_main_menu)
        menu_button.pack(side="bottom", pady=10)
        
        # İlk olasılıkları göster
        self.update_win_probabilities()
    
    def make_move(self, row, col):
        """Bir hamle yap"""
        if self.board[row][col] != ' ' or self.current_player != 1 or not self.game_started:
            return
        
        letter = self.selected_letter.get()
        self.board[row][col] = letter
        self.buttons[row][col].config(text=letter, bg="#e6f2ff", fg="#3a7ebf", state="disabled")
        self.filled_cells += 1
        self.last_move = (row, col)
        
        # SOS kontrolü
        sos_formed = self.check_sos(row, col)
        self.last_sos_formed = sos_formed
        
        if sos_formed:
            self.scores[self.current_player] += 1
            self.player_score_label.config(text=str(self.scores[1]))
            self.move_info_label.config(text=f"SOS oluşturdunuz! Ekstra hamle hakkı kazandınız.", fg="#007700")
        else:
            self.current_player = 2  # AI's turn
            self.move_info_label.config(text="AI düşünüyor...", fg="#555555")
            self.master.update()
            self.master.after(1000, self.ai_move)  # 1 saniye sonra AI hamlesi
        
        # Kazanma olasılıklarını güncelle
        self.update_win_probabilities()
        
        # Oyun sonu kontrolü
        if self.filled_cells == self.total_cells:
            self.game_over()
    
    def update_win_probabilities(self):#kazanma olasığını hesaplıyorum
        """Kazanma olasılıklarını güncelle"""
        remaining_moves = self.total_cells - self.filled_cells
        player_score = self.scores[1]
        ai_score = self.scores[2]
        
        if player_score == ai_score:
            player_prob = 0.5
            ai_prob = 0.5
        else:
            # Kalan hamle sayısı azaldıkça skor farkının etkisi artar
            lead_ratio = abs(player_score - ai_score) / (remaining_moves / 3 + 0.1)
            lead_ratio = min(lead_ratio, 0.9)  # Maksimum %90
            
            if player_score > ai_score:
                player_prob = 0.5 + lead_ratio / 2
                ai_prob = 1 - player_prob
            else:
                ai_prob = 0.5 + lead_ratio / 2
                player_prob = 1 - ai_prob
        
        # İhtimal çubuklarını güncelle
        self.player_prob_canvas.delete("all")
        self.ai_prob_canvas.delete("all")
        
        # Canvas boyutunu kontrol et
        self.master.update_idletasks()  # Güncellemeleri zorla
        canvas_width = self.player_prob_canvas.winfo_width()
        if canvas_width <= 1:  # Canvas henüz oluşturulmadıysa
            canvas_width = 300  # Varsayılan genişlik
        
        # Oyuncu çubuğu
        player_width = int(canvas_width * player_prob)
        self.player_prob_canvas.create_rectangle(0, 0, player_width, 20, fill="#3a7ebf", outline="")
        self.player_prob_value.config(text=f"{player_prob:.1%}")
        
        # AI çubuğu
        ai_width = int(canvas_width * ai_prob)
        self.ai_prob_canvas.create_rectangle(0, 0, ai_width, 20, fill="#bf3a3a", outline="")
        self.ai_prob_value.config(text=f"{ai_prob:.1%}")
    
    def check_sos(self, row, col):
        """SOS oluşup oluşmadığını kontrol et"""
        letter = self.board[row][col]
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # Yatay, dikey ve çaprazlar
        
        sos_formed = False
        
        if letter == 'S':
            # Bu S bir SOS'un başlangıcı mı?
            for dr, dc in directions:
                if (0 <= row + 2*dr < self.size and 
                    0 <= col + 2*dc < self.size and
                    self.board[row + dr][col + dc] == 'O' and
                    self.board[row + 2*dr][col + 2*dc] == 'S'):
                    sos_formed = True
                    self.highlight_sos(row, col, dr, dc)
            
            # Bu S bir SOS'un sonu mu?
            for dr, dc in directions:
                if (0 <= row - 2*dr < self.size and 
                    0 <= col - 2*dc < self.size and
                    self.board[row - dr][col - dc] == 'O' and
                    self.board[row - 2*dr][col - 2*dc] == 'S'):
                    sos_formed = True
                    self.highlight_sos(row - 2*dr, col - 2*dc, dr, dc)
                    
        elif letter == 'O':
            # Bu O bir SOS'un ortası mı?
            for dr, dc in directions:
                if (0 <= row - dr < self.size and 
                    0 <= col - dc < self.size and
                    0 <= row + dr < self.size and 
                    0 <= col + dc < self.size and
                    self.board[row - dr][col - dc] == 'S' and
                    self.board[row + dr][col + dc] == 'S'):
                    sos_formed = True
                    self.highlight_sos(row - dr, col - dc, dr, dc)
        
        return sos_formed
    
    def highlight_sos(self, start_row, start_col, dr, dc):
        """SOS'u vurgula"""
        # SOS vurgulama renkleri
        colors = {1: "#a8e6cf", 2: "#ffaaa5"}  # 1-İnsan için yeşil, 2-AI için kırmızı
        
        # SOS'u vurgula
        for i in range(3):
            r, c = start_row + i*dr, start_col + i*dc
            self.buttons[r][c].config(bg=colors[self.current_player])
            
            # 0.5 saniye sonra orijinal rengine döndür
            self.master.after(500, lambda row=r, cow=c, player=self.current_player:
                             self.reset_highlight(r, c, player))
    
    def reset_highlight(self, row, col, player):
        """Vurgulamayı kaldır"""
        # Orijinal renkler
        colors = {1: "#e6f2ff", 2: "#ffe6e6"}  # 1-İnsan için mavi, 2-AI için kırmızı
        
        self.buttons[row][col].config(bg=colors[player])
    
    def ai_move(self):
        """AI hamlesini yap"""
        if not self.game_started or self.filled_cells == self.total_cells:
            return
        
        # Zorluk seviyesine göre AI hamlesini belirle
        if self.difficulty == "imkansız":
            # İmkansız zorluk seviyesi her zaman kural bazlı çalışsın
            row, col, letter = self.rule_based_move_hard()
        else:
            # Diğer zorluk seviyeleri için seçilen modeli kullan
            if self.ai_type == "dt":
                if self.dt_model is None:
                    # Model yoksa kural bazlı kullan
                    row, col, letter = self.rule_based_move(self.difficulty)
                else:
                    # Zorluk seviyesine göre model kullanım oranını ayarla
                    if self.difficulty == "kolay" and random.random() < 0.7:
                        row, col, letter = self.rule_based_move_easy()
                    elif self.difficulty == "orta" and random.random() < 0.4:
                        row, col, letter = self.rule_based_move_medium()
                    else:
                        row, col, letter = self.model_based_move(self.dt_model)
            else:  # "rf"
                if self.rf_model is None:
                    # Model yoksa kural bazlı kullan
                    row, col, letter = self.rule_based_move(self.difficulty)
                else:
                    # Zorluk seviyesine göre model kullanım oranını ayarla
                    if self.difficulty == "kolay" and random.random() < 0.7:
                        row, col, letter = self.rule_based_move_easy()
                    elif self.difficulty == "orta" and random.random() < 0.4:
                        row, col, letter = self.rule_based_move_medium()
                    else:
                        row, col, letter = self.model_based_move(self.rf_model)
        
        # Hamleyi yap
        if row is not None and col is not None and letter is not None:
            self.board[row][col] = letter
            self.buttons[row][col].config(text=letter, bg="#ffe6e6", fg="#bf3a3a", state="disabled")
            self.filled_cells += 1
            self.last_move = (row, col)
            
            # SOS kontrolü
            sos_formed = self.check_sos(row, col)
            self.last_sos_formed = sos_formed
            
            if sos_formed:
                self.scores[self.current_player] += 1
                self.ai_score_label.config(text=str(self.scores[2]))
                self.move_info_label.config(text=f"AI bir SOS oluşturdu! Ekstra hamle kazandı.", fg="#990000")
                
                # AI tekrar hamle yapar
                self.master.after(1500, self.ai_move)
            else:
                self.current_player = 1  # İnsanın sırası
                self.move_info_label.config(text="Sizin sıranız. Bir hücre seçin ve S veya O yerleştirin.", fg="#3a7ebf")
            
            # Kazanma ihtimallerini güncelle
            self.update_win_probabilities()
            
            # Oyun sonu kontrolü
            if self.filled_cells == self.total_cells:
                self.game_over()
    
    def rule_based_move(self, difficulty=None):
        """Kural bazlı bir hamle yap"""
        if difficulty is None:
            difficulty = self.difficulty
        
        if difficulty == "kolay":
            return self.rule_based_move_easy()
        elif difficulty == "orta":
            # %70 zor, %30 kolay
            if random.random() < 0.7:
                return self.rule_based_move_medium()
            else:
                return self.rule_based_move_easy()
        elif difficulty == "zor":
            return self.rule_based_move_medium()
        else:  # imkansız
            return self.rule_based_move_hard()
    
    def rule_based_move_easy(self):
        """Kolay seviye için rastgele hamle yap"""
        # Boş hücreleri bul
        empty_cells = []
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == ' ':
                    empty_cells.append((i, j))
        
        if not empty_cells:
            return None, None, None
        
        # Rastgele bir hücre ve harf seç
        row, col = random.choice(empty_cells)
        letter = random.choice(['S', 'O'])
        
        return row, col, letter
    
    def rule_based_move_medium(self):
        """Orta seviye için yarı akıllı hamle yap"""
        # 1. Önce SOS oluşturabileceğimiz bir hamle var mı kontrol et
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == ' ':
                    # S ile SOS oluşturabilir miyiz?
                    self.board[i][j] = 'S'
                    if self.check_sos(i, j):
                        self.board[i][j] = ' '  # Tahtayı geri al
                        return i, j, 'S'
                    
                    # O ile SOS oluşturabilir miyiz?
                    self.board[i][j] = 'O'
                    if self.check_sos(i, j):
                        self.board[i][j] = ' '  # Tahtayı geri al
                        return i, j, 'O'
                    
                    self.board[i][j] = ' '  # Tahtayı geri al
        
        # 2. Basit hamle yap
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == ' ':
                    # O için S-O-? veya ?-O-S durumları
                    if self.check_letter_potential(i, j, 'O'):
                        return i, j, 'O'
        
        # 3. Rastgele hamle yap
        return self.rule_based_move_easy()
    
    def rule_based_move_hard(self):
        """Zor seviye için akıllı hamle yap"""
        # 1. Önce SOS oluşturabileceğimiz bir hamle var mı kontrol et
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == ' ':
                    # S ile SOS oluşturabilir miyiz?
                    self.board[i][j] = 'S'
                    if self.check_sos(i, j):
                        self.board[i][j] = ' '  # Tahtayı geri al
                        return i, j, 'S'
                    
                    # O ile SOS oluşturabilir miyiz?
                    self.board[i][j] = 'O'
                    if self.check_sos(i, j):
                        self.board[i][j] = ' '  # Tahtayı geri al
                        return i, j, 'O'
                    
                    self.board[i][j] = ' '  # Tahtayı geri al
        
        # 2. Rakibin SOS oluşturmasını engelleyecek bir hamle var mı kontrol et
        original_player = self.current_player
        opponent = 1  # İnsan
        
        self.current_player = opponent  # Geçici olarak rakibin sırası
        
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == ' ':
                    # Rakip S ile SOS oluşturabilir mi?
                    self.board[i][j] = 'S'
                    if self.check_sos(i, j):
                        self.board[i][j] = ' '  # Tahtayı geri al
                        self.current_player = original_player  # Oyuncuyu geri al
                        return i, j, 'S'
                    
                    # Rakip O ile SOS oluşturabilir mi?
                    self.board[i][j] = 'O'
                    if self.check_sos(i, j):
                        self.board[i][j] = ' '  # Tahtayı geri al
                        self.current_player = original_player  # Oyuncuyu geri al
                        return i, j, 'O'
                    
                    self.board[i][j] = ' '  # Tahtayı geri al
        
        self.current_player = original_player  # Oyuncuyu geri al
        
        # 3. Stratejik hamle yap
        strategic_moves = []
        
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == ' ':
                    # O harfi potansiyeli
                    o_score = self.evaluate_move(i, j, 'O')
                    strategic_moves.append((o_score, i, j, 'O'))
                    
                    # S harfi potansiyeli
                    s_score = self.evaluate_move(i, j, 'S')
                    strategic_moves.append((s_score, i, j, 'S'))
        
        if strategic_moves:
            strategic_moves.sort(reverse=True)  # En yüksek puanlı hamleyi seç
            return strategic_moves[0][1], strategic_moves[0][2], strategic_moves[0][3]
        
        # 4. Hiçbir şey bulunamazsa rastgele hamle yap
        return self.rule_based_move_easy()
    
    def check_letter_potential(self, row, col, letter):
        """Bir harfin potansiyel SOS oluşturma ihtimalini kontrol et"""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        if letter == 'O':
            for dr, dc in directions:
                # S-O-? durumu
                if (0 <= row - dr < self.size and 0 <= col - dc < self.size and
                    0 <= row + dr < self.size and 0 <= col + dc < self.size and
                    self.board[row - dr][col - dc] == 'S' and self.board[row + dr][col + dc] == ' '):
                    return True
                
                # ?-O-S durumu
                if (0 <= row - dr < self.size and 0 <= col - dc < self.size and
                    0 <= row + dr < self.size and 0 <= col + dc < self.size and
                    self.board[row - dr][col - dc] == ' ' and self.board[row + dr][col + dc] == 'S'):
                    return True
        
        elif letter == 'S':
            for dr, dc in directions:
                if (0 <= row + 2*dr < self.size and 0 <= col + 2*dc < self.size and
                    self.board[row + dr][col + dc] == ' ' and self.board[row + 2*dr][col + 2*dc] == ' '):
                    return True
                
                if (0 <= row - 2*dr < self.size and 0 <= col - 2*dc < self.size and
                    self.board[row - dr][col - dc] == ' ' and self.board[row - 2*dr][col - 2*dc] == ' '):
                    return True
        
        return False
    
    def evaluate_move(self, row, col, letter):
        """Bir hamlenin stratejik değerini hesapla"""
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        if letter == 'S':
            for dr, dc in directions:
                if (0 <= row + 2*dr < self.size and 0 <= col + 2*dc < self.size):
                    if self.board[row + dr][col + dc] == 'O' and self.board[row + 2*dr][col + 2*dc] == ' ':
                        score += 3  # Potansiyel SOS
                    elif self.board[row + dr][col + dc] == ' ' and self.board[row + 2*dr][col + 2*dc] == 'S':
                        score += 2  # S-?-S durumu
                    elif self.board[row + dr][col + dc] == ' ' and self.board[row + 2*dr][col + 2*dc] == ' ':
                        score += 1  # Başlangıç
                
                if (0 <= row - 2*dr < self.size and 0 <= col - 2*dc < self.size):
                    if self.board[row - dr][col - dc] == 'O' and self.board[row - 2*dr][col - 2*dc] == ' ':
                        score += 3  # Potansiyel SOS
                    elif self.board[row - dr][col - dc] == ' ' and self.board[row - 2*dr][col - 2*dc] == 'S':
                        score += 2  # S-?-S durumu
                    elif self.board[row - dr][col - dc] == ' ' and self.board[row - 2*dr][col - 2*dc] == ' ':
                        score += 1  # Başlangıç
        
        elif letter == 'O':
            for dr, dc in directions:
                # ?-O-? durumu
                if (0 <= row - dr < self.size and 0 <= col - dc < self.size and
                    0 <= row + dr < self.size and 0 <= col + dc < self.size):
                    if self.board[row - dr][col - dc] == 'S' and self.board[row + dr][col + dc] == 'S':
                        score += 10  # Kesin SOS
                    elif self.board[row - dr][col - dc] == 'S' and self.board[row + dr][col + dc] == ' ':
                        score += 3  # S-O-? durumu
                    elif self.board[row - dr][col - dc] == ' ' and self.board[row + dr][col + dc] == 'S':
                        score += 3  # ?-O-S durumu
                    elif self.board[row - dr][col - dc] == ' ' and self.board[row + dr][col + dc] == ' ':
                        score += 1  # Başlangıç
        
        original_player = self.current_player
        opponent = 1  # İnsan
        
        self.current_player = opponent
        self.board[row][col] = letter
        
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == ' ':
                    self.board[i][j] = 'S'
                    if self.check_sos(i, j):
                        score -= 5  
                    self.board[i][j] = ' '
                    
                    self.board[i][j] = 'O'
                    if self.check_sos(i, j):
                        score -= 5  
                    self.board[i][j] = ' '
        
        self.board[row][col] = ' '
        self.current_player = original_player
        
        return score

    def model_based_move(self, model):
        """Eğitilmiş makine öğrenmesi modelini kullanarak hamle yapar"""

        # Eğer model None ise, kural tabanlı hamle yap
        if model is None:
            return self.rule_based_move()

        # Mevcut tahta durumundan özellikler çıkar
        features = self.extract_features()# tahtayı vektöre çevirir

        try:
            # Modeli kullanarak tahmin yap; model.predict girdi olarak liste bekler
            move_str = model.predict([features])[0]# en uygun hamleyi verir

            # Tahmin sonucu "satır,sütun,harf" şeklinde string döner, parçala
            row, col, letter = move_str.split(",")

            # Satır ve sütun indekslerini tam sayıya çevir
            row, col = int(row), int(col)

            # Eğer önerilen hücre boş değilse (daha önce doluysa)
            if self.board[row][col] != ' ':
                # Zorluk seviyesine göre kural tabanlı kolay, orta veya zor hamle yap
                if self.difficulty == "kolay":
                    return self.rule_based_move_easy()
                elif self.difficulty == "orta":
                    return self.rule_based_move_medium()
                else:
                    return self.rule_based_move_hard()

            # Eğer hücre boşsa tahmin edilen hamleyi döndür
            return row, col, letter

        except Exception as e:
            # Tahmin sırasında hata olursa hata mesajını yazdır ve kural tabanlı hamle yap
            print(f"Model tahmininde hata: {str(e)}")
            return self.rule_based_move()

    def extract_features(self):#tahtayı vektöre çevirir
        """Tahtadaki hücre durumlarına göre model için özellik vektörü oluşturur"""

        features = []  # Özellikleri tutacak liste

        # Tahtadaki her hücre için
        for row in self.board:
            for cell in row:
                # Hücre boşsa 0 ekle
                if cell == " ":
                    features.append(0)
                # Hücrede 'S' varsa 1 ekle
                elif cell == "S":
                    features.append(1)
                # Hücrede 'O' varsa 2 ekle
                elif cell == "O":
                    features.append(2)

        # Tahtadaki toplam 'S' sayısını say
        s_count = features.count(1)

        # Tahtadaki toplam 'O' sayısını say
        o_count = features.count(2)

        # Tahtadaki boş hücre sayısını say
        empty_count = features.count(0)

        # Özellik listesine 'S', 'O' ve boş hücre sayılarını ekle
        features.append(s_count)
        features.append(o_count)
        features.append(empty_count)

        # SOS oluşturma potansiyellerini hesapla ve listeye ekle
        sos_potentials = self.count_sos_potentials()
        features.extend(sos_potentials)

        # Özellik vektörünü döndür
        return features

    def count_sos_potentials(self):
        """SOS oluşturma potansiyellerini sayar"""

        potentials = [0, 0]  # Şu an sadece bir oyuncu için kullanılıyor (potentials[0])

        # Kontrol edilecek 4 yön: sağa, aşağıya, sağ-alt çapraz, sol-alt çapraz
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        # Tüm hücreleri kontrol et
        for i in range(self.size):
            for j in range(self.size):
                # Eğer hücrede 'S' varsa, olası SOS dizileri kontrol edilir
                if self.board[i][j] == "S":
                    for dr, dc in directions:
                        # Şekil: S - O - boş (tamamlanabilir SOS)
                        if (0 <= i + 2 * dr < self.size and 0 <= j + 2 * dc < self.size and
                                self.board[i + dr][j + dc] == "O" and
                                self.board[i + 2 * dr][j + 2 * dc] == " "):
                            potentials[0] += 1

                        # Şekil: S - boş - S (tamamlanabilir SOS)
                        if (0 <= i + 2 * dr < self.size and 0 <= j + 2 * dc < self.size and
                                self.board[i + dr][j + dc] == " " and
                                self.board[i + 2 * dr][j + 2 * dc] == "S"):
                            potentials[0] += 1

                # Eğer hücrede 'O' varsa, çevresine bakılır
                elif self.board[i][j] == "O":
                    for dr, dc in directions:
                        # Şekil: S - O - boş (S sağdan gelebilir)
                        if (0 <= i - dr < self.size and 0 <= j - dc < self.size and
                                0 <= i + dr < self.size and 0 <= j + dc < self.size and
                                self.board[i - dr][j - dc] == "S" and
                                self.board[i + dr][j + dc] == " "):
                            potentials[0] += 1

                        # Şekil: boş - O - S (S soldan gelebilir)
                        if (0 <= i - dr < self.size and 0 <= j - dc < self.size and
                                0 <= i + dr < self.size and 0 <= j + dc < self.size and
                                self.board[i - dr][j - dc] == " " and
                                self.board[i + dr][j + dc] == "S"):
                            potentials[0] += 1

        return potentials  # Potansiyel sayısını döndür

    def game_over(self):
        """Oyun bittiğinde sonucu göster ve seçenek sun"""

        self.game_started = False  # Oyunun bittiğini işaretle

        winner = "Beraberlik"  # Varsayılan kazanan: eşitlik
        winner_color = "#555555"  # Varsayılan renk: gri

        # Skor karşılaştırılarak kazanan belirlenir
        if self.scores[1] > self.scores[2]:
            winner = "İnsan"
            winner_color = "#3a7ebf"  # Mavi renk
        elif self.scores[2] > self.scores[1]:
            winner = "AI"
            winner_color = "#bf3a3a"  # Kırmızı renk

        # Oyun sonucu ana etikette gösterilir
        self.move_info_label.config(text=f"Oyun bitti! Kazanan: {winner}", fg=winner_color)

        # Sonuç penceresi oluştur
        result_window = tk.Toplevel(self.master)
        result_window.title("Oyun Sonu")  # Başlık
        result_window.geometry("400x300")  # Boyut
        result_window.transient(self.master)  # Üst pencere
        result_window.grab_set()  # Diğer pencereyi kilitle

        # Pencere içeriği
        result_frame = tk.Frame(result_window, bg="#f0f0f0", padx=20, pady=20)
        result_frame.pack(expand=True, fill="both")

        # Başlık etiketi
        title_label = tk.Label(result_frame, text="OYUN SONU!", font=("Arial", 24, "bold"),
                               fg="#3a7ebf", bg="#f0f0f0")
        title_label.pack(pady=10)

        # Kazanan göster
        winner_text = f"Kazanan: {winner}"
        winner_label = tk.Label(result_frame, text=winner_text, font=("Arial", 18, "bold"),
                                fg=winner_color, bg="#f0f0f0")
        winner_label.pack(pady=10)

        # Skor göster
        score_text = f"İnsan: {self.scores[1]} - AI: {self.scores[2]}"
        score_label = tk.Label(result_frame, text=score_text, font=("Arial", 14),
                               fg="#333333", bg="#f0f0f0")
        score_label.pack(pady=10)

        # AI tipi açıklaması
        ai_desc = {
            "dt": "Decision Tree",
            "rf": "Random Forest"
        }

        # Seçilen ayarları göster
        settings_text = f"Zorluk: {self.difficulty.title()} | AI: {ai_desc[self.ai_type]}"
        settings_label = tk.Label(result_frame, text=settings_text, font=("Arial", 12),
                                  fg="#555555", bg="#f0f0f0")
        settings_label.pack(pady=5)

        # Buton çerçevesi
        button_frame = tk.Frame(result_frame, bg="#f0f0f0")
        button_frame.pack(pady=20)

        # Tekrar oyna butonu
        replay_button = tk.Button(button_frame, text="Tekrar Oyna", font=("Arial", 12),
                                  bg="#3a7ebf", fg="white", padx=10, pady=5,
                                  command=lambda: [result_window.destroy(), self.restart_game()])
        replay_button.grid(row=0, column=0, padx=10)

        # Ana menüye dön butonu
        menu_button = tk.Button(button_frame, text="Ana Menü", font=("Arial", 12),
                                bg="#555555", fg="white", padx=10, pady=5,
                                command=lambda: [result_window.destroy(), self.show_main_menu()])
        menu_button.grid(row=0, column=1, padx=10)

    def restart_game(self):
        """Aynı ayarlarla oyunu yeniden başlatır"""

        # Tahtayı sıfırla
        self.board = [[' ' for _ in range(self.size)] for _ in range(self.size)]
        self.current_player = 1  # Sıra insan oyuncuda
        self.scores = {1: 0, 2: 0}  # Skorları sıfırla
        self.last_move = None  # Son hamleyi temizle
        self.last_sos_formed = False  # Son SOS bilgisi sıfırla
        self.filled_cells = 0  # Dolu hücreleri sıfırla
        self.game_started = True  # Oyunu yeniden başlat

        # Butonları temizle
        for i in range(self.size):
            for j in range(self.size):
                self.buttons[i][j].config(text="", bg="white", state="normal")

        # Skor etiketlerini sıfırla
        self.player_score_label.config(text="0")
        self.ai_score_label.config(text="0")

        # Bilgi etiketi güncelle
        self.move_info_label.config(text="Oyun yeniden başladı!", fg="#555555")

        # Kazanma ihtimalleri hesapla
        self.update_win_probabilities()


if __name__ == "__main__":
    root = tk.Tk()              # Tkinter ana penceresini oluştur
    app = SOSGame(root)         # SOSGame sınıfından bir örnek oluştur
    root.mainloop()             # Arayüzü çalıştır
