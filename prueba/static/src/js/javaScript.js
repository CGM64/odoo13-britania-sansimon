function enviar(e) {
    var nm = document.getElementById('nombre')
    var edad = document.getElementById('edad')
    var correo = document.getElementById('correo')
    var direccion = document.getElementById('direccion')

    if(nm.value.trim() === "" || edad.value.trim() ==="" || correo.value.trim() === "" || direccion.value.trim() === ""){
        alert('No puede dejar campos vacíos')
    }else if(nm.value.trim() !== "" && edad.value.trim() !== "" && correo.value.trim() !== "" && direccion.value.trim() !== ""){
        alert('Datos guardados')
    }
}