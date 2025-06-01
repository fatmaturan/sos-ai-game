
from sklearn.ensemble import RandomForestClassifier  # Rastgele orman sınıflandırıcısı (AI modeli)
from sklearn.tree import DecisionTreeClassifier  # Karar ağacı sınıflandırıcısı (AI modeli)
from sklearn.model_selection import train_test_split  # Veriyi eğitim/test olarak ayırmak için
import random  # Rastgele sayı ve seçim işlemleri için
import pickle  # Python nesnelerini dosyaya kaydetmek/yüklemek için
import os  # Dosya/dizin işlemleri için
import time  # Zaman ölçümü için
from datetime import datetime  # Güncel tarih/zaman bilgisi


# SOS oyun tahtasını ve kurallarını yöneten sınıf
class SOSBoard:
    def __init__(self, size=5):
        self.size = size  # Oyun tahtasının boyutu (örneğin 5x5)

        # Tahtayı başlat: boş hücrelerle (boşluk karakteri) doldurulmuş 2 boyutlu liste
        self.board = [[' ' for _ in range(size)] for _ in range(size)]

        # Oyuncu bilgisi (1. oyuncu ile başlanır)
        self.current_player = 1

        # Oyuncuların skorlarını tutan sözlük
        self.scores = {1: 0, 2: 0}

        # Şu ana kadar doldurulmuş hücre sayısı
        self.filled_cells = 0

        # Toplam hücre sayısı (örneğin 5x5 = 25)
        self.total_cells = size * size

        # Oyun bitmiş mi? Başlangıçta False
        self.game_over = False

        # Her hamlenin geçmişini tutan liste (AI eğitimi için kullanılır)
        self.moves_history = []

    def make_move(self, row, col, letter):
        """Verilen hücreye (row, col) 'S' veya 'O' harfini koyarak bir hamle yapar"""

        # Hamle sınır dışıysa ya da hücre zaten doluysa geçersiz sayılır
        if row < 0 or row >= self.size or col < 0 or col >= self.size or self.board[row][col] != ' ':
            return False

        # Harfi tahtaya yerleştir
        self.board[row][col] = letter

        # Dolu hücre sayısını bir artır
        self.filled_cells += 1

        # Hamle bilgilerini kaydetmek için sözlük oluştur
        move_data = {
            "player": self.current_player,  # Hamleyi yapan oyuncu
            "row": row,  # Hamle yapılan satır
            "col": col,  # Hamle yapılan sütun
            "letter": letter,  # Konulan harf ('S' veya 'O')
            "board_state": [row[:] for row in self.board],  # Tahtanın kopyası (hamle sonrası hali)
            "scores": self.scores.copy()  # Skorun kopyası (o andaki skor durumu)
        }

        # Konulan harf bir SOS oluşturuyor mu kontrol et
        sos_formed = self.check_sos(row, col)

        # Sonuçları hamle verisine ekle
        move_data["formed_sos"] = sos_formed

        # Hamleyi geçmişe ekle (eğitim için kullanılacak)
        self.moves_history.append(move_data)

        if sos_formed:
            # Eğer bu hamle SOS oluşturduysa, oyuncuya 1 puan ekle
            self.scores[self.current_player] += 1
        else:
            # Aksi halde sırayı diğer oyuncuya geçir
            self.current_player = 3 - self.current_player  # 1 → 2, 2 → 1 dönüşümü

        # Tüm hücreler dolduysa oyunu bitmiş olarak işaretle
        if self.filled_cells == self.total_cells:
            self.game_over = True

        # Hamle başarıyla tamamlandıysa True döndür
        return True

    def check_sos(self, row, col): #kontrol etme
        """Verilen (row, col) hücresine konulan harf ile bir SOS oluşmuş mu kontrol eder"""

        # O hücreye konan harfi al ('S' ya da 'O')
        letter = self.board[row][col]

        # SOS desenlerini kontrol etmek için 4 yön:
        # sağ, aşağı, sağ alt çapraz, sol alt çapraz
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        sos_formed = False  # Başlangıçta SOS oluşmamış kabul edilir

        # Eğer konulan harf 'S' ise: bu 'S' bir SOS'un başında ya da sonunda olabilir
        if letter == 'S':
            # SOS'un BAŞI mı? (S O S → bu S en başta)
            for dr, dc in directions:
                if (0 <= row + 2 * dr < self.size and
                        0 <= col + 2 * dc < self.size and
                        self.board[row + dr][col + dc] == 'O' and  # Ortadaki harf 'O' olmalı
                        self.board[row + 2 * dr][col + 2 * dc] == 'S'):  # S O S yapısı tamamlanmalı
                    sos_formed = True

            # SOS'un SONU mu? (S O S → bu S en sonda)
            for dr, dc in directions:
                if (0 <= row - 2 * dr < self.size and
                        0 <= col - 2 * dc < self.size and
                        self.board[row - dr][col - dc] == 'O' and  # Ortadaki harf 'O' olmalı
                        self.board[row - 2 * dr][col - 2 * dc] == 'S'):  # S O S yapısı tamamlanmalı
                    sos_formed = True

    def get_winner(self):
        """Oyun sonunda skorlara göre kazanan oyuncuyu döndürür"""

        # Oyuncu 1'in skoru daha yüksekse, kazanan 1. oyuncudur
        if self.scores[1] > self.scores[2]:
            return 1

        # Oyuncu 2'nin skoru daha yüksekse, kazanan 2. oyuncudur
        elif self.scores[2] > self.scores[1]:
            return 2

        # Skorlar eşitse, oyun berabere bitmiştir
        else:
            return 0  # Beraberlik

    def get_possible_moves(self):
        """Tahtadaki tüm boş hücreler için 'S' ve 'O' harflerini içeren hamleleri döndürür"""

        moves = []  # Hamleleri tutacak liste

        # Tahtadaki tüm hücreleri dolaş
        for i in range(self.size):
            for j in range(self.size):
                # Eğer hücre boşsa
                if self.board[i][j] == ' ':
                    # Bu hücreye 'S' veya 'O' yerleştirilebilir
                    moves.append((i, j, 'S'))
                    moves.append((i, j, 'O'))

        return moves  # Tüm mümkün hamleleri döndür

    def rule_based_move(self, difficulty="hard"):
        """Kural bazlı bir hamle yap"""
        if difficulty == "easy":
            return self.rule_based_move_easy()
        elif difficulty == "medium":
            # %70 zor, %30 kolay
            if random.random() < 0.7:
                return self.rule_based_move_hard()
            else:
                return self.rule_based_move_easy()
        else:  # hard
            return self.rule_based_move_hard()

    def rule_based_move_easy(self):
        """Kolay seviye için rastgele hamle yap"""
        possible_moves = self.get_possible_moves()  # Tahtadaki tüm boş hücreleri al

        if not possible_moves:
            return None  # Hiç hamle yoksa None döndür

        return random.choice(possible_moves)  # Boş hamlelerden rastgele birini seç ve döndür

    def rule_based_move_hard(self):
        """Zor seviye için akıllı hamle yap"""
        # 1. SOS oluşturabilecek bir hamle olup olmadığını kontrol et
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == ' ':
                    # S harfi koyarsak SOS olur mu?
                    self.board[i][j] = 'S'
                    if self.check_sos(i, j):
                        self.board[i][j] = ' '  # Denemeyi geri al
                        return (i, j, 'S')  # S harfi ile SOS yapabildik

                    # O harfi koyarsak SOS olur mu?
                    self.board[i][j] = 'O'
                    if self.check_sos(i, j):
                        self.board[i][j] = ' '  # Denemeyi geri al
                        return (i, j, 'O')  # O harfi ile SOS yapabildik

                    self.board[i][j] = ' '  # Denemeyi geri al

        # 2. Rakibin SOS oluşturmasını engelleyecek bir hamle var mı kontrol et
        original_player = self.current_player
        self.current_player = 3 - original_player  # Geçici olarak rakibin sırası

        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == ' ':
                    # Rakip S ile SOS oluşturabilir mi?
                    self.board[i][j] = 'S'
                    if self.check_sos(i, j):
                        self.board[i][j] = ' '  # Tahtayı geri al
                        self.current_player = original_player  # Oyuncuyu geri al
                        return (i, j, 'S')

                    # Rakip O ile SOS oluşturabilir mi?
                    self.board[i][j] = 'O'
                    if self.check_sos(i, j):
                        self.board[i][j] = ' '  # Tahtayı geri al
                        self.current_player = original_player  # Oyuncuyu geri al
                        return (i, j, 'O')

                    self.board[i][j] = ' '  # Tahtayı geri al

        self.current_player = original_player  # Oyuncuyu geri al

        strategic_moves = []  # Tüm stratejik hamleleri tutacak liste

        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == ' ':
                    score = self.evaluate_strategic_move(i, j, 'S')  # S harfi için stratejik puan hesapla
                    strategic_moves.append((score, i, j, 'S'))  # S harfli hamleyi listeye ekle

                    score = self.evaluate_strategic_move(i, j, 'O')  # O harfi için stratejik puan hesapla
                    strategic_moves.append((score, i, j, 'O'))  # O harfli hamleyi listeye ekle

        if strategic_moves:
            strategic_moves.sort(reverse=True)  # Puanı yüksek olandan düşük olana sırala
            return strategic_moves[0][1:]  # En yüksek puanlı hamleyi döndür (i, j, harf)

        return self.rule_based_move_easy()  # Eğer stratejik hamle yoksa kolay hamleye geri dön

    def evaluate_strategic_move(self, row, col, letter):
        """Stratejik hamle puanını hesapla"""
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]# Yönler: sağ, aşağı, çaprazlar

        if letter == 'S':
            for dr, dc in directions:
                # S-?-? şeklindeki kalıpları kontrol et
                if (0 <= row + 2*dr < self.size and 0 <= col + 2*dc < self.size):
                    if self.board[row + dr][col + dc] == 'O' and self.board[row + 2*dr][col + 2*dc] == ' ':
                        score += 2  # Gerçekleşmeye yakın SOS
                    elif self.board[row + dr][col + dc] == ' ' and self.board[row + 2*dr][col + 2*dc] == ' ':
                        score += 1  # Potansiyel SOS

                if (0 <= row - 2*dr < self.size and 0 <= col - 2*dc < self.size):
                    if self.board[row - dr][col - dc] == 'O' and self.board[row - 2*dr][col - 2*dc] == ' ':
                        score += 2  # Gerçekleşmeye yakın SOS
                    elif self.board[row - dr][col - dc] == ' ' and self.board[row - 2*dr][col - 2*dc] == ' ':
                        score += 1  # Potansiyel SOS


        elif letter == 'O':
            for dr, dc in directions:
                # O harfi ortadaysa çevresinde S olup olmadığını kontrol et
                if (0 <= row - dr < self.size and 0 <= col - dc < self.size and
                    0 <= row + dr < self.size and 0 <= col + dc < self.size):
                    if self.board[row - dr][col - dc] == 'S' and self.board[row + dr][col + dc] == 'S':
                        score += 10  # Kesin SOS
                    elif self.board[row - dr][col - dc] == 'S' and self.board[row + dr][col + dc] == ' ':
                        score += 3  # SOS ihtimali
                    elif self.board[row - dr][col - dc] == ' ' and self.board[row + dr][col + dc] == 'S':
                        score += 3  # SOS ihtimali
        # Rakibin bu hamleye karşı SOS yapma ihtimalini düş
        original_player = self.current_player
        self.current_player = 3 - original_player  # Rakibi aktif yap

        self.board[row][col] = letter  # Geçici olarak hamleyi uygula
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == ' ':
                    for test_letter in ['S', 'O']:
                        self.board[r][c] = test_letter
                        if self.check_sos(r, c):
                            score -= 5  # Rakip burada SOS yapabiliyor, puan düş
                        self.board[r][c] = ' '  # Geri al

        self.board[row][col] = ' '  # Kendi hamleni de geri al
        self.current_player = original_player  # Oyuncuyu geri getir

        return score  # Hesaplanan stratejik puanı döndür

