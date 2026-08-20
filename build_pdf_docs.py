"""
build_pdf_docs.py — Converts Haykal AI Markdown Documentation into Luxury Executive PDFs
Using Python markdown + Pygments + Headless Microsoft Edge rendering.
"""

import os
import sys
import re
import subprocess
import markdown

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_PATH):
    EDGE_PATH = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

AR_MD_PATH = "PROJECT_DOCUMENTATION_AR.md"
EN_MD_PATH = "PROJECT_DOCUMENTATION_EN.md"

AR_HTML_PATH = "PROJECT_DOCUMENTATION_AR.html"
EN_HTML_PATH = "PROJECT_DOCUMENTATION_EN.html"

AR_PDF_PATH = "PROJECT_DOCUMENTATION_AR.pdf"
EN_PDF_PATH = "PROJECT_DOCUMENTATION_EN.pdf"


def preprocess_markdown(md_content: str, is_arabic: bool = True) -> str:
    """Preprocesses markdown for richer HTML styling (alerts, callouts, tables, badges)."""
    # Replace GitHub alerts like > [!IMPORTANT]
    def replace_alert(match):
        alert_type = match.group(1).upper()
        content = match.group(2).strip()
        icon = "🚨" if "IMPORTANT" in alert_type or "CAUTION" in alert_type else "💡" if "TIP" in alert_type else "ℹ️"
        title = "تنبيه سريري وقانوني هام" if is_arabic and "IMPORTANT" in alert_type else "Clinical & Legal Notice" if not is_arabic and "IMPORTANT" in alert_type else alert_type
        return f"""
<div class="alert-box alert-{alert_type.lower()}">
    <div class="alert-header"><span class="alert-icon">{icon}</span> <strong>{title}</strong></div>
    <div class="alert-body">{content}</div>
</div>
"""
    md_content = re.sub(r'> \[!(IMPORTANT|WARNING|NOTE|TIP|CAUTION)\]\s*\n((?:> .*\n?)+)', 
                        lambda m: replace_alert(re.match(r'\[!(IMPORTANT|WARNING|NOTE|TIP|CAUTION)\]\s*\n(.*)', m.group(0).replace('> ', ''), re.DOTALL)), 
                        md_content)

    return md_content


