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

window.onload=function() {
  var anchors = document.getElementById('fb');
  if(anchors != null & anchors.length > 0){
      anchors[0].href = anchors[1].href;
      document.getElementById('divFb').setAttribute('data-href', anchors[0].href);
      document.getElementById('blkFb').setAttribute('cite', anchors[0].href);
      document.getElementById('aFb').setAttribute('src', anchors[0].href);
      console.log(anchors[0].href)
  }
    }