class AITrainer:
    def __init__(self):
        self.dt_model = DecisionTreeClassifier(max_depth=10)  # Karar ağacı modeli
        self.rf_model = RandomForestClassifier(n_estimators=100, max_depth=10)  # Rastgele orman modeli
        self.training_data = []  # Eğitim verilerini tutmak için boş liste

    # Özellik çıkarımı yapan sınıf içindeki fonksiyonlar
    def extract_features(self, board_state, size):
        """Tahta durumundan özellikler çıkarır"""
        features = []  # Özellikleri tutacak liste
        for row in board_state:  # Her satır için döngü
            for cell in row:  # Satırdaki her hücre için döngü
                if cell == " ":  # Hücre boşsa
                    features.append(0)  # 0 ekle
                elif cell == "S":  # Hücrede "S" varsa
                    features.append(1)  # 1 ekle
                elif cell == "O":  # Hücrede "O" varsa
                    features.append(2)  # 2 ekle

        s_count = features.count(1)  # "S" harfi sayısı
        o_count = features.count(2)  # "O" harfi sayısı
        empty_count = features.count(0)  # Boş hücre sayısı

        features.append(s_count)  # Özellik listesine ekle
        features.append(o_count)  # Özellik listesine ekle
        features.append(empty_count)  # Özellik listesine ekle

        sos_potentials = self.count_sos_potentials(board_state, size)  # Potansiyel SOS sayısını al
        features.extend(sos_potentials)  # Özellik listesine ekle

        return features  # Özellik listesini döndür

    def count_sos_potentials(self, board_state, size):
        """SOS oluşturma potansiyellerini sayar"""
        potentials = [0, 0]  # SOS oluşturma potansiyelleri listesi (S-O-? ve ?-O-S gibi)

        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # Sağ, aşağı, sağ çapraz, sol çapraz yönler

        for i in range(size):  # Satırlar üzerinde dön
            for j in range(size):  # Sütunlar üzerinde dön
                if board_state[i][j] == "S":  # Hücrede "S" varsa
                    for dr, dc in directions:  # Her yön için
                        # S-O-? deseni kontrolü
                        if (0 <= i + 2 * dr < size and 0 <= j + 2 * dc < size and
                                board_state[i + dr][j + dc] == "O" and
                                board_state[i + 2 * dr][j + 2 * dc] == " "):
                            potentials[0] += 1  # Potansiyel sayısını artır

                        # ?-O-S deseni kontrolü
                        if (0 <= i + 2 * dr < size and 0 <= j + 2 * dc < size and
                                board_state[i + dr][j + dc] == " " and
                                board_state[i + 2 * dr][j + 2 * dc] == "S"):
                            potentials[0] += 1  # Potansiyel sayısını artır

                elif board_state[i][j] == "O":  # Hücrede "O" varsa
                    for dr, dc in directions:  # Her yön için
                        # S-O-? deseni için: O ortadaysa
                        if (0 <= i - dr < size and 0 <= j - dc < size and
                                0 <= i + dr < size and 0 <= j + dc < size and
                                board_state[i - dr][j - dc] == "S" and
                                board_state[i + dr][j + dc] == " "):
                            potentials[0] += 1  # Potansiyel sayısını artır

                        # ?-O-S deseni için
                        if (0 <= i - dr < size and 0 <= j - dc < size and
                                0 <= i + dr < size and 0 <= j + dc < size and
                                board_state[i - dr][j - dc] == " " and
                                board_state[i + dr][j + dc] == "S"):
                            potentials[0] += 1  # Potansiyel sayısını artır

        return potentials  # Potansiyel listesini döndür

    def prepare_training_data(self, games_history, board_size):
        """Oyun geçmişinden eğitim verileri hazırlar"""
        X = []  # Özellikler için liste
        y = []  # Etiketler (hamleler) için liste

        for game in games_history:  # Her oyun için
            for move in game:  # Her hamle için
                features = self.extract_features(move["board_state"], board_size)  # Özellik çıkar
                target = f"{move['row']},{move['col']},{move['letter']}"  # Hedef etiket formatı

                weight = 1  # Ağırlık değeri
                if move.get("formed_sos", False):  # Eğer SOS oluşturduysa
                    weight = 3  # Ağırlığı artır

                for _ in range(weight):  # Ağırlık kadar tekrar ekle
                    X.append(features)  # Özellikleri listeye ekle
                    y.append(target)  # Hedefi listeye ekle

        self.training_data = (X, y)  # Eğitim verisini sınıf değişkenine kaydet
        return X, y  # Özellik ve hedefleri döndür

    def train_models(self, X, y):
        """Her iki modeli de eğit"""
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)  # Veriyi böl

        print("Decision Tree modeli eğitiliyor...")  # Bilgi mesajı
        self.dt_model.fit(X_train, y_train)  # Decision Tree modeli eğit
        dt_score = self.dt_model.score(X_test, y_test)  # Başarı oranını al

        print("Random Forest modeli eğitiliyor...")  # Bilgi mesajı
        self.rf_model.fit(X_train, y_train)  # Random Forest modeli eğit
        rf_score = self.rf_model.score(X_test, y_test)  # Başarı oranını al

        return {"dt_score": dt_score, "rf_score": rf_score}  # Başarı oranlarını döndür

    def save_models(self, board_size):
        """Modelleri kaydet"""
        os.makedirs("models", exist_ok=True)  # Klasör yoksa oluştur

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Zaman etiketi oluştur

        dt_filename = f"models/sos_dt_{board_size}x{board_size}_{timestamp}.pkl"  # DT model dosya adı
        with open(dt_filename, 'wb') as f:  # Dosyayı yazma modunda aç
            pickle.dump(self.dt_model, f)  # Modeli dosyaya yaz

        rf_filename = f"models/sos_rf_{board_size}x{board_size}_{timestamp}.pkl"  # RF model dosya adı
        with open(rf_filename, 'wb') as f:  # Dosyayı yazma modunda aç
            pickle.dump(self.rf_model, f)  # Modeli dosyaya yaz

        return {"dt_model": dt_filename, "rf_model": rf_filename}  # Dosya yollarını döndür


