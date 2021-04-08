function concatenar(){
        var name = "prueba1";
        var desc = "desc1";

        name = document.getElementById("contact_nm").value;
        document.getElementById("nm").value = name;

        var combo = document.getElementById("modelo");
        var selected = combo.options[combo.selectedIndex].text;
        desc = document.getElementById("contact_nm").value +", "+ selected;
        document.getElementById("conc").value = desc;
    }
