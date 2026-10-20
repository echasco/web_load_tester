#!/usr/bin/env python3
# ============================================================
# Autor: Eduardo Chasco
# Revisión: 1.4
# Nombre del programa: Web Load Tester Python Load Tester
#
# Descripción:
#   Herramienta de pruebas de carga HTTP que simula el
#   comportamiento de herramientas de carga profesionales,
#   permitiendo enviar miles de requests concurrentes, medir
#   latencias, códigos HTTP, throughput y generar reportes
#   profesionales CSV y HTML5.
#
# Objetivo:
#   Evaluar disponibilidad, estabilidad y rendimiento de APIs
#   bajo alta carga, con métricas avanzadas (p50, p90, p95, p99),
#   dashboard en tiempo real y reportes automáticos por URL.
# ============================================================

import argparse
import asyncio
import aiohttp
import json
import time
import csv
import os
from datetime import datetime
from collections import defaultdict
from statistics import median
from urllib.parse import urlparse

from rich.live import Live
from rich.table import Table
from rich.console import Console

console = Console()

# ============================================================
# VARIABLES GLOBALES (SE LIMPIAN POR CADA URL)
# ============================================================

stats = defaultdict(int)
latencies = []
request_log = []
summary_results = []   # NUEVO: para reporte ejecutivo final


# ============================================================
# UTILIDADES
# ============================================================

def timestamp():
    return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")


def ensure_reports_folder():
    folder = "reports"
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


def extract_domain(url):
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return "unknown_domain"


def extract_url_segment(url):
    """Extrae los siguientes 20 caracteres después del dominio y los sanitiza."""
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        segment = path[:20] if path else ""
        segment = segment.replace("/", "_")
        segment = segment.replace("-", "_")
        segment = segment.replace(" ", "_")
        segment = ''.join(c if c.isalnum() or c == "_" else "_" for c in segment)
        return segment if segment else "root"
    except:
        return "root"


def reset_metrics():
    stats.clear()
    latencies.clear()
    request_log.clear()


def percentiles(data):
    if not data:
        return {"p50": 0, "p90": 0, "p95": 0, "p99": 0}
    data_sorted = sorted(data)
    return {
        "p50": data_sorted[int(0.50 * len(data_sorted))],
        "p90": data_sorted[int(0.90 * len(data_sorted))],
        "p95": data_sorted[int(0.95 * len(data_sorted))],
        "p99": data_sorted[int(0.99 * len(data_sorted))],
    }


# ============================================================
# WORKER
# ============================================================

async def worker(session, url, method, payload, headers):
    start = time.perf_counter()
    try:
        async with session.request(method, url, json=payload, headers=headers) as response:
            latency = time.perf_counter() - start
            latencies.append(latency)
            stats[response.status] += 1
            request_log.append({
                "url": url,
                "status": response.status,
                "latency": latency,
                "error": ""
            })
    except Exception as e:
        latency = time.perf_counter() - start
        stats["error"] += 1
        latencies.append(latency)
        request_log.append({
            "url": url,
            "status": "error",
            "latency": latency,
            "error": str(e)
        })


# ============================================================
# LOAD TEST
# ============================================================

async def run_load_test(url, concurrency, duration, rate, total_requests, method, payload, headers):
    async with aiohttp.ClientSession() as session:
        end_time = time.time() + duration
        requests_sent = 0

        while time.time() < end_time:
            batch = []

            for _ in range(concurrency):
                if total_requests and requests_sent >= total_requests:
                    break
                batch.append(worker(session, url, method, payload, headers))
                requests_sent += 1

            if not batch:
                break

            await asyncio.gather(*batch)

            if rate:
                await asyncio.sleep(1 / rate)
            else:
                await asyncio.sleep(0)


# ============================================================
# DASHBOARD
# ============================================================