# Eğitim verisi oluşturan fonksiyon
def generate_training_data(board_size=5, num_games=10000, player1_diff="hard", player2_diff="hard"):
    """Eğitim verisi oluştur"""
    print(f"{board_size}x{board_size} tahta için {num_games} oyun oluşturuluyor...")  # Bilgi mesajı
    print(f"Oyuncu 1: {player1_diff} zorluk | Oyuncu 2: {player2_diff} zorluk")  # Oyuncu bilgisi

    games_history = []  # Oyun geçmişini tutacak liste

    for game_idx in range(num_games):  # Belirtilen sayıda oyun döngüsü
        if (game_idx + 1) % 100 == 0:  # Her 100 oyunda bir durum bildirimi
            print(f"Oyun {game_idx + 1}/{num_games} tamamlandı")

        game = SOSBoard(size=board_size)  # Yeni oyun oluştur
        #kural bazlı botlar oynuyor
        while not game.game_over:  # Oyun bitene kadar
            if game.current_player == 1:  # Sıra oyuncu 1'deyse
                move = game.rule_based_move(player1_diff)  # Oyuncu 1 için hamle üret
            else:
                move = game.rule_based_move(player2_diff)  # Oyuncu 2 için hamle üret

            if move:  # Eğer geçerli hamle varsa
                row, col, letter = move  # Hamleyi ayır
                game.make_move(row, col, letter)  # Hamleyi uygula
            else:
                break  # Hamle yoksa döngüden çık

        games_history.append(game.moves_history)  # Oyunu geçmişe ekle

    print(f"{num_games} oyun tamamlandı!")  # Tamamlama bildirimi

    total_moves = sum(len(game) for game in games_history)  # Toplam hamle sayısı
    avg_moves = total_moves / num_games  # Ortalama hamle sayısı

    print(f"Toplam hamle: {total_moves}")  # Toplam hamle bilgisi
    print(f"Ortalama hamle/oyun: {avg_moves:.2f}")  # Ortalama bilgi

    return games_history  # Oyun geçmişini döndür


