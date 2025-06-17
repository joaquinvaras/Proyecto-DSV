# Proyecto 1 #

## Cómo ejecutar el aplicativo ##
Para ejecutar el aplicativo se deben seguir los siguientes pasos:
* Ejecutar el docker compose que se encuentra en la carpeta ```db``` con el comando ```docker compose up```
    * Debe tener instalado ```docker``` en su máquina para poder ejecutar ese comando
* Se debe ingresar a la base de datos con algún administrador de base de datos relacional de preferencia (Databind, DBeaver, etc) y crear la tabla de registros que se encuentra en la carpeta ```db``` en el archivo ```db.sql```
* Instalar las bibliotecas que se encuentran en el archivo ```requirements.txt``` utilizando el comando ```pip install -r requirements.txt```
    * NOTA: Si el comando anterior no funciona puedes utilizarlo indicando que se ejecute desde python con ```python -m pip install -r requirements.txt```
* Crear un archivo ```.env``` que contenga lo siguiente:
    ```
    MYSQL_HOST='localhost'
    MYSQL_PORT=3306
    MYSQL_DATABASE='test_poc'
    MYSQL_USER='user'
    MYSQL_PASSWORD='pass'
    ```
* Ejecutar la aplicación desde ```main.py``` con el comando ```python .\main.py```
    * Por defecto la aplicación se ejecuta en ```localhost``` en el puerto ```5000```


## Pasos especificos de instalacion que usamos
- Docker windows tiene que esta ejecutandose en segundo plano
- Iniciar una consola en modo administrador o super usuario e ingresar ```docker compose up``` en la carpeta ```db```
- Conectar DBeaver a la base de datos MySQL en localhost dejando todo por defecto, luego cambiar en la configuracion de la base de datos en Driver Properties ```allowPublicKeyRetrieval``` dejarlo en ```false``` y ```useSSL``` como ```true```
- Ejecutar el script ```db.sql``` que se encuentra en la carpeta ```db```
- Instalar las dependencias mediante ```pip install -r requirements.txt```
- Ejecutar el programa principal de python con ```python .\main.py```


## Uso del programa
La pagina web contiene unicamente los CRUD de sistemas que consisten en lo siguiente:

- Cursos: La creacion de cursos requiere solo seleccionar un nombre y un NRC (numero de identificacion), y se pueden seleccionar los cursos que se quieren definir como requisitos de este

- Alumno: Crear un alumno solo requiere nombre, mail y seleccionar la fecha de cuando ingreso

- Profesor: Para el profesor es lo mismo, requiere su nombre, mail y fecha desde la que trabaja

- Instanciacion de cursos: De la lista de cursos se selecciona uno y se pueden crear instancias designando un profesor, el periodo que se dicta y un numero para identificarlo

- A una seccion se le pueden añadir alumnos individualmente


# 📋 Entrega 3 - Análisis Estático de Código

## 🔍 Herramienta de Análisis Estático

Para el análisis estático del código se utilizó **Pylint**, una herramienta estándar de la industria para Python que evalúa la calidad del código, cumplimiento de estándares PEP 8, y detecta posibles errores.

El reporte inicial completo se encuentra en el archivo `static_analysis_report_initial.txt`. Cada archivo analizado incluye el sufijo `_nombre_del_archivo` al final para diferenciar los distintos análisis estáticos realizados.

---

## 📊 Resultados Finales por Archivo

A continuación se presentan los resultados obtenidos después de aplicar las correcciones sugeridas por Pylint:

### 🎯 **main.py:**
```
*************** Module main
main.py:1:0: C0302: Too many lines in module (1615/1000) (too-many-lines)
main.py:219:4: R1702: Too many nested blocks (6/5) (too-many-nested-blocks)
------------------------------------------------------------------
Your code has been rated at 9.98/10
```

### 🔧 **activity_service.py:**
```
*************** Module activity_service
activity_service.py:7:0: E0401: Unable to import 'db' (import-error)
------------------------------------------------------------------
Your code has been rated at 8.75/10
```

### 📚 **course_service.py:**
```
*************** Module course_service
course_service.py:7:0: E0401: Unable to import 'db' (import-error)
------------------------------------------------------------------
Your code has been rated at 9.40/10
```

### 📝 **course_taken_service.py:**
```
*************** Module course_taken_service
course_taken_service.py:7:0: E0401: Unable to import 'db' (import-error)
------------------------------------------------------------------
Your code has been rated at 8.48/10
```

