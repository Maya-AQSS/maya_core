## Instalación **Maya | Core**

> A lo largo del documento, el prompt **$** indica un comando a introducir en el host, mientras que el prompt **>** indica un comando a introducir en el contenedor.

1. [ ] Clonar en la carpeta de los _addons_ el repo de **Maya | Core** desde [github](https://github.com/Maya-AQSS/maya_core). 
     
     En caso de usar [odooddock](https://aoltra.github.io/odoodock/), la mejor opción es el uso de script _create-module.sh_, opción O2, tal y como se explica [aquí](https://aoltra.github.io/odoodock/docs/modulos/crear-modulos-script).

     > Es posible que al actualizar la lista de aplicaciones desde _Odoo_, **Maya | Core** no aparezca entre ellas. Lo mejor en estos casos es tumbar (_docker compose down_) y volver a levantar los contenedores (_up.sh_)
 

2. [] Instalar los requerimientos. Desde la carpeta del módulo clonado, _maya_core_, ejecutar:

   ```
   $ pip3 install -r requirements-dev.txt
   ```

   En caso de usar [odooddock](https://aoltra.github.io/odoodock/), hay que entrar dentro del contendor y ejecutar el comando:

   ```
   $ docker exec -it odoodock-web-1 bash
   > cd /mnt/extra-addons/maya_core
   > pip3 install -r requirements-dev.txt
   ```

3. [] Instalar **Maya | Core** desde el menu de _Aplicaciones_ de _Odoo_.