def build_dashboard(url):
    table = Table(title=f"Web Load Tester Dashboard\nURL: {url}", style="bold white")
    table.add_column("Métrica", style="cyan", no_wrap=True)
    table.add_column("Valor", style="magenta")

    total = sum(stats.values())
    table.add_row("Total requests", str(total))

    codes = ", ".join(f"{code}: {count}" for code, count in stats.items())
    table.add_row("HTTP codes / errores", codes or "N/A")

    if latencies:
        avg = sum(latencies) / len(latencies)
        med = median(latencies)
        p = percentiles(latencies)
        table.add_row("Latencia promedio", f"{avg:.4f} s")
        table.add_row("Latencia mediana", f"{med:.4f} s")
        table.add_row("p50", f"{p['p50']:.4f} s")
        table.add_row("p90", f"{p['p90']:.4f} s")
        table.add_row("p95", f"{p['p95']:.4f} s")
        table.add_row("p99", f"{p['p99']:.4f} s")
    else:
        table.add_row("Latencias", "sin datos aún")

    return table


async def realtime_dashboard(url):
    await asyncio.sleep(0.1)  # FIX: evita que quede el dashboard anterior
    with Live(build_dashboard(url), refresh_per_second=2, console=console) as live:
        while True:
            await asyncio.sleep(1)
            live.update(build_dashboard(url))


# ============================================================
# REPORTES
# ============================================================

def export_csv(url):
    folder = ensure_reports_folder()
    domain = extract_domain(url)
    segment = extract_url_segment(url)
    name = f"report_{domain}_{segment}_{timestamp()}.csv"
    path = os.path.join(folder, name)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "status", "latency", "error"])
        writer.writeheader()
        writer.writerows(request_log)

    console.print(f"[bold]📄 CSV generado:[/] {path}")


