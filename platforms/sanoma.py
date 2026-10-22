"""Sanoma (porting di Leone25/sanoma-downloader).

Login con email+password, download dello ZIP, estrazione delle pagine SVG
e conversione in PDF con PyMuPDF (niente Inkscape richiesto).
"""
import io
import os
import re
import tempfile
import zipfile

import pymupdf as fitz
from . import network as requests

from .common import response_json, save_pdf, checked_zip, svg_pdf, LoginError, sanitize, UA_SIMPLE

LABEL = "Sanoma"
AUTH_FIELDS = [("email", "Email account Sanoma", False, True),
               ("password", "Password", True, True)]
AUTH_HELP = "Accedi con email e password del tuo account Sanoma."
ID_LABEL = "ID libro (gedi)"
ID_HELP = "Il codice 'gedi' del libro, oppure selezionalo dalla lista."
OPTIONS = []
API = "https://npmoffline.sanoma.it/mcs/api/v1"

NEEDS_LOGIN = True
NEEDS_LIST = True


def login(creds):
    email, password = creds["email"].strip(), creds["password"]
    try:
        r = response_json(requests.post(
            f"{API}/login",
            headers={**UA_SIMPLE, "Content-Type": "application/json", "X-Timezone-Offset": "+0200"},
            json={"id": email, "password": password},
            timeout=20,
        ))
    except Exception:
        raise LoginError("Server Sanoma non raggiungibile. Riprova più tardi.")
    if r.get("code") != 0:
        raise LoginError(f"Login non riuscito: {r.get('message', 'email o password errati')}.")
    try:
        return {"token": r["result"]["data"]["access_token"]}
    except KeyError:
        raise LoginError("Risposta di login inattesa dal server Sanoma.")


def _auth(state):
    return {**UA_SIMPLE, "X-Auth-Token": "Bearer " + state["token"]}


def _catalog_request(state, resource, *, synchronization=False):
    label = "sincronizzazione prodotti" if synchronization else "elenco libri"
    response = requests.get(f"{API}/{resource}", headers=_auth(state), timeout=30)
    status = response.status_code
    if status >= 400:
        raise RuntimeError(f"Sanoma: {label} non riuscito (HTTP {status}).")
    # The synchronization endpoint's body is not part of the book-list contract.
    if synchronization:
        return None
    payload = response_json(response)
    code = payload.get("code") if isinstance(payload, dict) else None
    if not isinstance(payload, dict) or code not in (None, 0, "0", 200, "200"):
        safe_code = str(code) if isinstance(code, (int, str)) and re.fullmatch(r"-?[0-9]{1,8}", str(code)) else "non previsto"
        raise RuntimeError(f"Sanoma: {label} rifiutato (HTTP {status}, codice {safe_code}).")
    return payload


def list_books(state):
    # /products synchronizes the account's entitlements before /books reads them.
    # The original downloader performs this request even though it ignores its data.
    _catalog_request(state, "products", synchronization=True)
    payload = _catalog_request(state, "books?app=true")
    result = payload.get("result")
    if not isinstance(result, dict) or not isinstance(result.get("data"), list):
        raise RuntimeError("Risposta del catalogo Sanoma inattesa. Nessuna biblioteca aggiornata.")
    rows = result["data"]
    books = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("gedi") is None:
            raise RuntimeError("Catalogo Sanoma con un libro senza identificativo valido.")
        gid = str(row["gedi"]).strip()
        if not gid:
            raise RuntimeError("Catalogo Sanoma con un libro senza identificativo valido.")
        books[gid] = {"id": gid, "title": row.get("name") or "Libro senza titolo",
                      "url_download": row.get("url_download")}
    # Do not replace a previously loaded catalogue until synchronization and parsing succeed.
    state["by_id"] = books
    state["_debug"] = [f"Sanoma: prodotti sincronizzati; {len(books)} titoli nel catalogo."]
    return [{"id": b["id"], "title": b["title"]} for b in books.values()]


def download(state, book_id, out_dir, options, progress):
    gid = book_id.strip()
    book = (state.get("by_id") or {}).get(gid)
    if book is None:  # lista non caricata o ID manuale: ricarica
        for b in list_books(state):
            pass
        book = (state.get("by_id") or {}).get(gid)
    if book is None or not book.get("url_download"):
        raise RuntimeError("Libro non trovato nella tua libreria.")
    title = book["title"]

    tmp = tempfile.mkdtemp(prefix="sanoma_")
    try:
        progress(0, 1, f"Scarico '{title}'…")
        zpath = os.path.join(tmp, "book.zip")
        def transfer_progress(done, total):
            amount = f"{done / 1024**2:.1f} MB"
            if total:
                amount += f" / {total / 1024**2:.1f} MB"
            progress(done, total, f"Scarico ZIP: {amount}")
        requests.download_file(book["url_download"], zpath,
                               headers=_auth(state), progress=transfer_progress)

        progress(0, 1, "Estraggo le pagine…")
        pages_dir = os.path.join(tmp, "pages")
        with zipfile.ZipFile(zpath) as zh:
            checked_zip(zh, max_total_size=8 * 1024**3)
            for name in zh.namelist():
                m = re.search(r"(?:^|/)pages/(.+)$", name)
                if not m or name.endswith("/"):
                    continue
                dest = os.path.join(pages_dir, m.group(1))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with zh.open(name) as src, open(dest, "wb") as fh:
                    while chunk := src.read(1024 * 1024):
                        requests.check()
                        fh.write(chunk)

        folders = sorted(
            (d for d in os.listdir(pages_dir)
             if os.path.isdir(os.path.join(pages_dir, d)) and re.fullmatch(r"\d+", d)),
            key=int,
        )
        if not folders:
            raise RuntimeError("ZIP inatteso: nessuna pagina trovata.")

        doc = fitz.open()
        for i, n in enumerate(folders):
            requests.check()
            progress(i, len(folders), f"Converto pagina {i + 1}/{len(folders)}…")
            svg_path = os.path.join(pages_dir, n, f"{n}.svg")
            if not os.path.exists(svg_path):
                # qualche pagina può avere nome diverso: prendi il primo svg
                cands = [f for f in os.listdir(os.path.join(pages_dir, n)) if f.lower().endswith(".svg")]
                if not cands:
                    raise RuntimeError(f"Pagina {n} mancante: download incompleto.")
                svg_path = os.path.join(pages_dir, n, cands[0])
            with open(svg_path, "rb") as fh:
                converted = svg_pdf(fh.read(), os.path.dirname(svg_path))
            with fitz.open(stream=converted, filetype="pdf") as page:
                doc.insert_pdf(page)

        progress(1, 1, "Salvo il PDF…")
        out = os.path.join(out_dir, sanitize(title) + ".pdf")
        out = save_pdf(doc, out_dir, title)
        doc.close()
        progress(1, 1, "PDF salvato!")
        return out
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
