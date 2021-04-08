function concatenar(){
        var name = "prueba1";
        var desc = "desc1";

        name = document.getElementById("contact_nm").value;
        document.getElementById("nm").value = name;

        desc = document.getElementById("contact_nm").value +", "+
        document.getElementById("model").value;

        document.getElementById("conc").value = desc;
    }
