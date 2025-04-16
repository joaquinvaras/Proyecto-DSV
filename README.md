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

