let boutons = [];
let textes = {};
let actif = null;

function clique(e){
    textes[actif.id].style.setProperty("display","none");
    actif.classList.remove("bouton-actif");
    actif = e;
    textes[actif.id].style.setProperty("display","block");
    actif.classList.add("bouton-actif");
}

document.addEventListener("DOMContentLoaded",()=>{
    for(const e of document.getElementById("tableau-domaines-boutons").children){
        boutons.push(e)
        e.addEventListener("click",()=>clique(e))
    }

    for(const e of document.getElementById("tableau-domaines-textes").children){
        textes[e.getAttribute("for")] = e;
    }

    actif = boutons[0];
    textes[actif.id].style.setProperty("display","block");
    actif.classList.add("bouton-actif");
})