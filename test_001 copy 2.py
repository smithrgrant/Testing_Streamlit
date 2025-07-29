from pathlib import Path
from pathlib import Path
from xhtml2pdf import pisa


src = Path(r"C:\Users\grobe\OneDrive\Documents\GitHub\Testing_Streamlit\quotes_out\Quote_1001.html")          # your HTML file
dst = Path(r"C:\Users\grobe\OneDrive\Documents\GitHub\Testing_Streamlit\quotes_out\quote.pdf")           # output PDF



def html_to_pdf(html_path: str | Path, pdf_path: str | Path) -> bool:
    html_path, pdf_path = Path(html_path), Path(pdf_path)
    html = html_path.read_text(encoding="utf-8")
    with open(pdf_path, "wb") as f_out:
        result = pisa.CreatePDF(html, dest=f_out)
    return not result.err  # True if success

if __name__ == "__main__":
    ok = html_to_pdf(src, dst)
    print("Done!" if ok else "Failed.")


