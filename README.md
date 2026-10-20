# Web Load Tester  
### Python HTTP Load Testing Tool  
**Autor:** Eduardo Chasco  
**Versión:** 1.4  
**Licencia:** MIT  

---

## 📑 Tabla de Contenidos

1. [Descripción](#descripción)
2. [Objetivo](#objetivo)
3. [Características](#características)
4. [Métricas](#métricas)
5. [Instalación](#instalación)
6. [Uso](#uso)
7. [Reportes](#reportes)
8. [Estructura del Proyecto](#estructura-del-proyecto)
9. [Tecnologías Utilizadas](#tecnologías-utilizadas)
10. [Contribuciones](#contribuciones)
11. [Licencia MIT](#licencia-mit)

---

## 📌 Descripción

**Web Load Tester** es una herramienta de pruebas de carga HTTP escrita en Python, diseñada para evaluar el rendimiento, estabilidad y disponibilidad de APIs y endpoints web bajo condiciones de alta concurrencia.

Permite ejecutar miles de solicitudes simultáneas, medir métricas avanzadas y generar reportes ejecutivos y técnicos en formatos **CSV** y **HTML5** con estilo dark.

---

## 🎯 Objetivo

Proveer una alternativa ligera, portable y extensible para realizar pruebas de carga sin depender de herramientas pesadas o complejas.

Está orientada a:

- Equipos de desarrollo  
- QA / Testing  
- DevOps / SRE  
- Auditorías de disponibilidad  
- Pentesting de rendimiento  

---

## 🚀 Características

### ✔ Pruebas de carga HTTP concurrentes
- Envío de miles de requests simultáneos  
- Control de concurrencia  
- Control de duración  
- Control de requests por segundo (rate)  
- Límite de requests totales  

### ✔ Soporte para múltiples URLs
- Analiza una sola URL  
- O múltiples URLs desde un archivo `.txt`  
- Cada URL se analiza por separado  
- Cada URL genera su propio reporte  

### ✔ Dashboard en tiempo real
- Métricas actualizadas en vivo  
- Latencias  
- Códigos HTTP  
- Percentiles  
- Throughput  
- Título dinámico con la URL analizada  
- Sin interferencia entre dashboards  

### ✔ Reportes automáticos
- **CSV** con todos los logs  
- **HTML5 dark elegante** con métricas completas  
- Nombre del archivo incluye:  
  - dominio  
  - segmento sanitizado de la URL  
  - fecha y hora  
- Carpeta automática `/reports/`

### ✔ Reporte ejecutivo final
Cuando se usa `-file`, se genera un reporte adicional con:

- URL  
- Total de requests  
- Latencia promedio  
- p95  
- Código predominante  
- Throughput  
- Sin logs detallados  
- Ideal para gerencias y presentaciones  

---

## 📊 Métricas

- **Total de requests**
- **Códigos HTTP**
- **Latencia promedio**
- **Latencia mediana**
- **Percentiles:**  
  - p50  
  - p90  
  - p95  
  - p99  
- **Throughput (req/s)**

---

## 🧩 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/<tu-usuario>/web-load-tester.git
cd web-load-tester