def export_html(url):
    folder = ensure_reports_folder()
    domain = extract_domain(url)
    segment = extract_url_segment(url)
    name = f"report_{domain}_{segment}_{timestamp()}.html"
    path = os.path.join(folder, name)

    p = percentiles(latencies)
    total = sum(stats.values())
    avg = sum(latencies) / len(latencies) if latencies else 0
    med = median(latencies) if latencies else 0

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Web Load Tester Report</title>
<style>
body {{
    background-color: #121212;
    color: #e0e0e0;
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
}}
h1, h2 {{
    color: #ffffff;
}}
.card {{
    background-color: #1e1e1e;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5);
}}
table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
}}
th, td {{
    padding: 8px;
    border-bottom: 1px solid #333;
}}
th {{
    background-color: #272727;
}}
.badge {{
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    background-color: #333;
    margin-right: 4px;
}}
.badge-ok {{ background-color: #2e7d32; }}
.badge-error {{ background-color: #c62828; }}
</style>
</head>
<body>
<h1>Web Load Tester Report</h1>
<h2>URL analizada: {url}</h2>

<div class="card">
  <h2>Resumen</h2>
  <p><strong>Total requests:</strong> {total}</p>
  <p><strong>Latencia promedio:</strong> {avg:.4f} s</p>
  <p><strong>Latencia mediana:</strong> {med:.4f} s</p>
  <p><strong>p50:</strong> {p['p50']:.4f} s</p>
  <p><strong>p90:</strong> {p['p90']:.4f} s</p>
  <p><strong>p95:</strong> {p['p95']:.4f} s</p>
  <p><strong>p99:</strong> {p['p99']:.4f} s</p>
</div>

<div class="card">
  <h2>Códigos HTTP</h2>
  <p>
"""
    for code, count in stats.items():
        cls = "badge-ok" if isinstance(code, int) and 200 <= code < 300 else "badge-error"
        html += f'<span class="badge {cls}">{code}: {count}</span> '
    html += """
  </p>
</div>

<div class="card">
  <h2>Detalle de requests</h2>
  <table>
    <thead>
      <tr>
        <th>URL</th>
        <th>Status</th>
        <th>Latencia (s)</th>
        <th>Error</th>
      </tr>
    </thead>
    <tbody>
"""
    for r in request_log:
        html += f"""
      <tr>
        <td>{r['url']}</td>
        <td>{r['status']}</td>
        <td>{r['latency']:.4f}</td>
        <td>{r['error']}</td>
      </tr>
"""
    html += """
    </tbody>
  </table>
</div>

</body>
</html>
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    console.print(f"[bold]🌐 HTML generado:[/] {path}")


# ============================================================
# REPORTE EJECUTIVO FINAL
# ============================================================

def export_summary():
    folder = ensure_reports_folder()
    name = f"summary_{timestamp()}.html"
    path = os.path.join(folder, name)

    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Resumen Ejecutivo Web Load Tester</title>
<style>
body { background-color:#121212; color:#e0e0e0; font-family:Arial; padding:20px; }
h1,h2 { color:#fff; }
.card { background:#1e1e1e; padding:16px; margin-bottom:20px; border-radius:8px; }
table { width:100%; border-collapse:collapse; }
th,td { padding:8px; border-bottom:1px solid #333; }
th { background:#272727; }
</style>
</head>
<body>
<h1>Resumen Ejecutivo Web Load Tester</h1>
"""

    for item in summary_results:
        html += f"""
<div class="card">
<h2>{item['url']}</h2>
<p><strong>Total requests:</strong> {item['total']}</p>
<p><strong>Latencia promedio:</strong> {item['avg']:.4f} s</p>
<p><strong>p95:</strong> {item['p95']:.4f} s</p>
<p><strong>Código predominante:</strong> {item['code']}</p>
<p><strong>Throughput:</strong> {item['throughput']:.2f} req/s</p>
</div>
"""

    html += "</body></html>"

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    console.print(f"[bold]📘 Resumen ejecutivo generado:[/] {path}")


# ============================================================
# CLI
# ============================================================

def load_urls(args):
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return [args.url]


def load_json_file(path):
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def async_main(args):
    urls = load_urls(args)
    payload = load_json_file(args.payload)
    headers = load_json_file(args.headers)

    for url in urls:
        reset_metrics()

        console.print(f"\n[bold cyan]========================================[/]")
        console.print(f"[bold cyan]Iniciando análisis para URL: {url}[/]")
        console.print(f"[bold cyan]========================================[/]\n")

        dashboard_task = asyncio.create_task(realtime_dashboard(url))

        await run_load_test(
            url,
            args.concurrency,
            args.duration,
            args.rate,
            args.requests,
            args.method.upper(),
            payload,
            headers
        )

        dashboard_task.cancel()

        console.print(f"\n[bold green]✔ Finalizado análisis para {url}[/]\n")

        # Guardar resumen ejecutivo
        p = percentiles(latencies)
        total = sum(stats.values())
        avg = sum(latencies) / len(latencies) if latencies else 0
        throughput = total / sum(latencies) if latencies else 0
        main_code = max(stats, key=stats.get)

        summary_results.append({
            "url": url,
            "total": total,
            "avg": avg,
            "p95": p["p95"],
            "code": main_code,
            "throughput": throughput
        })

        if args.csv:
            export_csv(url)

        if args.html:
            export_html(url)

    # Generar resumen final si se usó archivo
    if args.file:
        export_summary()


def main():
    parser = argparse.ArgumentParser(
        description="Web Load Tester: herramienta de carga HTTP en Python",
        epilog="""
Ejemplos de uso:

  1) Probar una sola URL:
     python web-load-tester.py -url https://dominio.cl -c 200 -d 30 --csv --html

  2) Probar múltiples URLs desde un archivo:
     python web-load-tester.py -file urls.txt -c 100 -d 60 --csv --html

  3) Enviar máximo 5000 requests:
     python web-load-tester.py -url https://api.cl -n 5000

  4) Controlar requests por segundo (rate):
     python web-load-tester.py -url https://api.cl -r 50

  5) Enviar POST con payload y headers:
     python web-load-tester.py -url https://api.cl --method POST --payload data.json --headers headers.json
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("-url", help="URL a probar")
    parser.add_argument("-file", help="Archivo con listado de URLs (una por línea)")
    parser.add_argument("-c", "--concurrency", type=int, default=10)
    parser.add_argument("-d", "--duration", type=int, default=10)
    parser.add_argument("-r", "--rate", type=float, default=0)
    parser.add_argument("-n", "--requests", type=int, default=0)
    parser.add_argument("--method", default="GET")
    parser.add_argument("--payload", help="Archivo JSON para payload")
    parser.add_argument("--headers", help="Archivo JSON para headers")
    parser.add_argument("--csv", action="store_true")
    parser.add_argument("--html", action="store_true")

    args = parser.parse_args()

    if not args.url and not args.file:
        console.print("[bold red]Debes especificar -url o -file[/]")
        return

    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