def build_arabic_html(body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>وثيقة مشروع هيكل | Haykal AI - التقرير الفني الشامل</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800;900&family=Fira+Code:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        @page {{
            size: A4;
            margin: 15mm 15mm 18mm 15mm;
            @bottom-right {{
                content: "منصة هيكل الطبية | Haykal AI";
                font-family: 'Cairo', sans-serif;
                font-size: 8pt;
                color: #94a3b8;
            }}
            @bottom-left {{
                content: "صفحة " counter(page);
                font-family: 'Cairo', sans-serif;
                font-size: 8pt;
                color: #64748b;
                font-weight: 600;
            }}
        }}

        *, *::before, *::after {{
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Cairo', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 10.5pt;
            line-height: 1.65;
            color: #1e293b;
            background-color: #ffffff;
            margin: 0;
            padding: 0;
            direction: rtl;
            text-align: right;
        }}

        /* Header Cover Banner */
        .doc-cover {{
            background: linear-gradient(135deg, #0f172a 0%, #0d9488 60%, #0284c7 100%);
            color: #ffffff;
            padding: 32px 30px;
            border-radius: 14px;
            margin-bottom: 25px;
            box-shadow: 0 10px 25px -5px rgba(13, 148, 136, 0.25);
            page-break-inside: avoid;
        }}

        .doc-cover .badge {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(8px);
            color: #ffffff;
            padding: 4px 14px;
            border-radius: 50px;
            font-size: 9pt;
            font-weight: 700;
            margin-bottom: 12px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            letter-spacing: 0.5px;
        }}

        .doc-cover h1 {{
            color: #ffffff !important;
            font-size: 24pt;
            font-weight: 900;
            margin: 0 0 8px 0;
            line-height: 1.2;
            border-bottom: none !important;
            padding-bottom: 0 !important;
        }}

        .doc-cover .subtitle {{
            font-size: 12pt;
            color: #ccfbf1;
            margin: 0 0 16px 0;
            font-weight: 600;
        }}

        .doc-cover .meta-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 18px;
            padding-top: 14px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            font-size: 8.5pt;
        }}

        .meta-item strong {{
            color: #99f6e4;
            display: block;
            margin-bottom: 2px;
        }}

        /* Headings */
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Cairo', sans-serif;
            color: #0f172a;
            font-weight: 800;
            page-break-after: avoid;
            page-break-inside: avoid;
        }}

        h1 {{
            font-size: 17pt;
            margin-top: 28px;
            margin-bottom: 14px;
            padding-bottom: 6px;
            border-bottom: 2.5px solid #0d9488;
            color: #0f172a;
        }}

        h2 {{
            font-size: 13.5pt;
            margin-top: 22px;
            margin-bottom: 10px;
            color: #0f766e;
            display: flex;
            align-items: center;
        }}

        h3 {{
            font-size: 11.5pt;
            margin-top: 16px;
            margin-bottom: 8px;
            color: #1e293b;
        }}

        p {{
            margin: 0 0 10px 0;
            text-align: justify;
        }}

        /* Links */
        a {{
            color: #0284c7;
            text-decoration: none;
            font-weight: 600;
        }}

        /* Lists */
        ul, ol {{
            margin: 0 0 12px 0;
            padding-right: 22px;
            padding-left: 0;
        }}

        li {{
            margin-bottom: 5px;
        }}

        li > strong {{
            color: #0f172a;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 14px 0 18px 0;
            font-size: 9pt;
            page-break-inside: avoid;
            background: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
        }}

        th {{
            background: #0f172a;
            color: #ffffff;
            font-weight: 700;
            text-align: right;
            padding: 9px 12px;
            border: 1px solid #1e293b;
            font-size: 9pt;
        }}

        td {{
            padding: 8px 12px;
            border: 1px solid #e2e8f0;
            vertical-align: top;
        }}

        tr:nth-child(even) td {{
            background-color: #f8fafc;
        }}

        /* Code & Pre */
        pre {{
            background-color: #0f172a;
            color: #f8fafc;
            padding: 12px 14px;
            border-radius: 8px;
            font-family: 'Fira Code', Consolas, Monaco, monospace;
            font-size: 8pt;
            line-height: 1.45;
            direction: ltr;
            text-align: left;
            overflow-x: auto;
            border: 1px solid #1e293b;
            margin: 10px 0 14px 0;
            page-break-inside: avoid;
        }}

        code {{
            font-family: 'Fira Code', Consolas, Monaco, monospace;
            font-size: 8.5pt;
            background-color: #f1f5f9;
            color: #0f766e;
            padding: 2px 6px;
            border-radius: 4px;
            direction: ltr;
            display: inline-block;
            border: 1px solid #e2e8f0;
            font-weight: 600;
        }}

        pre code {{
            background-color: transparent;
            color: inherit;
            padding: 0;
            border: none;
            font-weight: 400;
            font-size: 8pt;
        }}

        /* Blockquotes / Alerts */
        blockquote {{
            margin: 14px 0;
            padding: 12px 16px;
            background-color: #f0fdf4;
            border-right: 4px solid #0d9488;
            border-radius: 0 8px 8px 0;
            color: #166534;
            font-size: 9.5pt;
            page-break-inside: avoid;
        }}

        .alert-box {{
            margin: 14px 0;
            padding: 14px 18px;
            border-radius: 10px;
            page-break-inside: avoid;
            font-size: 9.5pt;
        }}

        .alert-important, .alert-caution, .alert-warning {{
            background-color: #fff1f2;
            border: 1.5px solid #fecdd3;
            border-right: 5px solid #e11d48;
            color: #881337;
        }}

        .alert-header {{
            font-weight: 800;
            margin-bottom: 6px;
            font-size: 10.5pt;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .alert-body {{
            line-height: 1.55;
            color: #4c0519;
        }}

        /* Badges for Triage and Sources */
        strong:contains("[TRIAGE") {{
            color: #e11d48;
        }}

        hr {{
            border: none;
            height: 1px;
            background: #e2e8f0;
            margin: 22px 0;
        }}
    </style>
</head>
<body>

    <div class="doc-cover">
        <div class="badge">🏥 وثيقة فنية واعتماد سريري شامل</div>
        <h1>هيكل | Haykal AI</h1>
        <div class="subtitle">المنصة والوكيل السريري الذكي المتخصص (Primary AI Medical Agent & Decision Support)</div>
        <div class="meta-grid">
            <div class="meta-item"><strong>التخصصات الطبية:</strong> المخ والأعصاب • العظام والمفاصل</div>
            <div class="meta-item"><strong>المحرك والنموذج:</strong> LangGraph • Google Gemini 3.5 • Medical RAG</div>
            <div class="meta-item"><strong>حالة الأمان السريري:</strong> فحص طوارئ فوري (Red Flags) بنسبة 100%</div>
        </div>
    </div>

    {body_html}

</body>
</html>
"""


def build_english_html(body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <title>Haykal AI - Comprehensive Technical & Clinical Documentation</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        @page {{
            size: A4;
            margin: 15mm 15mm 18mm 15mm;
            @bottom-left {{
                content: "Haykal AI Clinical Platform | Technical Documentation";
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 8pt;
                color: #94a3b8;
            }}
            @bottom-right {{
                content: "Page " counter(page);
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 8pt;
                color: #64748b;
                font-weight: 600;
            }}
        }}

        *, *::before, *::after {{
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 10pt;
            line-height: 1.6;
            color: #1e293b;
            background-color: #ffffff;
            margin: 0;
            padding: 0;
            direction: ltr;
            text-align: left;
        }}

        /* Header Cover Banner */
        .doc-cover {{
            background: linear-gradient(135deg, #0f172a 0%, #0d9488 60%, #0284c7 100%);
            color: #ffffff;
            padding: 32px 30px;
            border-radius: 14px;
            margin-bottom: 25px;
            box-shadow: 0 10px 25px -5px rgba(13, 148, 136, 0.25);
            page-break-inside: avoid;
        }}

        .doc-cover .badge {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(8px);
            color: #ffffff;
            padding: 4px 14px;
            border-radius: 50px;
            font-size: 8.5pt;
            font-weight: 700;
            margin-bottom: 12px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            letter-spacing: 0.5px;
        }}

        .doc-cover h1 {{
            color: #ffffff !important;
            font-size: 24pt;
            font-weight: 800;
            margin: 0 0 8px 0;
            line-height: 1.2;
            border-bottom: none !important;
            padding-bottom: 0 !important;
        }}

        .doc-cover .subtitle {{
            font-size: 11.5pt;
            color: #ccfbf1;
            margin: 0 0 16px 0;
            font-weight: 500;
        }}

        .doc-cover .meta-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 18px;
            padding-top: 14px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            font-size: 8.5pt;
        }}

        .meta-item strong {{
            color: #99f6e4;
            display: block;
            margin-bottom: 2px;
        }}

        /* Headings */
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #0f172a;
            font-weight: 700;
            page-break-after: avoid;
            page-break-inside: avoid;
        }}

        h1 {{
            font-size: 16pt;
            margin-top: 26px;
            margin-bottom: 12px;
            padding-bottom: 6px;
            border-bottom: 2.5px solid #0d9488;
            color: #0f172a;
        }}

        h2 {{
            font-size: 13pt;
            margin-top: 20px;
            margin-bottom: 10px;
            color: #0f766e;
        }}

        h3 {{
            font-size: 11pt;
            margin-top: 14px;
            margin-bottom: 6px;
            color: #1e293b;
        }}

        p {{
            margin: 0 0 10px 0;
            text-align: justify;
        }}

        /* Links */
        a {{
            color: #0284c7;
            text-decoration: none;
            font-weight: 600;
        }}

        /* Lists */
        ul, ol {{
            margin: 0 0 12px 0;
            padding-left: 20px;
        }}

        li {{
            margin-bottom: 4px;
        }}

        li > strong {{
            color: #0f172a;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 14px 0 18px 0;
            font-size: 8.5pt;
            page-break-inside: avoid;
            background: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
        }}

        th {{
            background: #0f172a;
            color: #ffffff;
            font-weight: 700;
            text-align: left;
            padding: 9px 12px;
            border: 1px solid #1e293b;
        }}

        td {{
            padding: 8px 12px;
            border: 1px solid #e2e8f0;
            vertical-align: top;
        }}

        tr:nth-child(even) td {{
            background-color: #f8fafc;
        }}

        /* Code & Pre */
        pre {{
            background-color: #0f172a;
            color: #f8fafc;
            padding: 12px 14px;
            border-radius: 8px;
            font-family: 'Fira Code', Consolas, Monaco, monospace;
            font-size: 8pt;
            line-height: 1.45;
            overflow-x: auto;
            border: 1px solid #1e293b;
            margin: 10px 0 14px 0;
            page-break-inside: avoid;
        }}

        code {{
            font-family: 'Fira Code', Consolas, Monaco, monospace;
            font-size: 8.5pt;
            background-color: #f1f5f9;
            color: #0f766e;
            padding: 2px 5px;
            border-radius: 4px;
            display: inline-block;
            border: 1px solid #e2e8f0;
            font-weight: 600;
        }}

        pre code {{
            background-color: transparent;
            color: inherit;
            padding: 0;
            border: none;
            font-weight: 400;
            font-size: 8pt;
        }}

        /* Blockquotes / Alerts */
        blockquote {{
            margin: 14px 0;
            padding: 12px 16px;
            background-color: #f0fdf4;
            border-left: 4px solid #0d9488;
            border-radius: 0 8px 8px 0;
            color: #166534;
            font-size: 9pt;
            page-break-inside: avoid;
        }}

        .alert-box {{
            margin: 14px 0;
            padding: 14px 18px;
            border-radius: 10px;
            page-break-inside: avoid;
            font-size: 9pt;
        }}

        .alert-important, .alert-caution, .alert-warning {{
            background-color: #fff1f2;
            border: 1.5px solid #fecdd3;
            border-left: 5px solid #e11d48;
            color: #881337;
        }}

        .alert-header {{
            font-weight: 800;
            margin-bottom: 6px;
            font-size: 10pt;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .alert-body {{
            line-height: 1.55;
            color: #4c0519;
        }}

        hr {{
            border: none;
            height: 1px;
            background: #e2e8f0;
            margin: 22px 0;
        }}
    </style>
</head>
<body>

    <div class="doc-cover">
        <div class="badge">🏥 Comprehensive Clinical & Technical Specification</div>
        <h1>Haykal AI</h1>
        <div class="subtitle">Primary AI Medical Agent & Clinical Decision Support System</div>
        <div class="meta-grid">
            <div class="meta-item"><strong>Specialties:</strong> Neurology & Spine • Orthopedics & Musculoskeletal</div>
            <div class="meta-item"><strong>Engine & Model:</strong> LangGraph • Google Gemini 3.5 • Medical RAG</div>
            <div class="meta-item"><strong>Safety Status:</strong> Deterministic 100% Red Flag Interception</div>
        </div>
    </div>

    {body_html}

</body>
</html>
"""


def convert_md_to_pdf():
    md_parser = markdown.Markdown(extensions=['extra', 'tables', 'fenced_code', 'toc'])

    # 1. Process Arabic
    print("⏳ Processing Arabic Documentation...")
    with open(AR_MD_PATH, "r", encoding="utf-8") as f:
        ar_md = f.read()
    
    ar_md_clean = preprocess_markdown(ar_md, is_arabic=True)
    ar_body = md_parser.convert(ar_md_clean)
    ar_html = build_arabic_html(ar_body)
    
    with open(AR_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(ar_html)
    
    abs_ar_html = os.path.abspath(AR_HTML_PATH)
    abs_ar_pdf = os.path.abspath(AR_PDF_PATH)
    
    cmd_ar = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        f"--print-to-pdf={abs_ar_pdf}",
        f"file:///{abs_ar_html.replace(os.sep, '/')}"
    ]
    print(f"🚀 Generating Arabic PDF via Edge: {abs_ar_pdf}")
    res_ar = subprocess.run(cmd_ar, capture_output=True, text=True)
    if os.path.exists(abs_ar_pdf) and os.path.getsize(abs_ar_pdf) > 1000:
        print(f"✅ Arabic PDF created successfully! ({os.path.getsize(abs_ar_pdf)} bytes)")
    else:
        print(f"❌ Error generating Arabic PDF: {res_ar.stderr}")

    # 2. Process English
    print("\n⏳ Processing English Documentation...")
    md_parser.reset()
    with open(EN_MD_PATH, "r", encoding="utf-8") as f:
        en_md = f.read()
    
    en_md_clean = preprocess_markdown(en_md, is_arabic=False)
    en_body = md_parser.convert(en_md_clean)
    en_html = build_english_html(en_body)
    
    with open(EN_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(en_html)
    
    abs_en_html = os.path.abspath(EN_HTML_PATH)
    abs_en_pdf = os.path.abspath(EN_PDF_PATH)
    
    cmd_en = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        f"--print-to-pdf={abs_en_pdf}",
        f"file:///{abs_en_html.replace(os.sep, '/')}"
    ]
    print(f"🚀 Generating English PDF via Edge: {abs_en_pdf}")
    res_en = subprocess.run(cmd_en, capture_output=True, text=True)
    if os.path.exists(abs_en_pdf) and os.path.getsize(abs_en_pdf) > 1000:
        print(f"✅ English PDF created successfully! ({os.path.getsize(abs_en_pdf)} bytes)")
    else:
        print(f"❌ Error generating English PDF: {res_en.stderr}")


if __name__ == "__main__":
    convert_md_to_pdf()
