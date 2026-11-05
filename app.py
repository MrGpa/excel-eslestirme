import os
import pandas as pd
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "gizli-anahtar-degistir"
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXT = {"xlsx", "xls"}

def izinli_dosya(ad):
    return "." in ad and ad.rsplit(".", 1)[1].lower() in ALLOWED_EXT

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        dosya = request.files.get("excel")
        if not dosya or dosya.filename == "":
            flash("Lütfen bir Excel dosyası seçin.")
            return redirect(url_for("index"))

        if not izinli_dosya(dosya.filename):
            flash("Sadece .xlsx veya .xls dosyaları yüklenebilir.")
            return redirect(url_for("index"))

        # Benzersiz isim ver
        zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
        guvenli_ad = secure_filename(dosya.filename)
        yuklenen_ad = f"{zaman}_{guvenli_ad}"
        yuklenen_yol = os.path.join(app.config["UPLOAD_FOLDER"], yuklenen_ad)
        dosya.save(yuklenen_yol)

        try:
            df = pd.read_excel(yuklenen_yol)
            c_kol = df.columns[2]
            u_kol = df.columns[20]

            c_vals = df[c_kol].astype(str).str.strip().str.lower()
            u_vals = df[u_kol].astype(str).str.strip().str.lower()
            eslesmeyen = df[c_vals != u_vals]

            if eslesmeyen.empty:
                return render_template("index.html", mesaj="✅ Tüm satırlar eşleşti, False olan yok.")

            cikti_ad = f"eslesmeyenler_{zaman}.xlsx"
            cikti_yol = os.path.join(app.config["UPLOAD_FOLDER"], cikti_ad)
            eslesmeyen.to_excel(cikti_yol, index=False)

            # Önizleme için ilk 50 satır
            onizleme = eslesmeyen.head(50).fillna("").to_dict(orient="records")
            kolonlar = list(eslesmeyen.columns)

            return render_template(
                "index.html",
                mesaj=f"⚠️ {len(eslesmeyen)} satır eşleşmedi.",
                onizleme=onizleme,
                kolonlar=kolonlar,
                toplam=len(eslesmeyen),
                cikti_ad=cikti_ad
            )

        except Exception as e:
            return render_template("index.html", mesaj=f"Hata: {e}")

    return render_template("index.html")

@app.route("/indir/<ad>")
def indir(ad):
    # Güvenlik: sadece uploads klasöründen indir
    ad = secure_filename(ad)
    yol = os.path.join(app.config["UPLOAD_FOLDER"], ad)
    if os.path.exists(yol):
        return send_file(yol, as_attachment=True)
    return "Dosya bulunamadı.", 404

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
