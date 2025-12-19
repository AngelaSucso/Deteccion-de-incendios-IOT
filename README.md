# Deteccion-de-incendios-IOT
---

<!-- TABLA DE CONTENIDOS -->
<details>
  <summary>Tabla de Contenidos</summary>
  <ol>
    <li>
      <a href="#acerca-del-proyecto">Acerca del Proyecto</a>
      <ul>
        <li><a href="#descripcion-general-del-sistema">Descripción General del Sistema</a></li>
        <li><a href="#arquitectura-del-sistema">Arquitectura del Sistema</a></li>
        <li><a href="#tecnologias-utilizadas">Tecnologías Utilizadas</a></li>
      </ul>
    </li>
    <li>
      <a href="#primeros-pasos">Primeros Pasos</a>
      <ul>
        <li><a href="#requisitos-previos">Requisitos Previos</a></li>
        <li><a href="#instalacion">Instalación</a></li>
      </ul>
    </li>
    <li>
      <a href="#uso-del-sistema">Uso del Sistema</a>
      <ul>
        <li><a href="#estado-de-monitoreo-normal">Estado de Monitoreo Normal</a></li>
        <li><a href="#estado-de-deteccion-de-riesgo">Estado de Detección de Riesgo</a></li>
        <li><a href="#captura-multimedia">Captura Multimedia</a></li>
        <li><a href="#confirmacion-de-incendio">Confirmación de Incendio</a></li>
        <li><a href="#envio-de-alertas">Envío de Alertas</a></li>
      </ul>
    </li>
    <li><a href="#hoja-de-ruta">Hoja de Ruta</a></li>
    <li><a href="#contribuciones">Contribuciones</a></li>
    <li><a href="#licencia">Licencia</a></li>
    <li><a href="#contacto">Contacto</a></li>
    <li><a href="#agradecimientos">Agradecimientos</a></li>
  </ol>
</details>


## Acerca del Proyecto
### Descripción General del Sistema
### Arquitectura del Sistema
### Tecnologías Utilizadas



### ⚙️ Funcionamiento
1. El sistema se suscribe a un tópico MQTT y recibe datos en formato JSON.
2. Se evalúan los valores de temperatura, humedad y luz según umbrales definidos.
3. Si las condiciones de riesgo se mantienen durante varias lecturas consecutivas, se confirma la alerta.
4. Ante una alerta confirmada:
   - Se detecta el riesgo de incendio.
   - Se analiza la humedad ambiental.
   - Se captura una imagen desde la cámara IP.

     <img src="images/ipwebcam.jpeg" width="400">

   - Se graba un archivo de audio.
5. El sistema evita alertas repetidas hasta que las condiciones vuelvan a la normalidad.

---

### Datos esperados (MQTT)
El sistema espera mensajes en formato JSON con la siguiente estructura:

```json

{
  "temp": 45,
  "hum": 18,
  "luz": 2300
}