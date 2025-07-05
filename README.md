# PEMEX Local Logistics Dashboard - Dash App (Zona Pacífico)

## Descripción General

PEMEX Local Logistics Dashboard es una aplicación de escritorio desarrollada en Dash (Plotly + Flask), orientada al análisis operativo de la logística de transporte de combustibles en la Zona Pacífico.

La aplicación permite cargar archivos Excel locales, procesar KPIs logísticos clave y visualizar resultados en gráficos interactivos, todo sin necesidad de conexión a internet.

## Características Principales

- Carga automática de archivos Excel desde la carpeta local `/data/`.
- Detección automática del archivo Programa AT correspondiente al día actual (basado en la fecha dentro del nombre del archivo).
- Procesamiento y visualización de KPIs logísticos como:
  - Cumplimiento programado vs real.
  - Productividad por terminal.
  - Análisis de ociosidad.
  - Distribución de viajes por terminal.
- Interfaz profesional personalizable con colores institucionales (Vino y Mostaza).
- Compatible con PCs de especificaciones medias.

## Estructura del Proyecto

```
Pemex_Logistics/
├── Pemex_Logistica.py      # Código principal de la aplicación Dash
├── requirements.txt        # Lista de dependencias de Python
├── /assets/
│   └── style.css           # Estilos visuales personalizados
├── /data/                  # Archivos Excel diarios (carpeta ignorada por Git)
└── README.md               # Este archivo
```

## Requerimientos Previos

- Python 3.8 o superior.
- Instalación de dependencias necesarias:

```
pip install -r requirements.txt
```

## Instrucciones de Ejecución

1. Coloca los archivos Excel operativos dentro de la carpeta `/data/`.
2. Ejecuta la aplicación desde la terminal:

```
python Pemex_Logistica.py
```

3. Abre tu navegador web y accede a:

```
http://127.0.0.1:8050
```

## Consideraciones

- Este repositorio no contiene archivos de datos operativos de PEMEX.
- La carpeta `/data/` está listada en `.gitignore` para evitar subir información sensible.
- La aplicación está optimizada para uso local sin conexión a internet.

## Posibles Extensiones Futuras

- Empaquetado como `.exe` para usuarios no técnicos.
- Conexión futura a bases de datos corporativas (SQL Server, Microsoft Fabric).
- Exportación de reportes en PDF o Excel.
- Integración de modelos predictivos para optimización logística.

Desarrollado bajo un enfoque profesional de análisis logístico y visualización de datos en Dash y Python.
