document.addEventListener("DOMContentLoaded",()=>{
    for(let e of document.getElementsByTagName("decompte")){
        fin = new Date(e.getAttribute("fin")).getTime();

        setInterval(function() {
            var aujourdhui = new Date().getTime();
            var distance = fin - aujourdhui;

            var jours = Math.floor(distance / (1000 * 60 * 60 * 24));
            var heures = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            var secondes = Math.floor((distance % (1000 * 60)) / 1000);

            e.innerHTML = jours + "j " + heures + "h " + minutes + "m " + secondes + "s";

            if (distance < 0) {
                clearInterval(x);
                e.innerHTML = e.getAttribute("texte-fin");
            }
        }, 1000);
    }
});