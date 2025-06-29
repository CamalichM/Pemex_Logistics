# PEMEX Local Logistics Dashboard – Zona Pacífico (Web App)

## 📌 Descripción General

**PEMEX Local Logistics Dashboard** es una aplicación web local, diseñada para ofrecer una solución ligera, portable y altamente interactiva para el análisis operativo y estratégico de la logística de transporte de combustibles en la **Zona Pacífico** de PEMEX.

La solución permite a los usuarios trabajar en un ambiente **100% local**, sin requerir conexión a internet ni servidores externos, garantizando así la confidencialidad y seguridad de la información operativa.

---

## 🎯 Objetivo del Proyecto

Proporcionar a los **analistas logísticos**, **programadores de transporte** y **personal operativo de PEMEX** una herramienta de visualización de KPIs clave, que permita una toma de decisiones ágil y fundamentada, a partir de los archivos Excel generados diariamente por las distintas áreas operativas.

---

## 🛠️ Características Principales

- ✅ Lectura y procesamiento local de múltiples archivos Excel:  
  - Programa AT  
  - BASE PACÍFICO  
  - OPERACIÓN 24  
  - CUMPLE JULIO  

- ✅ Visualización interactiva de KPIs críticos como:  
  - Cumplimiento Programado vs Real  
  - Productividad por Terminal, Cliente o Equipo  
  - Análisis de Ociosidad de Flota  
  - Tendencias de Cumplimiento  
  - Rutas Críticas por bajo desempeño  

- ✅ Interfaz profesional con:  
  - Diseño UX/UI de nivel corporativo  
  - Colores institucionales: **Vino**, **Mostaza** y **Neutros**  
  - Tipografía moderna para legibilidad y presentación ejecutiva  
  - Filtros dinámicos y gráficos interactivos desarrollados en **Chart.js**  

- ✅ Total portabilidad:  
  Solo requiere un navegador moderno (Chrome, Edge o Firefox)

  
---

## 🚀 Requerimientos Técnicos

- ✅ **Navegador:** Chrome, Edge o Firefox (actualizados).
- ✅ **Librerías locales necesarias:**
  - **Chart.js:**  
    [https://cdn.jsdelivr.net/npm/chart.js](https://cdn.jsdelivr.net/npm/chart.js)
  - **SheetJS XLSX:**  
    [https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js](https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js)
Las librerías deben descargarse manualmente y colocarse dentro de la carpeta `/libs/`.

---

## 🖥️ Uso de la Aplicación

1. Ubicar los archivos Excel diarios dentro de una carpeta local.
2. Abrir el archivo `index.html` desde el navegador.
3. Utilizar los botones de carga para importar los datos operativos.
4. Aplicar filtros según sea necesario: **Cliente**, **Terminal**, **Producto**, **Fecha**.
5. Analizar las métricas y visualizaciones generadas en tiempo real.

---

## 📌 Alcance y Limitaciones

> Este proyecto es una solución **interina y local**, orientada a entornos donde las políticas corporativas de red impiden el uso de herramientas en la nube o de almacenamiento externo.

No sustituye a un sistema de Business Intelligence centralizado como **Microsoft Fabric** o **SQL Server Reporting Services**, pero representa una alternativa eficiente y profesional para el análisis logístico diario.

---

## 📈 Posibles Extensiones Futuras

- Exportación de reportes en PDF o Excel.
- Incorporación de análisis predictivo de cumplimiento.
- Versión empaquetada como aplicación de escritorio (Electron o Python EXE).
- Migración a plataforma web corporativa de PEMEX.

---

**Desarrollado bajo un enfoque de análisis de datos logísticos con estándares de calidad y visualización profesional para PEMEX Zona Pacífico.**