# Model eğitimi ve kaydetme fonksiyonu
def train_and_save_models(board_size=5, num_games=10000):
    """Veri oluştur, eğit ve modelleri kaydet"""
    print("Eğitim verisi oluşturuluyor...")  # Bilgi mesajı
    games_history = generate_training_data(board_size, num_games)  # Eğitim verisi üret

    print("Modeller eğitiliyor...")  # Bilgi mesajı
    trainer = AITrainer()  # Eğitici sınıfı örnekle
    X, y = trainer.prepare_training_data(games_history, board_size)  # Eğitim verisini hazırla

    print(f"Toplam {len(X)} örnek ile eğitim yapılıyor")  # Eğitim verisi sayısı
    scores = trainer.train_models(X, y)  # Modelleri eğit

    print(f"Eğitim tamamlandı!")  # Eğitim tamamlandı bildirimi
    print(f"Decision Tree doğruluk: {scores['dt_score']:.4f}")  # DT doğruluk oranı
    print(f"Random Forest doğruluk: {scores['rf_score']:.4f}")  # RF doğruluk oranı

    print("Modeller kaydediliyor...")  # Kayıt bildirimi
    model_paths = trainer.save_models(board_size)  # Modelleri kaydet

    print("Modeller başarıyla kaydedildi!")  # Kayıt başarılı bildirimi
    print(f"Decision Tree modeli: {model_paths['dt_model']}")  # DT model dosya yolu
    print(f"Random Forest modeli: {model_paths['rf_model']}")  # RF model dosya yolu

    return model_paths  # Model yollarını döndür


# Ana çalışma bloğu
if __name__ == "__main__":
    start_time = time.time()  # Başlangıç zamanını al

    board_size = 5  # Tahta boyutu
    num_games = 10000  # Oyun sayısı

    train_and_save_models(board_size, num_games)  # Eğitim ve kayıt işlemini başlat

    elapsed_time = time.time() - start_time  # Geçen süreyi hesapla
    print(f"Toplam süre: {elapsed_time:.2f} saniye")  # Süreyi yazdır