### 📊 **grade_service.py:**
```
*************** Module grade_service
grade_service.py:7:0: E0401: Unable to import 'db' (import-error)
------------------------------------------------------------------
Your code has been rated at 9.44/10
```

### 📥 **import_service.py:**
```
************* Module import_service
import_service.py:312:0: C0325: Unnecessary parens after 'not' keyword (superfluous-parens)
import_service.py:1:0: C0302: Too many lines in module (1431/1000) (too-many-lines)
import_service.py:11:0: E0401: Unable to import 'db' (import-error)
import_service.py:14:0: R0903: Too few public methods (1/2) (too-few-public-methods)
------------------------------------------------------------------
Your code has been rated at 9.90/10
```

### 🏢 **instance_service.py:**
```
*************** Module instance_service
instance_service.py:7:0: E0401: Unable to import 'db' (import-error)
------------------------------------------------------------------
Your code has been rated at 9.22/10
```

### 🏫 **room_service.py:**
```
*************** Module room_service
room_service.py:7:0: E0401: Unable to import 'db' (import-error)
------------------------------------------------------------------
Your code has been rated at 8.81/10
```

### 📅 **schedule_service.py:**
```
************* Module schedule_service
schedule_service.py:10:0: E0401: Unable to import 'db' (import-error)
------------------------------------------------------------------
Your code has been rated at 9.55/10 
```

### 📖 **section_service.py:**
```
*************** Module section_service
section_service.py:7:0: E0401: Unable to import 'db' (import-error)
------------------------------------------------------------------
Your code has been rated at 9.32/10
```

### 📋 **topic_service.py:**
```
*************** Module topic_service
topic_service.py:7:0: E0401: Unable to import 'db' (import-error)
------------------------------------------------------------------
Your code has been rated at 8.75/10
```

### 👥 **user_service.py:**
```
*************** Module user_service
user_service.py:7:0: E0401: Unable to import 'db' (import-error)
------------------------------------------------------------------
Your code has been rated at 9.21/10
```

---

## ⚠️ Análisis de Errores Remanentes

### Docstring
Agregamos a todos los archivos un docstring (todo entre 3 comillas) al principio de cada metodo y de los archivos en general sino nos tiraba muchos errores la herramiento, se comento con el profesor y dijo que podiamos dejarlos para que no tire tantos errores.

### 🔗 **Error de Importación (E0401)**
La mayoría de los archivos de servicio presentan el error `Unable to import 'db'`. Este error es **inevitable** debido a que se trata de un import local del sistema que no está disponible en el entorno de análisis de Pylint. No representa un problema funcional del código.

### 📄 **Errores en import_service.py**

Este archivo presenta un par de errores, 

1. **Código extenso (C0302)**: El módulo excede las 1000 líneas recomendadas. Esto se debe a que la logica de importacion tiene muchas validaciones sobre la carga de archivos en la base de datos, lo que causa que quede algo largo el archivo.

2. **Parentesis innecesario (C0325)**: Esto parece ser un error en el pylint, ya que si quitamos ese parentesis el not no se toma de la manera correcta.

2. **Pocos metodos publicos (R0903)**: usamos los metodos necesarios asi que por motivos de usabilidad del codigo decidimos ignora el error.

### 📄 **Errores en main.py**

El archivo principal presenta dos advertencias menores:

1. **Código extenso (C0302)**: El módulo excede las 1000 líneas recomendadas. Esto se debe a que centralizamos toda la lógica de la aplicación en el archivo main.py, lo cual consideramos una decisión arquitectónica aceptable para este proyecto.

2. **Anidamiento complejo (R1702)**: La función `create_topic` tiene un nivel de anidamiento al límite. Esto es necesario debido a las múltiples validaciones de datos requeridas y se mantiene en el umbral aceptable de complejidad.

### 🎯 **Puntuación Final**
El archivo principal obtuvo una calificación de **9.98/10**, lo cual consideramos un resultado excelente que refleja la alta calidad del código desarrollado.

---

## ✅ Conclusión

El análisis estático ha demostrado que el código cumple con altos estándares de calidad, manteniendo puntuaciones superiores a 8.0/10 en todos los archivos analizados. Los errores remanentes son principalmente de naturaleza técnica (imports locales) o decisiones arquitectónicas justificadas.
